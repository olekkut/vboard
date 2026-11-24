import subprocess
from dataclasses import dataclass

from .environment import is_gnome_environment, is_kde_environment, is_wayland_session
from .gtk import Gio, GLib
from .xkb_layouts import build_layout_from_xkb


PLASMA_LAYOUT_SERVICE = "org.kde.keyboard"
PLASMA_LAYOUT_PATH = "/Layouts"
PLASMA_LAYOUT_INTERFACE = "org.kde.KeyboardLayouts"

GNOME_INPUT_SOURCES_SCHEMA = "org.gnome.desktop.input-sources"

DEFAULT_VBOARD_TO_XKB_LAYOUT = {
    "de": "de",
    "en": "us",
    "fr": "fr",
    "pl": "pl",
    "ru": "ru",
    "sv": "se",
    "uk": "ua",
}

XKB_FALLBACK_TO_VBOARD_LAYOUT = {
    "au": "en",
    "ca": "en",
    "de": "de",
    "fr": "fr",
    "gb": "en",
    "pl": "pl",
    "ru": "ru",
    "se": "sv",
    "ua": "uk",
    "us": "en",
}

# Default XKB variant names that are identical to the empty ("") variant in xkb-data.
DEFAULT_XKB_VARIANT_ALIASES = {
    ("de", "basic"): "",
    ("fr", "basic"): "",
    ("pl", "basic"): "",
    ("ru", "winkeys"): "",
    ("se", "basic"): "",
    ("ua", "unicode"): "",
    ("us", "basic"): "",
}


@dataclass(frozen=True)
class SystemLayoutEntry:
    index: int
    xkb_layout: str
    variant: str
    display_name: str


def parse_xkb_spec(layout_name, variant=""):
    """Normalize an XKB layout name that may embed a variant like 'us(dvorak)' or 'us+dvorak'."""
    layout_name = (layout_name or "").strip()
    variant = (variant or "").strip()
    if "(" in layout_name and layout_name.endswith(")"):
        base, embedded_variant = layout_name.split("(", 1)
        layout_name = base.strip()
        if not variant:
            variant = embedded_variant[:-1].strip()
    elif "+" in layout_name:
        base, embedded_variant = layout_name.split("+", 1)
        layout_name = base.strip()
        if not variant:
            variant = embedded_variant.strip()
    return layout_name, variant


def normalize_xkb_variant(xkb_layout, variant=""):
    return DEFAULT_XKB_VARIANT_ALIASES.get((xkb_layout, variant), variant)


def build_xkb_lookup_maps(keyboard_layouts):
    vboard_to_xkb = dict(DEFAULT_VBOARD_TO_XKB_LAYOUT)
    exact_xkb_to_vboard = {}

    for layout_id, layout_config in keyboard_layouts.items():
        if layout_config.get("dynamic"):
            continue
        xkb_layout = layout_config.get("xkb_layout") or vboard_to_xkb.get(layout_id)
        xkb_variant = layout_config.get("xkb_variant", "") or ""
        if xkb_layout:
            xkb_layout, xkb_variant = parse_xkb_spec(xkb_layout, xkb_variant)
            xkb_variant = normalize_xkb_variant(xkb_layout, xkb_variant)
            vboard_to_xkb[layout_id] = xkb_layout
            exact_xkb_to_vboard[(xkb_layout, xkb_variant)] = layout_id

    return vboard_to_xkb, exact_xkb_to_vboard


def resolve_system_entry_to_vboard_layout(entry, keyboard_layouts):
    """
    Resolve a SystemLayoutEntry to a Vboard layout ID.

    Prefers curated static/user JSON layouts for exact (xkb_layout, variant) matches.
    For non-default variants or languages without a bundled JSON layout, dynamically
    generates an accurate Vboard layout via libxkbcommon and registers it in
    keyboard_layouts so Vboard always stays in sync with the active OS layout.
    """
    if entry is None:
        return None

    xkb_layout, variant = parse_xkb_spec(entry.xkb_layout, entry.variant)
    if not xkb_layout:
        return None
    canonical_variant = normalize_xkb_variant(xkb_layout, variant)

    _vboard_to_xkb, exact_xkb_to_vboard = build_xkb_lookup_maps(keyboard_layouts)

    exact_match = exact_xkb_to_vboard.get((xkb_layout, canonical_variant))
    if exact_match is not None:
        return exact_match

    # Dynamically extract exact labels from XKB for any variant or unbundled language.
    dynamic_layout = build_layout_from_xkb(
        xkb_layout,
        canonical_variant,
        display_name=entry.display_name or None,
    )
    if dynamic_layout is not None:
        keyboard_layouts[dynamic_layout["id"]] = dynamic_layout
        return dynamic_layout["id"]

    # Fallback when libxkbcommon is unavailable.
    if not canonical_variant:
        fallback_id = XKB_FALLBACK_TO_VBOARD_LAYOUT.get(xkb_layout)
        if fallback_id in keyboard_layouts:
            return fallback_id
    else:
        default_match = exact_xkb_to_vboard.get((xkb_layout, ""))
        if default_match is not None:
            return default_match

    return None


def get_next_layout_id(current_layout, available_layouts):
    available = tuple(dict.fromkeys(available_layouts))
    if len(available) < 2:
        return None
    if current_layout not in available:
        return available[0]
    current_index = available.index(current_layout)
    return available[(current_index + 1) % len(available)]


class PlasmaLayoutBackend:
    """Two-way keyboard layout sync over KDE Plasma's org.kde.KeyboardLayouts D-Bus API."""

    name = "plasma"

    def __init__(self, on_changed=None):
        self.on_changed = on_changed
        self.proxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE,
            None,
            PLASMA_LAYOUT_SERVICE,
            PLASMA_LAYOUT_PATH,
            PLASMA_LAYOUT_INTERFACE,
            None,
        )
        self.entries = []
        self.refresh()
        self.signal_handler_id = self.proxy.connect("g-signal", self._on_dbus_signal)

    def _call(self, method, parameters=None):
        return self.proxy.call_sync(
            method,
            parameters,
            Gio.DBusCallFlags.NONE,
            2000,
            None,
        )

    def refresh(self):
        result = self._call("getLayoutsList")
        raw_layouts = list(result.unpack()[0])
        self.entries = [
            SystemLayoutEntry(
                index=idx,
                xkb_layout=parse_xkb_spec(layout, variant)[0],
                variant=parse_xkb_spec(layout, variant)[1],
                display_name=description or layout,
            )
            for idx, (layout, variant, description) in enumerate(raw_layouts)
        ]
        return list(self.entries)

    def get_layouts(self):
        return tuple(self.entries)

    def get_current_index(self):
        result = self._call("getLayout")
        index = int(result.unpack()[0])
        if 0 <= index < len(self.entries):
            return index
        return None

    def set_layout_index(self, index):
        if index < 0 or index >= len(self.entries):
            return False
        result = self._call("setLayout", GLib.Variant("(u)", (index,)))
        unpacked = result.unpack()
        return bool(unpacked[0]) if unpacked else True

    def _on_dbus_signal(self, _proxy, _sender_name, signal_name, parameters):
        if signal_name == "layoutListChanged":
            try:
                self.refresh()
                current_index = self.get_current_index()
            except (GLib.Error, OSError, RuntimeError):
                return
            self._notify(current_index)
            return

        if signal_name == "layoutChanged":
            layout_index = int(parameters.unpack()[0])
            if layout_index >= len(self.entries):
                try:
                    self.refresh()
                except (GLib.Error, OSError, RuntimeError):
                    return
            self._notify(layout_index)

    def _notify(self, index):
        if self.on_changed is None or index is None:
            return
        if 0 <= index < len(self.entries):
            self.on_changed(self.entries[index])

    def close(self):
        if self.signal_handler_id is not None:
            self.proxy.disconnect(self.signal_handler_id)
            self.signal_handler_id = None


class GnomeLayoutBackend:
    """Two-way keyboard layout sync over GNOME org.gnome.desktop.input-sources GSettings."""

    name = "gnome"

    def __init__(self, on_changed=None):
        schema_source = Gio.SettingsSchemaSource.get_default()
        if schema_source is None or schema_source.lookup(GNOME_INPUT_SOURCES_SCHEMA, True) is None:
            raise RuntimeError("GNOME input-sources schema is not available")

        self.on_changed = on_changed
        self.settings = Gio.Settings.new(GNOME_INPUT_SOURCES_SCHEMA)
        self.raw_sources = []
        self.entries = []
        self.refresh()
        self._mru_handler_id = self.settings.connect(
            "changed::mru-sources", self._on_settings_changed
        )
        self._sources_handler_id = self.settings.connect(
            "changed::sources", self._on_settings_changed
        )

    def refresh(self):
        self.raw_sources = list(self.settings.get_value("sources").unpack())
        entries = []
        for idx, (kind, spec) in enumerate(self.raw_sources):
            if kind != "xkb":
                continue
            xkb_layout, variant = parse_xkb_spec(spec)
            display = f"{xkb_layout.upper()} ({variant})" if variant else xkb_layout.upper()
            entries.append(
                SystemLayoutEntry(
                    index=idx,
                    xkb_layout=xkb_layout,
                    variant=variant,
                    display_name=display,
                )
            )
        self.entries = entries
        return list(self.entries)

    def get_layouts(self):
        return tuple(self.entries)

    def get_current_index(self):
        mru = list(self.settings.get_value("mru-sources").unpack())
        if mru:
            active_source = mru[0]
            for entry in self.entries:
                if self.raw_sources[entry.index] == active_source:
                    return entry.index
        if self.entries:
            return self.entries[0].index
        return None

    def set_layout_index(self, index):
        if index < 0 or index >= len(self.raw_sources):
            return False
        target = self.raw_sources[index]
        mru = list(self.settings.get_value("mru-sources").unpack())
        reordered = [target] + [item for item in mru if item != target]
        for item in self.raw_sources:
            if item not in reordered:
                reordered.append(item)
        self.settings.set_value("mru-sources", GLib.Variant("a(ss)", reordered))
        return True

    def _on_settings_changed(self, _settings, _key):
        self.refresh()
        current_index = self.get_current_index()
        if self.on_changed is None or current_index is None:
            return
        for entry in self.entries:
            if entry.index == current_index:
                self.on_changed(entry)
                break

    def close(self):
        if self._mru_handler_id is not None:
            self.settings.disconnect(self._mru_handler_id)
            self._mru_handler_id = None
        if self._sources_handler_id is not None:
            self.settings.disconnect(self._sources_handler_id)
            self._sources_handler_id = None


class X11LayoutBackend:
    """Fallback layout backend for X11 sessions using setxkbmap / xkb-switch."""

    name = "x11"

    def __init__(self, on_changed=None):
        self.on_changed = on_changed
        self.entries = []
        self.refresh()
        if not self.entries:
            raise RuntimeError("No X11 keyboard layouts found via setxkbmap")

    def refresh(self):
        try:
            proc = subprocess.run(
                ["setxkbmap", "-query"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
        except OSError as exc:
            raise RuntimeError(f"setxkbmap not available: {exc}") from exc

        if proc.returncode != 0:
            raise RuntimeError("setxkbmap -query failed")

        layouts = []
        variants = []
        for line in proc.stdout.splitlines():
            if line.startswith("layout:"):
                layouts = [item.strip() for item in line.split(":", 1)[1].split(",") if item.strip()]
            elif line.startswith("variant:"):
                variants = [item.strip() for item in line.split(":", 1)[1].split(",")]

        self.entries = []
        for idx, layout in enumerate(layouts):
            variant = variants[idx] if idx < len(variants) else ""
            xkb_layout, variant = parse_xkb_spec(layout, variant)
            display = f"{xkb_layout.upper()} ({variant})" if variant else xkb_layout.upper()
            self.entries.append(
                SystemLayoutEntry(
                    index=idx,
                    xkb_layout=xkb_layout,
                    variant=variant,
                    display_name=display,
                )
            )
        return list(self.entries)

    def get_layouts(self):
        return tuple(self.entries)

    def get_current_index(self):
        try:
            proc = subprocess.run(
                ["xkb-switch", "-p"],
                capture_output=True,
                text=True,
                timeout=1,
                check=False,
            )
            if proc.returncode == 0:
                current_spec = proc.stdout.strip()
                xkb_layout, variant = parse_xkb_spec(current_spec)
                for entry in self.entries:
                    if entry.xkb_layout == xkb_layout and entry.variant == variant:
                        return entry.index
                for entry in self.entries:
                    if entry.xkb_layout == xkb_layout:
                        return entry.index
        except OSError:
            pass
        return 0 if self.entries else None

    def set_layout_index(self, index):
        if index < 0 or index >= len(self.entries):
            return False
        entry = self.entries[index]
        spec = f"{entry.xkb_layout}({entry.variant})" if entry.variant else entry.xkb_layout
        try:
            proc = subprocess.run(
                ["xkb-switch", "-s", spec],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if proc.returncode == 0:
                return True
        except OSError:
            pass
        return False

    def close(self):
        return


class SystemLayoutController:
    """High-level controller coordinating two-way synchronization with system keyboard layouts."""

    def __init__(self, backend, keyboard_layouts, on_layout_changed=None):
        self.backend = backend
        self.keyboard_layouts = keyboard_layouts
        self.on_layout_changed = on_layout_changed
        self.backend.on_changed = self._handle_backend_change

    @classmethod
    def create(cls, keyboard_layouts, on_layout_changed=None):
        backend = None
        candidates = []
        if is_kde_environment():
            candidates.append(PlasmaLayoutBackend)
        elif is_gnome_environment():
            candidates.append(GnomeLayoutBackend)
        else:
            # Try Plasma D-Bus first (works even if XDG_CURRENT_DESKTOP is custom), then GNOME, then X11.
            candidates.extend((PlasmaLayoutBackend, GnomeLayoutBackend))

        if not is_wayland_session():
            candidates.append(X11LayoutBackend)

        for backend_cls in candidates:
            try:
                backend = backend_cls(on_changed=None)
                break
            except (GLib.Error, OSError, RuntimeError):
                continue

        if backend is None:
            return None

        return cls(backend, keyboard_layouts, on_layout_changed=on_layout_changed)

    @property
    def backend_name(self):
        return getattr(self.backend, "name", "unknown")

    def refresh(self):
        return self.backend.refresh()

    def get_system_entries(self):
        return self.backend.get_layouts()

    def get_current_index(self):
        return self.backend.get_current_index()

    def get_current_entry(self):
        current_index = self.get_current_index()
        if current_index is None:
            return None
        for entry in self.get_system_entries():
            if entry.index == current_index:
                return entry
        return None

    def get_current_vboard_layout(self):
        return resolve_system_entry_to_vboard_layout(
            self.get_current_entry(),
            self.keyboard_layouts,
        )

    def set_layout_by_index(self, index):
        return bool(self.backend.set_layout_index(index))

    def find_entry_for_vboard_layout(self, vboard_layout_id):
        layout_config = self.keyboard_layouts.get(vboard_layout_id, {})
        vboard_to_xkb, _exact = build_xkb_lookup_maps(self.keyboard_layouts)
        wanted_xkb = layout_config.get("xkb_layout") or vboard_to_xkb.get(vboard_layout_id)
        wanted_variant = layout_config.get("xkb_variant", "") or ""
        if not wanted_xkb:
            return None
        wanted_xkb, wanted_variant = parse_xkb_spec(wanted_xkb, wanted_variant)
        wanted_canonical = normalize_xkb_variant(wanted_xkb, wanted_variant)

        entries = self.get_system_entries()
        # 1. Exact match on canonical (xkb_layout, variant)
        for entry in entries:
            entry_canonical = normalize_xkb_variant(entry.xkb_layout, entry.variant)
            if entry.xkb_layout == wanted_xkb and entry_canonical == wanted_canonical:
                return entry
        # 2. Prefer default variant if present; otherwise match base layout
        for entry in entries:
            entry_canonical = normalize_xkb_variant(entry.xkb_layout, entry.variant)
            if entry.xkb_layout == wanted_xkb and not entry_canonical:
                return entry
        for entry in entries:
            if entry.xkb_layout == wanted_xkb:
                return entry
        return None

    def set_vboard_layout(self, vboard_layout_id):
        entry = self.find_entry_for_vboard_layout(vboard_layout_id)
        if entry is None:
            return False
        return self.set_layout_by_index(entry.index)

    def cycle_next_layout(self):
        entries = self.get_system_entries()
        if len(entries) < 2:
            return None

        current_index = self.get_current_index()
        positions = [entry.index for entry in entries]
        if current_index in positions:
            pos = positions.index(current_index)
            next_entry = entries[(pos + 1) % len(entries)]
        else:
            next_entry = entries[0]

        if not self.set_layout_by_index(next_entry.index):
            return None

        layout_id = resolve_system_entry_to_vboard_layout(
            next_entry,
            self.keyboard_layouts,
        )
        return (next_entry, layout_id)

    def _handle_backend_change(self, entry):
        layout_id = resolve_system_entry_to_vboard_layout(entry, self.keyboard_layouts)
        if layout_id is not None and self.on_layout_changed is not None:
            self.on_layout_changed(layout_id, entry)

    def close(self):
        self.backend.close()
