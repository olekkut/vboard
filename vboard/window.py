import configparser
import importlib
import os
import sys

from .constants import (
    ACCENT_COLOR_CHOICES,
    APP_DISPLAY_NAME,
    COMMAND_MODIFIER_KEYS,
    COLOR_CHOICES,
    COLOR_PRESETS,
    COMPACT_TV_LAYER_ALPHA,
    COMPACT_TV_LAYER_NUMBERS,
    DEFAULT_ACCENT_COLOR,
    DEFAULT_CUSTOM_KEY_BG,
    DEFAULT_CUSTOM_KEY_BORDER_COLOR,
    DEFAULT_CUSTOM_MODIFIER_BG,
    DEFAULT_CUSTOM_TEXT_COLOR,
    DEFAULT_CUSTOM_WINDOW_BG,
    DEFAULT_DWELL_TIME_MS,
    DEFAULT_FONT_SCALE,
    DEFAULT_FONT_WEIGHT,
    DEFAULT_INACTIVITY_DELAY_SECONDS,
    DEFAULT_INACTIVITY_FADE_OPACITY,
    DEFAULT_KEY_BORDER_WIDTH,
    DEFAULT_KEY_RADIUS,
    DEFAULT_KEY_SHADOW_ENABLED,
    DEFAULT_KEY_SPACING,
    DEFAULT_KEYBOARD_LAYOUT,
    DEFAULT_WINDOW_BORDER_COLOR,
    DEFAULT_WINDOW_BORDER_WIDTH,
    ENHANCED_BACKGROUND_PRESET,
    FONT_WEIGHT_CHOICES,
    FROST_LIGHT_BACKGROUND_PRESET,
    GRAPHITE_DARK_BACKGROUND_PRESET,
    HIGH_CONTRAST_TV_BACKGROUND_PRESET,
    INPUT_TRIGGER_CHOICES,
    INPUT_TRIGGER_PRESS,
    INPUT_TRIGGER_RELEASE,
    KEY_WIDTHS,
    KEYBOARD_MODE_CHOICES,
    KEYBOARD_MODE_COMPACT_TV,
    KEYBOARD_MODE_STANDARD,
    LIGHT_BACKGROUND_COLORS,
    MAX_KEY_HOLD_SECONDS,
    MODIFIER_KEYS,
    ONBOARD_BACKGROUND_PRESET,
    QUICK_SWITCH_LAYOUTS,
    SPACER_KEY_PREFIX,
    SUGGESTION_LIMIT,
    SUPPORTED_WORD_CONNECTORS,
    TV_ACTION_HIDE,
    TV_ACTION_KEYS,
    TV_ACTION_LANG,
    TV_ACTION_LAYER_ALPHA,
    TV_ACTION_LAYER_NUMBERS,
    TV_ACTION_OPTIONS,
    VERSION,
)
from .environment import DESKTOP_ENV
from .gtk import (
    APPINDICATOR_AVAILABLE,
    APPINDICATOR_BACKEND,
    AppIndicator3,
    Gdk,
    Gio,
    GLib,
    Gtk,
)
from .icons import render_icon_image, set_button_vector_icon
from .input_backends import EvdevUInputBackend, NullInputBackend, UInputBackend
from .layouts import (
    build_compact_tv_alpha_cells,
    build_compact_tv_numbers_cells,
    get_default_layout_key,
    get_layout_choices,
    get_layout_short_label,
    load_keyboard_layouts,
)
from .presets import PRESET_KEYS, UserPresetManager
from .suggestions import HunspellSuggestionEngine
from .system_layouts import (
    SystemLayoutController,
    get_next_layout_id,
    resolve_system_entry_to_vboard_layout,
)
from .themes import (
    build_theme_css,
    get_base_theme_colors,
    normalize_style_variant,
    parse_hex_rgb,
    resolve_theme_palette,
    rgb_to_hex,
)


BUG_REPORT_URL = "https://github.com/archisman-panigrahi/vboard/issues/"

STATUS_NOTIFIER_ITEM_XML = """
<node>
  <interface name="org.kde.StatusNotifierItem">
    <property name="Category" type="s" access="read"/>
    <property name="Id" type="s" access="read"/>
    <property name="Title" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="WindowId" type="i" access="read"/>
    <property name="IconName" type="s" access="read"/>
    <property name="IconThemePath" type="s" access="read"/>
    <property name="IconPixmap" type="a(iiay)" access="read"/>
    <property name="OverlayIconName" type="s" access="read"/>
    <property name="OverlayIconPixmap" type="a(iiay)" access="read"/>
    <property name="AttentionIconName" type="s" access="read"/>
    <property name="AttentionIconPixmap" type="a(iiay)" access="read"/>
    <property name="AttentionMovieName" type="s" access="read"/>
    <property name="ToolTip" type="(sa(iiay)ss)" access="read"/>
    <property name="ItemIsMenu" type="b" access="read"/>
    <property name="Menu" type="o" access="read"/>
    <method name="ContextMenu">
      <arg name="x" type="i" direction="in"/>
      <arg name="y" type="i" direction="in"/>
    </method>
    <method name="Activate">
      <arg name="x" type="i" direction="in"/>
      <arg name="y" type="i" direction="in"/>
    </method>
    <method name="SecondaryActivate">
      <arg name="x" type="i" direction="in"/>
      <arg name="y" type="i" direction="in"/>
    </method>
    <method name="Scroll">
      <arg name="delta" type="i" direction="in"/>
      <arg name="orientation" type="s" direction="in"/>
    </method>
  </interface>
</node>
"""

DBUS_MENU_XML = """
<node>
  <interface name="com.canonical.dbusmenu">
    <property name="Version" type="u" access="read"/>
    <property name="TextDirection" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="IconThemePath" type="as" access="read"/>
    <method name="GetLayout">
      <arg name="parentId" type="i" direction="in"/>
      <arg name="recursionDepth" type="i" direction="in"/>
      <arg name="propertyNames" type="as" direction="in"/>
      <arg name="revision" type="u" direction="out"/>
      <arg name="layout" type="(ia{sv}av)" direction="out"/>
    </method>
    <method name="GetGroupProperties">
      <arg name="ids" type="ai" direction="in"/>
      <arg name="propertyNames" type="as" direction="in"/>
      <arg name="properties" type="a(ia{sv})" direction="out"/>
    </method>
    <method name="GetProperty">
      <arg name="id" type="i" direction="in"/>
      <arg name="name" type="s" direction="in"/>
      <arg name="value" type="v" direction="out"/>
    </method>
    <method name="Event">
      <arg name="id" type="i" direction="in"/>
      <arg name="eventId" type="s" direction="in"/>
      <arg name="data" type="v" direction="in"/>
      <arg name="timestamp" type="u" direction="in"/>
    </method>
    <method name="EventGroup">
      <arg name="events" type="a(isvu)" direction="in"/>
      <arg name="idErrors" type="ai" direction="out"/>
    </method>
    <method name="AboutToShow">
      <arg name="id" type="i" direction="in"/>
      <arg name="needUpdate" type="b" direction="out"/>
    </method>
    <method name="AboutToShowGroup">
      <arg name="ids" type="ai" direction="in"/>
      <arg name="updatesNeeded" type="ai" direction="out"/>
      <arg name="idErrors" type="ai" direction="out"/>
    </method>
    <signal name="ItemsPropertiesUpdated">
      <arg name="updatedProps" type="a(ia{sv})"/>
      <arg name="removedProps" type="a(ias)"/>
    </signal>
    <signal name="LayoutUpdated">
      <arg name="revision" type="u"/>
      <arg name="parent" type="i"/>
    </signal>
  </interface>
</node>
"""


class StatusNotifierTrayIcon:
    OBJECT_PATH = "/StatusNotifierItem"
    MENU_PATH = "/StatusNotifierItem/Menu"
    INTERFACE_NAME = "org.kde.StatusNotifierItem"
    MENU_INTERFACE_NAME = "com.canonical.dbusmenu"
    WATCHER_NAME = "org.kde.StatusNotifierWatcher"
    WATCHER_PATH = "/StatusNotifierWatcher"
    DBUS_NAME = "org.freedesktop.DBus"
    DBUS_PATH = "/org/freedesktop/DBus"
    MENU_SEPARATOR_ID = 5
    MENU_LAYOUT_ID = 6
    MENU_SECOND_SEPARATOR_ID = 100
    MENU_LAYOUT_ID_OFFSET = 1000

    def __init__(self, window, icon_name):
        self.window = window
        self.icon_name = icon_name
        self.connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.bus_name = f"org.freedesktop.StatusNotifierItem-{os.getpid()}-1"
        self.registration_id = None
        self.menu_registration_id = None
        self.menu_revision = 1
        self.name_acquired = False
        try:
            request_result = self.connection.call_sync(
                self.DBUS_NAME,
                self.DBUS_PATH,
                self.DBUS_NAME,
                "RequestName",
                GLib.Variant("(su)", (self.bus_name, 0)),
                GLib.VariantType.new("(u)"),
                Gio.DBusCallFlags.NONE,
                1000,
                None,
            )
            request_reply = request_result.unpack()[0]
            if request_reply not in (1, 4):
                raise RuntimeError(f"Could not acquire D-Bus name {self.bus_name}")
            self.name_acquired = True

            self.node_info = Gio.DBusNodeInfo.new_for_xml(STATUS_NOTIFIER_ITEM_XML)
            self.interface_info = self.node_info.interfaces[0]
            self.menu_node_info = Gio.DBusNodeInfo.new_for_xml(DBUS_MENU_XML)
            self.menu_interface_info = self.menu_node_info.interfaces[0]
            self.menu_registration_id = self.connection.register_object(
                self.MENU_PATH,
                self.menu_interface_info,
                self.on_menu_method_call,
                self.on_menu_get_property,
                None,
            )
            self.registration_id = self.connection.register_object(
                self.OBJECT_PATH,
                self.interface_info,
                self.on_method_call,
                self.on_get_property,
                None,
            )
            self.connection.call_sync(
                self.WATCHER_NAME,
                self.WATCHER_PATH,
                self.WATCHER_NAME,
                "RegisterStatusNotifierItem",
                GLib.Variant("(s)", (self.bus_name,)),
                None,
                Gio.DBusCallFlags.NONE,
                1000,
                None,
            )
        except Exception:
            self.unregister()
            raise

    def on_method_call(
        self,
        connection,
        sender,
        object_path,
        interface_name,
        method_name,
        parameters,
        invocation,
    ):
        if method_name == "Activate":
            GLib.idle_add(self.window.on_tray_activate, None)
            invocation.return_value(None)
            return

        if method_name == "ContextMenu":
            x, y = parameters.unpack()
            GLib.idle_add(self.window.popup_tray_menu_at_coordinates, x, y)
            invocation.return_value(None)
            return

        if method_name == "SecondaryActivate":
            invocation.return_value(None)
            return

        if method_name == "Scroll":
            invocation.return_value(None)
            return

        invocation.return_dbus_error(
            "org.kde.StatusNotifierItem.Error.NotSupported",
            f"Unsupported tray method: {method_name}",
        )

    def on_get_property(
        self,
        connection,
        sender,
        object_path,
        interface_name,
        property_name,
    ):
        property_values = {
            "Category": GLib.Variant("s", "ApplicationStatus"),
            "Id": GLib.Variant("s", "vboard"),
            "Title": GLib.Variant("s", APP_DISPLAY_NAME),
            "Status": GLib.Variant("s", "Active"),
            "WindowId": GLib.Variant("i", 0),
            "IconName": GLib.Variant("s", self.icon_name),
            "IconThemePath": GLib.Variant("s", ""),
            "IconPixmap": GLib.Variant("a(iiay)", []),
            "OverlayIconName": GLib.Variant("s", ""),
            "OverlayIconPixmap": GLib.Variant("a(iiay)", []),
            "AttentionIconName": GLib.Variant("s", ""),
            "AttentionIconPixmap": GLib.Variant("a(iiay)", []),
            "AttentionMovieName": GLib.Variant("s", ""),
            "ToolTip": GLib.Variant(
                "(sa(iiay)ss)",
                (self.icon_name, [], APP_DISPLAY_NAME, "Virtual Keyboard"),
            ),
            "ItemIsMenu": GLib.Variant("b", False),
            "Menu": GLib.Variant("o", self.MENU_PATH),
        }
        return property_values.get(property_name)

    def on_menu_method_call(
        self,
        connection,
        sender,
        object_path,
        interface_name,
        method_name,
        parameters,
        invocation,
    ):
        if method_name == "GetLayout":
            parent_id, _recursion_depth, _property_names = parameters.unpack()
            invocation.return_value(
                GLib.Variant(
                    "(u(ia{sv}av))",
                    (self.menu_revision, self.get_menu_layout(parent_id)),
                )
            )
            return

        if method_name == "GetGroupProperties":
            ids, property_names = parameters.unpack()
            invocation.return_value(
                GLib.Variant(
                    "(a(ia{sv}))",
                    ([(item_id, self.get_menu_properties(item_id)) for item_id in ids],),
                )
            )
            return

        if method_name == "GetProperty":
            item_id, property_name = parameters.unpack()
            value = self.get_menu_properties(item_id).get(
                property_name,
                GLib.Variant("s", ""),
            )
            invocation.return_value(GLib.Variant("(v)", (value,)))
            return

        if method_name == "Event":
            item_id, event_id, data, timestamp = parameters.unpack()
            self.handle_menu_event(item_id, event_id)
            invocation.return_value(None)
            return

        if method_name == "EventGroup":
            for item_id, event_id, data, timestamp in parameters.unpack()[0]:
                self.handle_menu_event(item_id, event_id)
            invocation.return_value(GLib.Variant("(ai)", ([],)))
            return

        if method_name == "AboutToShow":
            invocation.return_value(GLib.Variant("(b)", (False,)))
            return

        if method_name == "AboutToShowGroup":
            invocation.return_value(GLib.Variant("(aiai)", ([], [])))
            return

        invocation.return_dbus_error(
            "com.canonical.dbusmenu.Error.NotSupported",
            f"Unsupported menu method: {method_name}",
        )

    def on_menu_get_property(
        self,
        connection,
        sender,
        object_path,
        interface_name,
        property_name,
    ):
        property_values = {
            "Version": GLib.Variant("u", 3),
            "TextDirection": GLib.Variant("s", "ltr"),
            "Status": GLib.Variant("s", "normal"),
            "IconThemePath": GLib.Variant("as", []),
        }
        return property_values.get(property_name)

    def menu_rows(self):
        rows = [
            (1, {"label": "Hide" if self.window.get_visible() else "Show"}),
            (
                2,
                {
                    "label": "Text Prediction",
                    "toggle-type": "checkmark",
                    "toggle-state": int(self.window.text_prediction_enabled),
                },
            ),
            (
                3,
                {
                    "label": "Swipe Typing",
                    "toggle-type": "checkmark",
                    "toggle-state": int(self.window.gesture_enabled),
                },
            ),
            (
                4,
                {
                    "label": "Visual Feedback",
                    "enabled": self.window.gesture_enabled,
                    "toggle-type": "checkmark",
                    "toggle-state": int(
                        self.window.gesture_visual_feedback_enabled
                    ),
                },
            ),
            (
                12,
                {
                    "label": "Start Minimized",
                    "toggle-type": "checkmark",
                    "toggle-state": int(self.window.start_minimized),
                },
            ),
            (
                11,
                {
                    "label": "Compact for TV Layout",
                    "toggle-type": "checkmark",
                    "toggle-state": int(
                        self.window.keyboard_mode == KEYBOARD_MODE_COMPACT_TV
                    ),
                },
            ),
            (
                self.MENU_SEPARATOR_ID,
                {"type": "separator", "enabled": False},
            ),
            (
                self.MENU_LAYOUT_ID,
                {
                    "label": "Keyboard Layout",
                    "children-display": "submenu",
                },
            ),
            (
                self.MENU_SECOND_SEPARATOR_ID,
                {"type": "separator", "enabled": False},
            ),
            (8, {"label": "About"}),
            (10, {"label": "Report bugs"}),
            (9, {"label": "Quit"}),
        ]
        return rows

    def layout_item_id(self, index):
        return self.MENU_LAYOUT_ID_OFFSET + index

    def get_menu_properties(self, item_id):
        properties = {"enabled": True, "visible": True}
        for row_id, row_properties in self.menu_rows():
            if row_id == item_id:
                properties.update(row_properties)
                break
        else:
            for index, (layout_key, layout_label) in enumerate(
                self.window.keyboard_layout_choices
            ):
                if self.layout_item_id(index) == item_id:
                    properties.update(
                        {
                            "label": layout_label,
                            "toggle-type": "radio",
                            "toggle-state": int(
                                layout_key == self.window.keyboard_layout
                            ),
                        }
                    )
                    break

        return {
            name: self.menu_property_variant(value)
            for name, value in properties.items()
        }

    def menu_property_variant(self, value):
        if isinstance(value, bool):
            return GLib.Variant("b", value)
        if isinstance(value, int):
            return GLib.Variant("i", value)
        return GLib.Variant("s", value)

    def menu_layout_item(self, item_id, children=None):
        return GLib.Variant(
            "(ia{sv}av)",
            (item_id, self.get_menu_properties(item_id), children or []),
        )

    def get_menu_layout(self, parent_id=0):
        layout_children = [
            self.menu_layout_item(self.layout_item_id(index))
            for index, _choice in enumerate(self.window.keyboard_layout_choices)
        ]
        if parent_id == self.MENU_LAYOUT_ID:
            return (
                self.MENU_LAYOUT_ID,
                self.get_menu_properties(self.MENU_LAYOUT_ID),
                layout_children,
            )
        children = []
        for item_id, _properties in self.menu_rows():
            if item_id == self.MENU_LAYOUT_ID:
                children.append(self.menu_layout_item(item_id, layout_children))
            else:
                children.append(self.menu_layout_item(item_id))
        return (0, {}, children)

    @staticmethod
    def _run_once(callback, *args):
        callback(*args)
        return False

    def handle_menu_event(self, item_id, event_id):
        if event_id not in ("clicked", "opened"):
            return
        if event_id == "opened":
            self.emit_menu_updated()
            return

        actions = {
            1: lambda: self.window.on_tray_activate(None),
            2: lambda: self.window.set_text_prediction_enabled(
                not self.window.text_prediction_enabled
            ),
            3: self.toggle_gesture_typing,
            4: lambda: self.window.set_gesture_visual_feedback_enabled(
                not self.window.gesture_visual_feedback_enabled
            ),
            8: lambda: self.window.on_tray_about(None),
            9: lambda: self.window.on_tray_quit(None),
            10: lambda: self.window.open_bug_report_url(),
            11: lambda: self.window.set_keyboard_mode(
                KEYBOARD_MODE_STANDARD
                if self.window.keyboard_mode == KEYBOARD_MODE_COMPACT_TV
                else KEYBOARD_MODE_COMPACT_TV
            ),
            12: lambda: self.window.set_start_minimized(
                not self.window.start_minimized
            ),
        }
        if item_id in actions:
            GLib.idle_add(self._run_once, actions[item_id])
            return

        layout_index = item_id - self.MENU_LAYOUT_ID_OFFSET
        if 0 <= layout_index < len(self.window.keyboard_layout_choices):
            layout_key = self.window.keyboard_layout_choices[layout_index][0]
            GLib.idle_add(self._run_once, self.window.set_keyboard_layout, layout_key)

    def toggle_gesture_typing(self):
        if self.window.gesture_enabled:
            self.window.disable_gesture_typing()
        else:
            self.window.enable_gesture_typing()

    def emit_menu_updated(self):
        if self.menu_registration_id is None:
            return
        self.menu_revision += 1
        self.connection.emit_signal(
            None,
            self.MENU_PATH,
            self.MENU_INTERFACE_NAME,
            "LayoutUpdated",
            GLib.Variant("(ui)", (self.menu_revision, 0)),
        )

    def unregister(self):
        if self.menu_registration_id is not None:
            self.connection.unregister_object(self.menu_registration_id)
            self.menu_registration_id = None
        if self.registration_id is not None:
            self.connection.unregister_object(self.registration_id)
            self.registration_id = None
        if self.name_acquired:
            try:
                self.connection.call_sync(
                    self.DBUS_NAME,
                    self.DBUS_PATH,
                    self.DBUS_NAME,
                    "ReleaseName",
                    GLib.Variant("(s)", (self.bus_name,)),
                    GLib.VariantType.new("(u)"),
                    Gio.DBusCallFlags.NONE,
                    1000,
                    None,
                )
            except Exception:
                pass
            self.name_acquired = False


class VirtualKeyboard(Gtk.Window):
    BASE_GRID_WIDTH = 920
    BASE_KEY_HEIGHT = 52
    BASE_KEY_FONT_SIZE = 16
    BASE_HEADER_FONT_SIZE = 13
    BASE_SUGGESTION_HEIGHT = 34
    BASE_SUGGESTION_FONT_SIZE = 15
    BASE_SUGGESTION_SPACING = 4
    BASE_SUGGESTION_MARGIN = 3
    BASE_SUGGESTION_MARGIN_BOTTOM = 1

    def __init__(self, application=None):
        super().__init__(title=APP_DISPLAY_NAME, name="toplevel")
        if application is not None:
            self.set_application(application)

        self.exiting = False
        self.set_border_width(0)
        self.set_resizable(True)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.stick()
        self.set_modal(False)
        self.set_focus_on_map(False)
        self.set_can_focus(False)
        self.set_accept_focus(False)
        self.set_deletable(True)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        min_geometry = Gdk.Geometry()
        min_geometry.min_width = 420
        min_geometry.min_height = 180
        self.set_geometry_hints(None, min_geometry, Gdk.WindowHints.MIN_SIZE)

        self.connect("delete-event", self.on_delete_event)
        self.connect("map-event", self.on_map_keep_above)
        self.connect("window-state-event", self.on_window_state_changed)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.BUTTON1_MOTION_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
        )
        self.connect("button-press-event", self.on_window_button_press_event)
        self.connect("motion-notify-event", self.on_window_motion_event)
        self.connect("button-release-event", self.on_window_button_release_event)
        self.connect("leave-notify-event", self.on_window_leave_notify_event)
        self.connect("enter-notify-event", self.on_window_enter_notify_event)
        self._keep_above_retries = 0
        self._keep_above_timer_id = None
        self._watchdog_source = None
        self._inactivity_timer_id = None
        self._scale_timer_id = None
        self._is_faded = False
        self._dwell_timer_id = None
        self._dwell_target = None
        self._pending_release_key = None
        self._auto_cap_armed = False
        self.width = 0
        self.height = 0
        self.pos_x = 0
        self.pos_y = 0
        self.config_pos_x = 0
        self.config_pos_y = 0
        self.set_position(Gtk.WindowPosition.NONE)

        self.CONFIG_DIR = os.path.expanduser("~/.config/vboard")
        self.CONFIG_FILE = os.path.join(self.CONFIG_DIR, "settings.conf")
        self.config = configparser.ConfigParser()
        self.preset_manager = UserPresetManager(os.path.join(self.CONFIG_DIR, "presets"))
        self.active_preset_name = ""
        self.keyboard_layouts = load_keyboard_layouts(
            os.path.join(self.CONFIG_DIR, "layouts")
        )
        self.keyboard_layout_choices = get_layout_choices(self.keyboard_layouts)

        self.bg_color = "0,0,0"
        self.opacity = "0.92"
        self.text_color = "#F5F5F7"
        self.style_variant = "graphite_dark"
        self.accent_color = DEFAULT_ACCENT_COLOR
        self.font_scale = DEFAULT_FONT_SCALE
        self.font_weight = DEFAULT_FONT_WEIGHT
        self.key_corner_radius = DEFAULT_KEY_RADIUS
        self.key_spacing = DEFAULT_KEY_SPACING
        self.key_border_width = DEFAULT_KEY_BORDER_WIDTH
        self.window_border_width = DEFAULT_WINDOW_BORDER_WIDTH
        self.window_border_color = DEFAULT_WINDOW_BORDER_COLOR
        self.key_shadow_enabled = DEFAULT_KEY_SHADOW_ENABLED
        self.use_custom_colors = False
        self.custom_window_bg = DEFAULT_CUSTOM_WINDOW_BG
        self.custom_key_bg = DEFAULT_CUSTOM_KEY_BG
        self.custom_modifier_bg = DEFAULT_CUSTOM_MODIFIER_BG
        self.custom_text_color = DEFAULT_CUSTOM_TEXT_COLOR
        self.custom_key_border_color = DEFAULT_CUSTOM_KEY_BORDER_COLOR
        self.text_prediction_enabled = True
        self.show_media_row = False
        self.show_current_text_bar = False
        self.show_fast_layout_bar = True
        self.show_modifier_hints = True
        self.input_trigger_mode = INPUT_TRIGGER_PRESS
        self.auto_capitalize = False
        self.auto_space_after_suggestion = False
        self.sticky_modifier_lock = True
        self.fade_on_inactivity = False
        self.inactivity_delay_seconds = DEFAULT_INACTIVITY_DELAY_SECONDS
        self.inactivity_fade_opacity = DEFAULT_INACTIVITY_FADE_OPACITY
        self.dwell_enabled = False
        self.dwell_time_ms = DEFAULT_DWELL_TIME_MS
        self.gesture_enabled = True
        self.gesture_visual_feedback_enabled = True
        self.start_minimized = False
        self.sync_system_layout = True
        self.keyboard_mode = KEYBOARD_MODE_STANDARD
        self.compact_tv_layer = COMPACT_TV_LAYER_ALPHA
        self.keyboard_layout = DEFAULT_KEYBOARD_LAYOUT
        self.system_layout_controller = None
        self.read_settings()
        self.initialize_system_layout_sync()

        self.modifiers = {mod_key: False for mod_key in MODIFIER_KEYS}
        self.locked_modifiers = {mod_key: False for mod_key in MODIFIER_KEYS}
        self.color_map = dict(COLOR_CHOICES)
        if self.width != 0 and self.height != 0:
            self.set_default_size(max(420, self.width), max(180, self.height))

        self.header = Gtk.HeaderBar()
        self.header.set_title(APP_DISPLAY_NAME)
        self.header.set_show_close_button(True)
        self.buttons = []
        self.menu_button = None
        self.media_buttons = []
        self.current_text_clear_button = None
        self.resize_grip = None
        self.key_buttons = {}
        self.modifier_buttons = {}
        self.layout_button = None
        self.layout_buttons = []
        self.layout_button_box = None
        self.current_word = ""
        self.current_text_buffer = ""
        self.suggestion_engine = HunspellSuggestionEngine(
            self.normalize_keyboard_layout(self.keyboard_layout)
        )
        self.suggestion_buttons = []
        self.suggestion_override = None
        self.color_combobox = Gtk.ComboBoxText()
        self.tray_icon = None
        self.tray_menu = None
        self.tray_toggle_item = None
        self.tray_prediction_item = None
        self.tray_gesture_item = None
        self.tray_visual_feedback_item = None
        self.tray_start_minimized_item = None
        self.tray_compact_tv_item = None
        self.tray_layout_items = {}
        self.settings_dialog = None
        self.settings_preset_combo = None
        self.settings_preset_delete_btn = None
        self.settings_gesture_check = None
        self.settings_visual_feedback_check = None
        self.settings_sync_layout_check = None
        self.settings_layout_combo = None
        self.settings_mode_combo = None
        self.settings_theme_combo = None
        self.settings_accent_combo = None
        self.settings_accent_color_btn = None
        self.settings_custom_colors_check = None
        self.settings_win_bg_btn = None
        self.settings_key_bg_btn = None
        self.settings_mod_bg_btn = None
        self.settings_text_color_btn = None
        self.settings_key_border_color_btn = None
        self.settings_win_border_color_btn = None
        self.settings_win_border_width_scale = None
        self.settings_key_border_width_scale = None
        self.settings_font_weight_combo = None
        self.settings_key_shadow_check = None
        self.settings_opacity_scale = None
        self.settings_font_scale = None
        self.settings_radius_scale = None
        self.settings_spacing_scale = None
        self.settings_prediction_check = None
        self.settings_media_row_check = None
        self.settings_current_text_check = None
        self.settings_fast_layout_check = None
        self.settings_modifier_hints_check = None
        self.settings_trigger_combo = None
        self.settings_auto_cap_check = None
        self.settings_auto_space_check = None
        self.settings_sticky_lock_check = None
        self.settings_dwell_check = None
        self.settings_dwell_scale = None
        self.settings_fade_check = None
        self.settings_fade_delay_spin = None
        self.settings_fade_opacity_scale = None
        self.settings_start_minimized_check = None
        self._syncing_settings_dialog = False
        self.css_provider = Gtk.CssProvider()
        self._css_provider_registered = False
        self._last_suggestion_scale = None
        self.caps_lock_active = False
        self._syncing_tray_items = False
        self.layout_character_lookup = {}
        self.key_font_size = self.BASE_KEY_FONT_SIZE
        self.secondary_key_font_size = max(
            8, int(round(self.BASE_KEY_FONT_SIZE * 0.75))
        )
        self.header_font_size = self.BASE_HEADER_FONT_SIZE
        self.suggestion_font_size = self.BASE_SUGGESTION_FONT_SIZE
        self.layout_scale = 1.0
        self.gesture_controller = None
        self.set_titlebar(self.header)
        self.set_name("vboard-main")
        self.set_default_icon_name(self.get_app_icon_name())

        self.create_settings()
        self.create_tray_icon()
        self.backend = self._initialize_input_backend()

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_name("vboard-content")
        self.content_box = content
        self.add(content)

        self.media_bar = self.create_media_bar()
        self.media_bar.set_no_show_all(True)
        content.pack_start(self.media_bar, False, False, 0)
        self.update_media_bar_visibility()

        self.current_text_bar, self.current_text_label = self.create_current_text_bar()
        self.current_text_bar.set_no_show_all(True)
        content.pack_start(self.current_text_bar, False, False, 0)
        self.update_current_text_bar_visibility()

        self.suggestion_revealer = Gtk.Revealer()
        self.suggestion_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.suggestion_revealer.set_no_show_all(True)
        self.suggestion_revealer.set_reveal_child(self.text_prediction_enabled)

        self.suggestion_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.suggestion_bar.set_name("suggestion-bar")
        self.suggestion_bar.set_margin_start(3)
        self.suggestion_bar.set_margin_end(3)
        self.suggestion_bar.set_margin_top(3)
        self.suggestion_bar.set_margin_bottom(1)
        self.suggestion_revealer.add(self.suggestion_bar)
        self.create_suggestion_buttons()

        grid_overlay = Gtk.Overlay()
        self.grid_overlay = grid_overlay
        content.pack_start(self.suggestion_revealer, False, False, 0)
        self.update_suggestion_bar_visibility()
        content.pack_start(grid_overlay, True, True, 0)

        grid = Gtk.Grid()
        grid.set_row_homogeneous(True)
        grid.set_column_homogeneous(True)
        grid.set_margin_start(3)
        grid.set_margin_end(3)
        grid.set_name("grid")
        grid.connect("size-allocate", self.on_grid_size_allocate)
        self.grid = grid
        grid_overlay.add(grid)

        self.resize_grip = self.create_resize_grip()
        grid_overlay.add_overlay(self.resize_grip)

        self.apply_css()
        if self.text_prediction_enabled:
            GLib.idle_add(self.preload_suggestions)
        GLib.idle_add(self.update_suggestion_bar_scale)

        self.keyboard_layout = self.normalize_keyboard_layout(self.keyboard_layout)
        self.refresh_layout_character_lookup()
        self.populate_keyboard_grid()
        self.update_layout_button()
        self.update_fast_layout_bar_visibility()
        self.refresh_vector_icons()

        if self.gesture_enabled:
            self.enable_gesture_typing(sync_controls=False, save=False)

        self.sync_caps_lock_from_system(connect=True)
        self._watchdog_source = GLib.timeout_add(250, self._watchdog_tick)
        self.reset_inactivity_timer()

    def _initialize_input_backend(self):
        errors = []
        try:
            return UInputBackend()
        except Exception as exc:
            errors.append(f"python-uinput: {exc}")

        try:
            backend = EvdevUInputBackend()
            print("Using python-evdev uinput fallback backend.")
            return backend
        except Exception as exc:
            errors.append(f"python-evdev: {exc}")

        return NullInputBackend(
            f"Could not initialize uinput backend ({'; '.join(errors)}); key output is disabled"
        )

    def _watchdog_tick(self):
        if getattr(self, "backend", None) is not None:
            self.backend.check_stuck_keys(MAX_KEY_HOLD_SECONDS)
        return True

    def stop_all_active_keys(self):
        self.stop_key_repeat()
        self.cancel_dwell_timer()
        self._pending_release_key = None
        if getattr(self, "backend", None) is not None:
            self.backend.release_all_keys()

    def get_active_icon_color(self):
        palette = resolve_theme_palette(
            style_variant=self.style_variant,
            bg_color=self.bg_color,
            text_color=self.text_color,
            accent_hex=self.accent_color,
            use_custom_colors=self.use_custom_colors,
            custom_window_bg=self.custom_window_bg,
            custom_key_bg=self.custom_key_bg,
            custom_modifier_bg=self.custom_modifier_bg,
            custom_text_color=self.custom_text_color,
            custom_key_border_color=self.custom_key_border_color,
            window_border_color=self.window_border_color,
        )
        return palette["icon_color"]

    def refresh_vector_icons(self):
        icon_color = self.get_active_icon_color()
        header_icon_px = max(13, min(22, int(round(self.header_font_size * 1.25))))
        media_icon_px = max(14, min(26, int(round(self.secondary_key_font_size * 1.35))))
        key_icon_px = max(15, min(30, int(round(self.key_font_size * 1.15))))

        if getattr(self, "menu_button", None) is not None:
            set_button_vector_icon(
                self.menu_button, "menu", size_px=header_icon_px, color=icon_color
            )
        for btn, icon_name in getattr(self, "media_buttons", ()):
            set_button_vector_icon(
                btn, icon_name, size_px=media_icon_px, color=icon_color
            )
        if getattr(self, "current_text_clear_button", None) is not None:
            set_button_vector_icon(
                self.current_text_clear_button,
                "clear",
                size_px=max(12, header_icon_px - 1),
                color=icon_color,
            )
        if getattr(self, "resize_grip", None) is not None:
            grip_img = render_icon_image("resize-grip", size_px=14, color=icon_color)
            for child in self.resize_grip.get_children():
                self.resize_grip.remove(child)
            self.resize_grip.add(grip_img)
            self.resize_grip.show_all()

        key_buttons = getattr(self, "key_buttons", {})
        options_btn = key_buttons.get(TV_ACTION_OPTIONS)
        if options_btn is not None:
            set_button_vector_icon(
                options_btn, "settings", size_px=key_icon_px, color=icon_color
            )
        if self.keyboard_mode == KEYBOARD_MODE_COMPACT_TV:
            bs_btn = key_buttons.get("Backspace")
            if bs_btn is not None:
                set_button_vector_icon(
                    bs_btn, "backspace", size_px=key_icon_px, color=icon_color
                )

    def create_resize_grip(self):
        grip = Gtk.EventBox()
        grip.set_name("resize-grip")
        grip.set_halign(Gtk.Align.END)
        grip.set_valign(Gtk.Align.END)
        grip.set_visible_window(False)
        grip.set_tooltip_text("Drag to resize keyboard")
        grip.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.ENTER_NOTIFY_MASK
        )
        grip.connect("realize", self._on_resize_grip_realize)
        grip.connect("button-press-event", self._on_resize_grip_press)
        grip_img = render_icon_image(
            "resize-grip", size_px=14, color=self.get_active_icon_color()
        )
        grip.add(grip_img)
        return grip

    def _on_resize_grip_realize(self, widget):
        gdk_win = widget.get_window()
        display = widget.get_display()
        if gdk_win is not None and display is not None:
            cursor = Gdk.Cursor.new_from_name(display, "nwse-resize")
            if cursor is not None:
                gdk_win.set_cursor(cursor)

    def _on_resize_grip_press(self, widget, event):
        if event.button == 1:
            self.begin_resize_drag(
                Gdk.WindowEdge.SOUTH_EAST,
                event.button,
                int(event.x_root),
                int(event.y_root),
                event.time,
            )
            return True
        return False

    def _detect_resize_edge(self, x, y, margin=6):
        width, height = self.get_size()
        if width <= 0 or height <= 0:
            return None
        left = x <= margin
        right = x >= width - margin
        top = y <= margin
        bottom = y >= height - margin
        if top and left:
            return Gdk.WindowEdge.NORTH_WEST
        if top and right:
            return Gdk.WindowEdge.NORTH_EAST
        if bottom and left:
            return Gdk.WindowEdge.SOUTH_WEST
        if bottom and right:
            return Gdk.WindowEdge.SOUTH_EAST
        if left:
            return Gdk.WindowEdge.WEST
        if right:
            return Gdk.WindowEdge.EAST
        if top:
            return Gdk.WindowEdge.NORTH
        if bottom:
            return Gdk.WindowEdge.SOUTH
        return None

    def on_window_button_press_event(self, widget, event):
        if event.button != 1:
            return False
        edge = self._detect_resize_edge(event.x, event.y)
        if edge is not None:
            self.begin_resize_drag(
                edge,
                event.button,
                int(event.x_root),
                int(event.y_root),
                event.time,
            )
            return True
        return False

    def on_window_motion_event(self, widget, event):
        if self.gesture_controller is not None:
            self.gesture_controller.handle_key_motion(widget, event)
        return False

    def create_media_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        bar.set_name("media-bar")
        bar.set_margin_start(6)
        bar.set_margin_end(6)
        bar.set_margin_top(4)
        bar.set_margin_bottom(0)
        controls = (
            ("brightness-down", "BrightnessDown", "Decrease screen brightness"),
            ("brightness-up", "BrightnessUp", "Increase screen brightness"),
            ("media-previous", "PreviousSong", "Previous track"),
            ("media-play-pause", "PlayPause", "Play / Pause"),
            ("media-next", "NextSong", "Next track"),
            ("audio-mute", "VolumeMute", "Mute / Unmute"),
            ("audio-low", "VolumeDown", "Volume down"),
            ("audio-high", "VolumeUp", "Volume up"),
            ("screenshot", "Print", "Screenshot"),
        )
        self.media_buttons = []
        icon_color = self.get_active_icon_color()
        for icon_name, key_event, tooltip in controls:
            btn = Gtk.Button()
            btn.set_can_focus(False)
            btn.set_focus_on_click(False)
            btn.set_tooltip_text(tooltip)
            set_button_vector_icon(btn, icon_name, size_px=16, color=icon_color)
            btn.connect(
                "clicked",
                lambda _widget, k=key_event: self.on_media_key_clicked(k),
            )
            bar.pack_start(btn, True, True, 0)
            self.media_buttons.append((btn, icon_name))
        return bar

    def on_media_key_clicked(self, key_event):
        self.reset_inactivity_timer()
        empty_mods = {mod: False for mod in MODIFIER_KEYS}
        self.backend.emit_key(key_event, empty_mods)

    def update_media_bar_visibility(self):
        if not hasattr(self, "media_bar") or self.media_bar is None:
            return
        if self.show_media_row:
            for child in self.media_bar.get_children():
                child.show_all()
            self.media_bar.show()
        else:
            self.media_bar.hide()

    def create_current_text_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.set_name("current-text-bar")
        bar.set_margin_start(6)
        bar.set_margin_end(6)
        bar.set_margin_top(4)
        bar.set_margin_bottom(0)
        label = Gtk.Label(label="")
        label.set_name("current-text-label")
        label.set_xalign(0.0)
        label.set_ellipsize(3)  # Pango.EllipsizeMode.END
        label.set_single_line_mode(True)
        bar.pack_start(label, True, True, 0)

        clear_btn = Gtk.Button()
        clear_btn.set_name("current-text-clear")
        clear_btn.set_can_focus(False)
        clear_btn.set_focus_on_click(False)
        clear_btn.set_tooltip_text("Clear text preview buffer")
        set_button_vector_icon(
            clear_btn, "clear", size_px=14, color=self.get_active_icon_color()
        )
        clear_btn.connect("clicked", lambda _w: self.clear_current_text_buffer())
        self.current_text_clear_button = clear_btn
        bar.pack_end(clear_btn, False, False, 0)
        return bar, label

    def clear_current_text_buffer(self):
        self.current_text_buffer = ""
        self.update_current_text_label()

    def update_current_text_label(self):
        if not hasattr(self, "current_text_label") or self.current_text_label is None:
            return
        preview = self.current_text_buffer[-64:]
        self.current_text_label.set_text(preview if preview else "Typing preview…")

    def update_current_text_bar_visibility(self):
        if not hasattr(self, "current_text_bar") or self.current_text_bar is None:
            return
        self.update_current_text_label()
        if self.show_current_text_bar:
            for child in self.current_text_bar.get_children():
                child.show_all()
            self.current_text_bar.show()
        else:
            self.current_text_bar.hide()

    def update_fast_layout_bar_visibility(self):
        if self.layout_button_box is None:
            return
        if self.show_fast_layout_bar:
            self.layout_button_box.show_all()
        else:
            self.layout_button_box.hide()

    def cancel_inactivity_timer(self):
        if self._inactivity_timer_id is not None:
            GLib.source_remove(self._inactivity_timer_id)
            self._inactivity_timer_id = None

    def set_faded_state(self, faded):
        faded = bool(faded)
        if faded == self._is_faded:
            return
        self._is_faded = faded
        target_opacity = self.inactivity_fade_opacity if faded else 1.0
        try:
            Gtk.Widget.set_opacity(self, target_opacity)
        except Exception:
            pass

    def reset_inactivity_timer(self):
        self.cancel_inactivity_timer()
        self.set_faded_state(False)
        if not self.fade_on_inactivity:
            return
        delay_ms = max(1000, int(round(self.inactivity_delay_seconds * 1000)))
        self._inactivity_timer_id = GLib.timeout_add(
            delay_ms, self._on_inactivity_timeout
        )

    def _on_inactivity_timeout(self):
        self._inactivity_timer_id = None
        if self.fade_on_inactivity and self.get_visible():
            self.set_faded_state(True)
        return False

    def on_window_enter_notify_event(self, widget, event):
        self.reset_inactivity_timer()
        return False

    def cancel_dwell_timer(self):
        if self._dwell_timer_id is not None:
            GLib.source_remove(self._dwell_timer_id)
            self._dwell_timer_id = None
        if self._dwell_target is not None:
            prev_widget, _prev_key = self._dwell_target
            try:
                prev_widget.get_style_context().remove_class("dwell-active")
            except Exception:
                pass
            self._dwell_target = None

    def start_dwell_timer(self, widget, key_event):
        self.cancel_dwell_timer()
        if not self.dwell_enabled:
            return
        self._dwell_target = (widget, key_event)
        widget.get_style_context().add_class("dwell-active")
        delay_ms = max(250, min(3000, int(self.dwell_time_ms)))
        self._dwell_timer_id = GLib.timeout_add(
            delay_ms, self._on_dwell_timeout, widget, key_event
        )

    def _on_dwell_timeout(self, widget, key_event):
        self._dwell_timer_id = None
        if self._dwell_target is None or self._dwell_target[0] is not widget:
            return False
        try:
            widget.get_style_context().remove_class("dwell-active")
        except Exception:
            pass
        self._dwell_target = None
        self.reset_inactivity_timer()
        if key_event in TV_ACTION_KEYS:
            fake_event = type("DwellEvent", (), {"button": 1})()
            self.handle_tv_action_key(widget, fake_event, key_event)
        elif key_event == "CapsLock":
            self.toggle_caps_lock()
            self.reset_modifiers()
        elif key_event in self.modifiers:
            self.toggle_modifier_key(key_event)
        else:
            self.emit_key(key_event)
        return False

    def get_app_icon_name(self):
        icon_theme = Gtk.IconTheme.get_default()
        preferred_icon = "io.github.archisman-panigrahi.vboard"
        fallback_icon = "preferences-desktop-keyboard"
        if icon_theme and icon_theme.has_icon(preferred_icon):
            return preferred_icon
        return fallback_icon

    def create_tray_icon(self):
        icon_name = self.get_app_icon_name()
        if self.create_status_notifier_tray_icon(icon_name):
            return

        if APPINDICATOR_AVAILABLE:
            if APPINDICATOR_BACKEND == "ayatana":
                GLib.log_set_handler(
                    "libayatana-appindicator",
                    GLib.LogLevelFlags.LEVEL_WARNING,
                    lambda domain, level, message, user_data: None,
                    None,
                )

            self.tray_icon = AppIndicator3.Indicator.new(
                "vboard",
                icon_name,
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            )
            self.tray_icon.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.tray_menu = self.build_tray_menu()
            self.tray_icon.set_menu(self.tray_menu)
            return

        if self.create_status_tray_icon(icon_name):
            return

        self.clear_tray_icon(
            "Warning: Could not create tray icon. Tray disabled."
        )

    def create_status_notifier_tray_icon(self, icon_name):
        try:
            self.tray_icon = StatusNotifierTrayIcon(self, icon_name)
            self.tray_menu = self.build_tray_menu()
            print("Using native StatusNotifierItem for system tray.")
            return True
        except Exception as exc:
            self.clear_tray_icon(
                f"Warning: Could not create native StatusNotifierItem tray icon ({exc})."
            )
            return False

    def create_status_tray_icon(self, icon_name):
        try:
            self.tray_icon = Gtk.StatusIcon()
            self.tray_icon.set_from_icon_name(icon_name)
            self.tray_icon.set_tooltip_text("Vboard - Virtual Keyboard")
            self.tray_icon.connect("activate", self.on_statusicon_activate)
            self.tray_icon.connect("popup-menu", self.on_statusicon_popup_menu)
            self.tray_menu = self.build_tray_menu()
            print("Using Gtk.StatusIcon for system tray.")
            return True
        except Exception as exc:
            self.clear_tray_icon(
                f"Warning: Could not create Gtk.StatusIcon tray icon ({exc})."
            )
            return False

    def clear_tray_icon(self, warning=None):
        if self.tray_icon is not None and hasattr(self.tray_icon, "unregister"):
            self.tray_icon.unregister()
        self.tray_icon = None
        self.tray_menu = None
        self.tray_toggle_item = None
        self.tray_prediction_item = None
        self.tray_gesture_item = None
        self.tray_visual_feedback_item = None
        self.tray_start_minimized_item = None
        self.tray_compact_tv_item = None
        self.tray_layout_items = {}
        if warning:
            print(warning)

    def build_tray_menu(self):
        tray_menu = Gtk.Menu()
        self.tray_toggle_item = Gtk.MenuItem(label="Hide")
        self.tray_toggle_item.connect("activate", self.on_tray_toggle)
        tray_menu.append(self.tray_toggle_item)

        self.tray_prediction_item = Gtk.CheckMenuItem(label="Text Prediction")
        self.tray_prediction_item.connect("toggled", self.on_tray_prediction_toggled)
        tray_menu.append(self.tray_prediction_item)

        self.tray_gesture_item = Gtk.CheckMenuItem(label="Swipe Typing")
        self.tray_gesture_item.connect("toggled", self.on_tray_gesture_toggled)
        tray_menu.append(self.tray_gesture_item)

        self.tray_visual_feedback_item = Gtk.CheckMenuItem(label="Visual Feedback")
        self.tray_visual_feedback_item.connect(
            "toggled", self.on_tray_visual_feedback_toggled
        )
        tray_menu.append(self.tray_visual_feedback_item)

        self.tray_start_minimized_item = Gtk.CheckMenuItem(label="Start Minimized")
        self.tray_start_minimized_item.connect(
            "toggled", self.on_tray_start_minimized_toggled
        )
        tray_menu.append(self.tray_start_minimized_item)

        self.tray_compact_tv_item = Gtk.CheckMenuItem(label="Compact for TV Layout")
        self.tray_compact_tv_item.connect(
            "toggled", self.on_tray_compact_tv_toggled
        )
        tray_menu.append(self.tray_compact_tv_item)

        tray_menu.append(Gtk.SeparatorMenuItem())

        layout_item = Gtk.MenuItem(label="Keyboard Layout")
        layout_menu = Gtk.Menu()
        self.tray_layout_items = {}
        first_layout_item = None
        for layout_key, layout_label in self.keyboard_layout_choices:
            if first_layout_item is None:
                item = Gtk.RadioMenuItem.new_with_label(None, layout_label)
                first_layout_item = item
            else:
                item = Gtk.RadioMenuItem.new_with_label_from_widget(
                    first_layout_item,
                    layout_label,
                )
            item.connect("toggled", self.on_tray_layout_toggled, layout_key)
            layout_menu.append(item)
            self.tray_layout_items[layout_key] = item
        layout_item.set_submenu(layout_menu)
        tray_menu.append(layout_item)

        tray_menu.append(Gtk.SeparatorMenuItem())

        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", self.on_tray_about)
        tray_menu.append(about_item)

        report_bugs_item = Gtk.MenuItem(label="Report bugs")
        report_bugs_item.connect("activate", self.on_report_bugs)
        tray_menu.append(report_bugs_item)

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.on_tray_quit)
        tray_menu.append(quit_item)

        tray_menu.show_all()
        self.sync_tray_items()
        return tray_menu

    def update_tray_menu(self):
        if self.tray_toggle_item is None:
            if hasattr(self.tray_icon, "emit_menu_updated"):
                self.tray_icon.emit_menu_updated()
            return

        self.tray_toggle_item.set_label("Hide" if self.get_visible() else "Show")
        if hasattr(self.tray_icon, "emit_menu_updated"):
            self.tray_icon.emit_menu_updated()

    def toggle_visibility(self):
        if self.get_visible():
            self.stop_all_active_keys()
            self.cancel_inactivity_timer()
            self.hide()
        else:
            self.show()
            self.present()
            self.request_keep_above()
            self.reset_inactivity_timer()
        self.update_tray_menu()

    def on_tray_activate(self, icon):
        self.toggle_visibility()

    def on_statusicon_activate(self, widget):
        self.on_tray_activate(widget)

    def on_statusicon_popup_menu(self, widget, button, activate_time):
        self.popup_tray_menu(widget, button, activate_time)

    def popup_tray_menu_at_coordinates(self, x, y):
        if self.tray_menu:
            root_window = Gdk.get_default_root_window()
            if root_window is not None:
                rect = Gdk.Rectangle()
                rect.x = x
                rect.y = y
                rect.width = 1
                rect.height = 1
                self.tray_menu.popup_at_rect(
                    root_window,
                    rect,
                    Gdk.Gravity.SOUTH_EAST,
                    Gdk.Gravity.NORTH_WEST,
                    None,
                )
            else:
                self.tray_menu.popup_at_pointer(None)
        return False

    def popup_tray_menu(self, widget, button, activate_time):
        if self.tray_menu:
            self.tray_menu.popup(None, None, widget.position_menu, button, activate_time)

    def on_tray_toggle(self, widget):
        self.on_tray_activate(None)

    def on_tray_prediction_toggled(self, widget):
        if not self._syncing_tray_items:
            self.set_text_prediction_enabled(widget.get_active())

    def on_tray_gesture_toggled(self, widget):
        if self._syncing_tray_items:
            return
        if widget.get_active():
            self.enable_gesture_typing()
        else:
            self.disable_gesture_typing()

    def on_tray_visual_feedback_toggled(self, widget):
        if not self._syncing_tray_items:
            self.set_gesture_visual_feedback_enabled(widget.get_active())

    def on_tray_start_minimized_toggled(self, widget):
        if not self._syncing_tray_items:
            self.set_start_minimized(widget.get_active())

    def on_tray_compact_tv_toggled(self, widget):
        if not self._syncing_tray_items:
            self.set_keyboard_mode(
                KEYBOARD_MODE_COMPACT_TV
                if widget.get_active()
                else KEYBOARD_MODE_STANDARD
            )

    def on_tray_layout_toggled(self, widget, layout_key):
        if not self._syncing_tray_items and widget.get_active():
            self.set_keyboard_layout(layout_key)

    def sync_tray_items(self):
        self._syncing_tray_items = True
        try:
            if self.tray_prediction_item is not None:
                self.tray_prediction_item.set_active(self.text_prediction_enabled)
            if self.tray_gesture_item is not None:
                self.tray_gesture_item.set_active(self.gesture_enabled)
            if self.tray_visual_feedback_item is not None:
                self.tray_visual_feedback_item.set_active(
                    self.gesture_visual_feedback_enabled
                )
                self.tray_visual_feedback_item.set_sensitive(self.gesture_enabled)
            if self.tray_start_minimized_item is not None:
                self.tray_start_minimized_item.set_active(self.start_minimized)
            if self.tray_compact_tv_item is not None:
                self.tray_compact_tv_item.set_active(
                    self.keyboard_mode == KEYBOARD_MODE_COMPACT_TV
                )
            for layout_key, item in self.tray_layout_items.items():
                item.set_active(layout_key == self.keyboard_layout)
        finally:
            self._syncing_tray_items = False
        if hasattr(self.tray_icon, "emit_menu_updated"):
            self.tray_icon.emit_menu_updated()

    def normalize_keyboard_layout(self, layout_key):
        if layout_key in self.keyboard_layouts:
            return layout_key
        return get_default_layout_key(self.keyboard_layouts)

    def normalize_keyboard_mode(self, mode):
        if mode == KEYBOARD_MODE_COMPACT_TV:
            return KEYBOARD_MODE_COMPACT_TV
        return KEYBOARD_MODE_STANDARD

    def get_layout_config(self):
        return self.keyboard_layouts[self.keyboard_layout]

    def get_active_key_rows(self):
        return self.get_layout_config()["rows"]

    def get_active_key_labels(self):
        return self.get_layout_config()["labels"]

    def get_active_shifted_map(self):
        return self.get_layout_config()["shifted"]

    def get_active_altgr_map(self):
        return self.get_layout_config().get("altgr", {})

    def get_active_altgr_shifted_map(self):
        return self.get_layout_config().get("altgr_shifted", {})

    def get_current_layout_short_label(self):
        return get_layout_short_label(self.keyboard_layout, self.keyboard_layouts)

    def initialize_system_layout_sync(self):
        self.close_system_layout_sync()
        controller = SystemLayoutController.create(
            self.keyboard_layouts,
            on_layout_changed=self.on_system_layout_changed,
        )
        if controller is None:
            return

        self.system_layout_controller = controller
        if self.sync_system_layout:
            try:
                current_layout = controller.get_current_vboard_layout()
            except (GLib.Error, OSError, RuntimeError) as exc:
                print(f"Warning: Could not read active system keyboard layout ({exc}).")
                return
            if current_layout in self.keyboard_layouts:
                self.keyboard_layout = current_layout

    def close_system_layout_sync(self):
        if self.system_layout_controller is not None:
            try:
                self.system_layout_controller.close()
            except Exception:
                pass
            self.system_layout_controller = None

    def on_system_layout_changed(self, layout_key, entry=None):
        if not self.sync_system_layout:
            return
        if layout_key in self.keyboard_layouts:
            self.set_keyboard_layout(layout_key, sync_system=False, save=False)
        current_signature = [
            (lid, e.index if e is not None else None)
            for _btn, lid, e in self.layout_buttons
        ]
        new_signature = [
            (lid, e.index if e is not None else None)
            for _sc, _dn, lid, e in self.get_fast_switch_items()
        ]
        if new_signature != current_signature:
            self.rebuild_layout_buttons()
        else:
            self.update_layout_button()

    def set_sync_system_layout(self, enabled):
        enabled = bool(enabled)
        if enabled == self.sync_system_layout:
            return

        self.sync_system_layout = enabled
        if enabled:
            if self.system_layout_controller is None:
                self.initialize_system_layout_sync()
            elif self.system_layout_controller is not None:
                try:
                    current_layout = (
                        self.system_layout_controller.get_current_vboard_layout()
                    )
                except (GLib.Error, OSError, RuntimeError):
                    current_layout = None
                if current_layout in self.keyboard_layouts:
                    self.set_keyboard_layout(
                        current_layout, sync_system=False, save=False
                    )
        self.rebuild_layout_buttons()
        self.sync_settings_dialog_controls()
        self.save_settings()

    def get_fast_switch_items(self):
        """Return [(short_label, tooltip_label, layout_id, system_entry_or_None), ...] for top-bar fast switch."""
        items = []
        seen_layout_ids = set()
        seen_xkb_layouts = set()

        if self.sync_system_layout and self.system_layout_controller is not None:
            try:
                system_entries = self.system_layout_controller.get_system_entries()
            except (GLib.Error, OSError, RuntimeError):
                system_entries = ()

            for entry in system_entries:
                resolved_id = resolve_system_entry_to_vboard_layout(
                    entry, self.keyboard_layouts
                )
                short_code = (
                    get_layout_short_label(resolved_id, self.keyboard_layouts)
                    if resolved_id
                    else entry.xkb_layout[:3].upper()
                )
                if resolved_id is not None:
                    seen_layout_ids.add(resolved_id)
                if entry.xkb_layout:
                    seen_xkb_layouts.add(entry.xkb_layout)
                items.append((short_code, entry.display_name, resolved_id, entry))

            if len(items) >= 2:
                if any(
                    lid in seen_layout_ids for lid in ("pl", "uk", "ru")
                ) or any(xkb in seen_xkb_layouts for xkb in ("pl", "ua", "ru")):
                    for layout_id, xkb_code in (("pl", "pl"), ("uk", "ua"), ("ru", "ru")):
                        if (
                            layout_id in self.keyboard_layouts
                            and layout_id not in seen_layout_ids
                            and xkb_code not in seen_xkb_layouts
                        ):
                            layout_config = self.keyboard_layouts[layout_id]
                            short_code = get_layout_short_label(layout_id, self.keyboard_layouts)
                            items.append((short_code, layout_config["label"], layout_id, None))
                            seen_layout_ids.add(layout_id)
                            seen_xkb_layouts.add(xkb_code)
                return items

        quick_ids = [
            layout_id
            for layout_id in QUICK_SWITCH_LAYOUTS
            if layout_id in self.keyboard_layouts
        ]
        if self.keyboard_layout in self.keyboard_layouts and self.keyboard_layout not in quick_ids:
            quick_ids.append(self.keyboard_layout)

        for layout_id in quick_ids:
            if layout_id in seen_layout_ids:
                continue
            layout_config = self.keyboard_layouts[layout_id]
            short_code = get_layout_short_label(layout_id, self.keyboard_layouts)
            items.append((short_code, layout_config["label"], layout_id, None))

        return items

    def rebuild_layout_buttons(self):
        if self.layout_button_box is None:
            return

        for child in self.layout_button_box.get_children():
            self.layout_button_box.remove(child)

        self.layout_buttons = []
        self.layout_button = None

        items = self.get_fast_switch_items()
        for short_code, display_name, layout_id, entry in items:
            button = Gtk.Button(label=short_code)
            button.set_can_focus(False)
            button.set_focus_on_click(False)
            button.set_name("layout-button")
            button.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            button.connect(
                "button-press-event",
                self.on_fast_layout_button_press_event,
                layout_id,
                entry,
            )
            tooltip = f"Switch to {display_name} ({short_code})"
            if entry is None and self.sync_system_layout and self.system_layout_controller is not None:
                tooltip += "\nAdd this layout in System Settings → Keyboard → Layouts for OS typing sync"
            else:
                tooltip += "\nLeft-click to switch, right-click for all layouts"
            button.set_tooltip_text(tooltip)
            self.layout_button_box.pack_start(button, False, False, 0)
            self.layout_buttons.append((button, layout_id, entry))

        self.update_fast_layout_bar_visibility()
        self.update_layout_button()

    def activate_fast_switch_item(self, layout_id, entry=None):
        if (
            entry is None
            and layout_id is not None
            and self.sync_system_layout
            and self.system_layout_controller is not None
        ):
            try:
                self.system_layout_controller.refresh()
                entry = self.system_layout_controller.find_entry_for_vboard_layout(
                    layout_id
                )
            except (GLib.Error, OSError, RuntimeError):
                entry = None

        if entry is not None and self.sync_system_layout and self.system_layout_controller is not None:
            self.select_system_layout_entry(entry)
        elif layout_id is not None:
            self.set_keyboard_layout(layout_id)

    def on_fast_layout_button_press_event(self, widget, event, layout_id, entry):
        if event.button == 3:
            self.popup_layout_menu(widget, event)
            return True
        if event.button == 1:
            self.activate_fast_switch_item(layout_id, entry)
            return True
        return False

    def update_layout_button(self):
        short_label = self.get_current_layout_short_label()

        current_system_index = None
        if self.sync_system_layout and self.system_layout_controller is not None:
            try:
                current_system_index = self.system_layout_controller.get_current_index()
            except (GLib.Error, OSError, RuntimeError):
                current_system_index = None

        matching_buttons = [
            (button, layout_id, entry)
            for button, layout_id, entry in self.layout_buttons
            if layout_id == self.keyboard_layout
        ]
        active_button = None
        if len(matching_buttons) == 1:
            active_button = matching_buttons[0][0]
        elif len(matching_buttons) > 1:
            for button, _layout_id, entry in matching_buttons:
                if (
                    entry is not None
                    and current_system_index is not None
                    and entry.index == current_system_index
                ):
                    active_button = button
                    break
            if active_button is None:
                active_button = matching_buttons[0][0]

        stale_flags = (
            Gtk.StateFlags.ACTIVE
            | Gtk.StateFlags.PRELIGHT
            | Gtk.StateFlags.FOCUSED
        )
        for button, _layout_id, _entry in self.layout_buttons:
            ctx = button.get_style_context()
            if button is active_button:
                ctx.add_class("active-layout")
            else:
                ctx.remove_class("active-layout")
                button.unset_state_flags(stale_flags)

        if active_button is not None:
            self.layout_button = active_button
        elif self.layout_buttons:
            self.layout_button = self.layout_buttons[0][0]

        tv_lang_button = self.key_buttons.get(TV_ACTION_LANG)
        if tv_lang_button is not None:
            tv_lang_button.set_label(short_label)

    def cycle_keyboard_layout(self):
        if self.sync_system_layout and self.system_layout_controller is not None:
            try:
                self.system_layout_controller.refresh()
            except (GLib.Error, OSError, RuntimeError):
                pass

        items = self.get_fast_switch_items()
        if len(items) >= 2:
            current_system_index = None
            if self.sync_system_layout and self.system_layout_controller is not None:
                try:
                    current_system_index = (
                        self.system_layout_controller.get_current_index()
                    )
                except (GLib.Error, OSError, RuntimeError):
                    current_system_index = None

            current_pos = None
            matching_positions = [
                idx
                for idx, (_sc, _dn, layout_id, _entry) in enumerate(items)
                if layout_id == self.keyboard_layout
            ]
            if len(matching_positions) == 1:
                current_pos = matching_positions[0]
            elif len(matching_positions) > 1:
                for idx in matching_positions:
                    entry = items[idx][3]
                    if (
                        entry is not None
                        and current_system_index is not None
                        and entry.index == current_system_index
                    ):
                        current_pos = idx
                        break
                if current_pos is None:
                    current_pos = matching_positions[0]

            next_pos = 0 if current_pos is None else (current_pos + 1) % len(items)
            _sc, _dn, next_layout_id, next_entry = items[next_pos]
            self.activate_fast_switch_item(next_layout_id, next_entry)
            return

        available = [layout_key for layout_key, _label in self.keyboard_layout_choices]
        next_layout = get_next_layout_id(self.keyboard_layout, available)
        if next_layout is not None:
            self.set_keyboard_layout(next_layout, sync_system=self.sync_system_layout)

    def select_system_layout_entry(self, entry):
        if self.system_layout_controller is None:
            return
        try:
            switched = self.system_layout_controller.set_layout_by_index(entry.index)
        except (GLib.Error, OSError, RuntimeError) as exc:
            print(f"Warning: Could not switch system keyboard layout ({exc}).")
            switched = False

        layout_id = resolve_system_entry_to_vboard_layout(entry, self.keyboard_layouts)
        if layout_id in self.keyboard_layouts:
            self.set_keyboard_layout(layout_id, sync_system=not switched, save=True)

    def on_layout_button_press_event(self, widget, event):
        if event.button == 1:
            self.cycle_keyboard_layout()
            return True
        if event.button == 3:
            self.popup_layout_menu(widget, event)
            return True
        return False

    def popup_layout_menu(self, widget, event=None):
        menu = Gtk.Menu()
        shown_layout_ids = set()

        system_entries = ()
        current_system_index = None
        if self.system_layout_controller is not None:
            try:
                self.system_layout_controller.refresh()
                system_entries = self.system_layout_controller.get_system_entries()
                current_system_index = self.system_layout_controller.get_current_index()
            except (GLib.Error, OSError, RuntimeError):
                system_entries = ()

        if system_entries:
            first_radio = None
            for entry in system_entries:
                resolved_id = resolve_system_entry_to_vboard_layout(
                    entry, self.keyboard_layouts
                )
                if resolved_id is not None:
                    shown_layout_ids.add(resolved_id)
                short_code = (
                    get_layout_short_label(resolved_id, self.keyboard_layouts)
                    if resolved_id
                    else entry.xkb_layout[:3].upper()
                )
                label_text = f"{short_code} - {entry.display_name}"
                if first_radio is None:
                    item = Gtk.RadioMenuItem.new_with_label(None, label_text)
                    first_radio = item
                else:
                    item = Gtk.RadioMenuItem.new_with_label_from_widget(
                        first_radio, label_text
                    )
                is_active = (
                    entry.index == current_system_index
                    if current_system_index is not None
                    else (resolved_id == self.keyboard_layout)
                )
                item.set_active(is_active)
                item.connect(
                    "activate",
                    lambda menu_item, selected=entry: (
                        self.select_system_layout_entry(selected)
                        if menu_item.get_active()
                        else None
                    ),
                )
                menu.append(item)

        extra_choices = [
            (layout_key, layout_label)
            for layout_key, layout_label in self.keyboard_layout_choices
            if layout_key not in shown_layout_ids
        ]
        if extra_choices:
            if system_entries:
                menu.append(Gtk.SeparatorMenuItem())
            for layout_key, layout_label in extra_choices:
                short_code = get_layout_short_label(layout_key, self.keyboard_layouts)
                item = Gtk.CheckMenuItem(label=f"{short_code} - {layout_label}")
                item.set_active(layout_key == self.keyboard_layout)
                item.connect(
                    "activate",
                    lambda _menu_item, key=layout_key: self.set_keyboard_layout(key),
                )
                menu.append(item)

        menu.show_all()
        menu.popup_at_widget(
            widget,
            Gdk.Gravity.SOUTH_WEST,
            Gdk.Gravity.NORTH_WEST,
            event,
        )

    def sync_caps_lock_from_system(self, keymap=None, connect=False):
        try:
            if keymap is None:
                display = self.get_display() or Gdk.Display.get_default()
                if display is None:
                    return
                keymap = Gdk.Keymap.get_for_display(display)
            if keymap is None or not hasattr(keymap, "get_caps_lock_state"):
                return
            self.set_caps_lock_active(
                bool(keymap.get_caps_lock_state()),
                update_system=False,
            )
            if connect:
                keymap.connect("state-changed", self.sync_caps_lock_from_system)
        except (AttributeError, TypeError, RuntimeError):
            return

    def refresh_layout_character_lookup(self):
        lookup = {}
        key_labels = self.get_active_key_labels()
        shifted_map = self.get_active_shifted_map()
        altgr_map = self.get_active_altgr_map()
        altgr_shifted_map = self.get_active_altgr_shifted_map()

        for row in self.get_active_key_rows():
            for key_event in row:
                if key_event in MODIFIER_KEYS:
                    continue

                key_label = key_labels.get(key_event, key_event)
                if len(key_label) == 1:
                    if key_label.isalpha():
                        lookup[key_label.lower()] = (key_event, False, False)
                        lookup[key_label.upper()] = (key_event, True, False)
                    else:
                        lookup[key_label] = (key_event, False, False)

                shifted_label = shifted_map.get(key_event)
                if shifted_label is not None:
                    lookup[shifted_label] = (key_event, True, False)

                altgr_label = altgr_map.get(key_event)
                if altgr_label is not None and len(altgr_label) == 1:
                    if altgr_label.isalpha():
                        lookup.setdefault(
                            altgr_label.lower(), (key_event, False, True)
                        )
                        lookup.setdefault(
                            altgr_label.upper(), (key_event, True, True)
                        )
                    else:
                        lookup.setdefault(altgr_label, (key_event, False, True))

                altgr_shifted_label = altgr_shifted_map.get(key_event)
                if altgr_shifted_label is not None and len(altgr_shifted_label) == 1:
                    lookup.setdefault(altgr_shifted_label, (key_event, True, True))

        self.layout_character_lookup = lookup

    def populate_keyboard_grid(self):
        self.key_buttons = {}
        self.modifier_buttons = {}

        if self.keyboard_mode == KEYBOARD_MODE_COMPACT_TV:
            if self.compact_tv_layer == COMPACT_TV_LAYER_NUMBERS:
                cells = build_compact_tv_numbers_cells()
            else:
                cells = build_compact_tv_alpha_cells(self.get_layout_config())
            for key_event, col, row_index, width, height in cells:
                self.attach_grid_cell(
                    self.grid, key_event, col, row_index, width, height
                )
            self.update_compact_tv_layer_styles()
        else:
            for row_index, keys in enumerate(self.get_active_key_rows()):
                self.create_row(self.grid, row_index, keys)

        self.apply_modifier_styles()

    def rebuild_keyboard_grid(self):
        for child in self.grid.get_children():
            self.grid.remove(child)

        self.populate_keyboard_grid()
        self.grid.show_all()
        self.update_layout_button()
        self.update_suggestion_bar_scale()

    def set_keyboard_mode(self, mode, save=True):
        normalized_mode = self.normalize_keyboard_mode(mode)
        if normalized_mode == self.keyboard_mode:
            return

        self.keyboard_mode = normalized_mode
        self.compact_tv_layer = COMPACT_TV_LAYER_ALPHA
        self.rebuild_keyboard_grid()
        if self.gesture_controller is not None:
            self.gesture_controller.refresh_layout_cache()
            self.gesture_controller.queue_overlay_draw()
        self.sync_tray_items()
        self.sync_settings_dialog_controls()
        if save:
            self.save_settings()

    def set_compact_tv_layer(self, layer):
        if layer not in (COMPACT_TV_LAYER_ALPHA, COMPACT_TV_LAYER_NUMBERS):
            return
        if layer == self.compact_tv_layer:
            return

        self.compact_tv_layer = layer
        self.rebuild_keyboard_grid()
        if self.gesture_controller is not None:
            self.gesture_controller.refresh_layout_cache()
            self.gesture_controller.queue_overlay_draw()

    def update_compact_tv_layer_styles(self):
        alpha_btn = self.key_buttons.get(TV_ACTION_LAYER_ALPHA)
        numbers_btn = self.key_buttons.get(TV_ACTION_LAYER_NUMBERS)
        if alpha_btn is not None:
            ctx = alpha_btn.get_style_context()
            if self.compact_tv_layer == COMPACT_TV_LAYER_ALPHA:
                ctx.add_class("active-layer")
            else:
                ctx.remove_class("active-layer")
        if numbers_btn is not None:
            ctx = numbers_btn.get_style_context()
            if self.compact_tv_layer == COMPACT_TV_LAYER_NUMBERS:
                ctx.add_class("active-layer")
            else:
                ctx.remove_class("active-layer")

    def apply_modifier_styles(self):
        for mod_key, active in self.modifiers.items():
            button = self.modifier_buttons.get(mod_key)
            if button is None:
                continue
            style_context = button.get_style_context()
            modifier_class = (
                "active-command-modifier"
                if mod_key.startswith(("Shift", "Ctrl", "Alt"))
                else "active-modifier"
            )
            style_context.remove_class("active-modifier")
            style_context.remove_class("active-command-modifier")
            style_context.remove_class("locked-modifier")
            if active:
                style_context.add_class(modifier_class)
                if self.locked_modifiers.get(mod_key, False):
                    style_context.add_class("locked-modifier")

        caps_button = self.key_buttons.get("CapsLock")
        if caps_button is not None:
            style_context = caps_button.get_style_context()
            style_context.remove_class("active-modifier")
            style_context.remove_class("active-command-modifier")
            if self.caps_lock_active:
                style_context.add_class("active-command-modifier")

        self.update_modifier_hints()

    def update_modifier_hints(self):
        altgr_active = bool(self.modifiers.get("Alt_R", False))
        show_hints = altgr_active and self.show_modifier_hints
        altgr_keys = (
            set(self.get_active_altgr_map()) | set(self.get_active_altgr_shifted_map())
            if show_hints
            else set()
        )
        for key_event, button in self.key_buttons.items():
            ctx = button.get_style_context()
            if key_event in altgr_keys:
                ctx.add_class("altgr-hint")
            else:
                ctx.remove_class("altgr-hint")

    def set_keyboard_layout(self, layout_key, sync_system=True, save=True):
        normalized_layout = self.normalize_keyboard_layout(layout_key)
        if (
            sync_system
            and self.sync_system_layout
            and self.system_layout_controller is not None
        ):
            try:
                synced = self.system_layout_controller.set_vboard_layout(
                    normalized_layout
                )
            except (GLib.Error, OSError, RuntimeError) as exc:
                print(
                    f"Warning: Could not synchronize system keyboard layout ({exc})."
                )
                synced = False
            if not synced:
                print(
                    "Warning: Layout is not configured in system layouts; "
                    "switching Vboard without system layout synchronization: "
                    f"{normalized_layout}"
                )

        if normalized_layout == self.keyboard_layout:
            self.update_layout_button()
            self.sync_settings_dialog_controls()
            return

        self.keyboard_layout = normalized_layout
        self.suggestion_engine.set_layout(normalized_layout)
        self.refresh_layout_character_lookup()
        self.rebuild_keyboard_grid()
        if self.gesture_controller is not None:
            self.gesture_controller.refresh_layout_cache()
            self.gesture_controller.queue_overlay_draw()

        self.clear_suggestion_override(update=False)
        self.current_word = ""
        self.update_suggestions()
        if self.text_prediction_enabled:
            GLib.idle_add(self.preload_suggestions)
        self.update_layout_button()
        self.sync_tray_items()
        self.sync_settings_dialog_controls()

        if save:
            self.save_settings()

    @staticmethod
    def _hex_to_gdk_rgba(hex_color):
        r, g, b = parse_hex_rgb(hex_color, fallback=(255, 255, 255))
        rgba = Gdk.RGBA()
        rgba.red = r / 255.0
        rgba.green = g / 255.0
        rgba.blue = b / 255.0
        rgba.alpha = 1.0
        return rgba

    @staticmethod
    def _gdk_rgba_to_hex(rgba):
        return rgb_to_hex(
            (
                round(rgba.red * 255),
                round(rgba.green * 255),
                round(rgba.blue * 255),
            )
        )

    def get_active_theme_label(self):
        variant = normalize_style_variant(self.style_variant)
        if variant == "graphite_dark":
            return "Graphite Dark"
        if variant == "frost_light":
            return "Frost Light"
        if variant == "onboard":
            return "Onboard Droid"
        if variant == "high_contrast_tv":
            return "High Contrast TV"
        if variant == "enhanced":
            for label, color in COLOR_CHOICES:
                if (
                    isinstance(color, tuple)
                    and len(color) == 2
                    and color[0] == ENHANCED_BACKGROUND_PRESET
                    and color[1] == self.bg_color
                ):
                    return label
            return "Enhanced Charcoal"
        for label, color in COLOR_CHOICES:
            if color == self.bg_color:
                return label
        return "Classic Black"

    def sync_theme_comboboxes(self):
        active_label = self.get_active_theme_label()
        if active_label is None:
            return
        if self.color_combobox is not None:
            for index, (label, _color) in enumerate(COLOR_CHOICES, start=1):
                if label == active_label:
                    if self.color_combobox.get_active() != index:
                        self.color_combobox.set_active(index)
                    break
        if self.settings_theme_combo is not None:
            if self.settings_theme_combo.get_active_id() != active_label:
                self.settings_theme_combo.set_active_id(active_label)

    def refresh_preset_combobox(self):
        combo = self.settings_preset_combo
        if combo is None:
            return
        prev_sync = self._syncing_settings_dialog
        self._syncing_settings_dialog = True
        try:
            combo.remove_all()
            combo.append("", "— Select Saved Preset —")
            presets = self.preset_manager.list_presets()
            preset_names = [name for name, _settings in presets]
            for name in preset_names:
                combo.append(name, name)
            if self.active_preset_name in preset_names:
                combo.set_active_id(self.active_preset_name)
            else:
                combo.set_active_id("")
            if self.settings_preset_delete_btn is not None:
                self.settings_preset_delete_btn.set_sensitive(
                    bool(combo.get_active_id())
                )
        finally:
            self._syncing_settings_dialog = prev_sync

    def sync_settings_dialog_controls(self):
        if self.settings_dialog is None:
            return
        self._syncing_settings_dialog = True
        try:
            self.sync_theme_comboboxes()
            self.refresh_preset_combobox()
            if self.settings_accent_combo is not None:
                if not self.settings_accent_combo.set_active_id(self.accent_color):
                    self.settings_accent_combo.set_active_id("__custom__")
            if self.settings_accent_color_btn is not None:
                self.settings_accent_color_btn.set_rgba(
                    self._hex_to_gdk_rgba(self.accent_color)
                )
            if self.settings_custom_colors_check is not None:
                self.settings_custom_colors_check.set_active(self.use_custom_colors)
            for attr, hex_val in (
                ("settings_win_bg_btn", self.custom_window_bg),
                ("settings_key_bg_btn", self.custom_key_bg),
                ("settings_mod_bg_btn", self.custom_modifier_bg),
                ("settings_text_color_btn", self.custom_text_color),
                ("settings_key_border_color_btn", self.custom_key_border_color),
                ("settings_win_border_color_btn", self.window_border_color),
            ):
                btn = getattr(self, attr, None)
                if btn is not None:
                    btn.set_rgba(self._hex_to_gdk_rgba(hex_val))
            if self.settings_win_border_width_scale is not None:
                self.settings_win_border_width_scale.set_value(
                    self.window_border_width
                )
            if self.settings_key_border_width_scale is not None:
                self.settings_key_border_width_scale.set_value(self.key_border_width)
            if self.settings_font_weight_combo is not None:
                self.settings_font_weight_combo.set_active_id(str(self.font_weight))
            if self.settings_key_shadow_check is not None:
                self.settings_key_shadow_check.set_active(self.key_shadow_enabled)
            if self.settings_opacity_scale is not None:
                self.settings_opacity_scale.set_value(
                    round(self._parse_opacity(self.opacity) * 100)
                )
            if self.settings_font_scale is not None:
                self.settings_font_scale.set_value(round(self.font_scale * 100))
            if self.settings_radius_scale is not None:
                self.settings_radius_scale.set_value(self.key_corner_radius)
            if self.settings_spacing_scale is not None:
                self.settings_spacing_scale.set_value(self.key_spacing)
            if self.settings_sync_layout_check is not None:
                self.settings_sync_layout_check.set_active(self.sync_system_layout)
            if self.settings_layout_combo is not None:
                if not self.settings_layout_combo.set_active_id(self.keyboard_layout):
                    active_config = self.keyboard_layouts.get(self.keyboard_layout)
                    if active_config is not None:
                        self.settings_layout_combo.append(
                            self.keyboard_layout, active_config["label"]
                        )
                        self.settings_layout_combo.set_active_id(self.keyboard_layout)
            if self.settings_mode_combo is not None:
                self.settings_mode_combo.set_active_id(self.keyboard_mode)
            if self.settings_prediction_check is not None:
                self.settings_prediction_check.set_active(self.text_prediction_enabled)
            if self.settings_media_row_check is not None:
                self.settings_media_row_check.set_active(self.show_media_row)
            if self.settings_current_text_check is not None:
                self.settings_current_text_check.set_active(self.show_current_text_bar)
            if self.settings_fast_layout_check is not None:
                self.settings_fast_layout_check.set_active(self.show_fast_layout_bar)
            if self.settings_modifier_hints_check is not None:
                self.settings_modifier_hints_check.set_active(self.show_modifier_hints)
            if self.settings_trigger_combo is not None:
                self.settings_trigger_combo.set_active_id(self.input_trigger_mode)
            if self.settings_auto_cap_check is not None:
                self.settings_auto_cap_check.set_active(self.auto_capitalize)
            if self.settings_auto_space_check is not None:
                self.settings_auto_space_check.set_active(
                    self.auto_space_after_suggestion
                )
            if self.settings_sticky_lock_check is not None:
                self.settings_sticky_lock_check.set_active(self.sticky_modifier_lock)
            if self.settings_dwell_check is not None:
                self.settings_dwell_check.set_active(self.dwell_enabled)
            if self.settings_dwell_scale is not None:
                self.settings_dwell_scale.set_value(self.dwell_time_ms)
                self.settings_dwell_scale.set_sensitive(self.dwell_enabled)
            if self.settings_fade_check is not None:
                self.settings_fade_check.set_active(self.fade_on_inactivity)
            if self.settings_fade_delay_spin is not None:
                self.settings_fade_delay_spin.set_value(self.inactivity_delay_seconds)
                self.settings_fade_delay_spin.set_sensitive(self.fade_on_inactivity)
            if self.settings_fade_opacity_scale is not None:
                self.settings_fade_opacity_scale.set_value(
                    round(self.inactivity_fade_opacity * 100)
                )
                self.settings_fade_opacity_scale.set_sensitive(self.fade_on_inactivity)
            if self.settings_start_minimized_check is not None:
                self.settings_start_minimized_check.set_active(self.start_minimized)
        finally:
            self._syncing_settings_dialog = False

    def sync_gesture_controls(self):
        if (
            self.settings_gesture_check is not None
            and self.settings_gesture_check.get_active() != self.gesture_enabled
        ):
            self._syncing_settings_dialog = True
            try:
                self.settings_gesture_check.set_active(self.gesture_enabled)
            finally:
                self._syncing_settings_dialog = False
        self.sync_tray_items()

    def sync_visual_feedback_controls(self):
        if self.settings_visual_feedback_check is not None:
            self.settings_visual_feedback_check.set_sensitive(self.gesture_enabled)
            if (
                self.settings_visual_feedback_check.get_active()
                != self.gesture_visual_feedback_enabled
            ):
                self._syncing_settings_dialog = True
                try:
                    self.settings_visual_feedback_check.set_active(
                        self.gesture_visual_feedback_enabled
                    )
                finally:
                    self._syncing_settings_dialog = False
        self.sync_tray_items()

    def set_gesture_visual_feedback_enabled(self, enabled, sync_controls=True):
        self.gesture_visual_feedback_enabled = bool(enabled)
        if self.gesture_controller is not None:
            self.gesture_controller.set_visual_feedback_enabled(
                self.gesture_visual_feedback_enabled
            )
        if sync_controls:
            self.sync_visual_feedback_controls()
        self.save_settings()

    def enable_gesture_typing(self, sync_controls=True, save=True):
        if self.gesture_controller is None:
            gesture_module = importlib.import_module(f"{__package__}.gesture")
            self.gesture_controller = gesture_module.GestureTypingController(
                self,
                self.grid_overlay,
            )
            self.gesture_controller.refresh_layout_cache()
            self.gesture_controller.queue_overlay_draw()
        self.gesture_controller.set_visual_feedback_enabled(
            self.gesture_visual_feedback_enabled
        )

        self.gesture_enabled = True
        if sync_controls:
            self.sync_gesture_controls()
            self.sync_visual_feedback_controls()
        if save:
            self.save_settings()

    def disable_gesture_typing(self, sync_controls=True, save=True):
        had_gesture_commit = (
            self.gesture_controller is not None and self.gesture_controller.has_committed_text()
        )

        if self.gesture_controller is not None:
            self.gesture_controller.destroy()
            self.gesture_controller = None

        self.gesture_enabled = False
        if had_gesture_commit:
            self.suggestion_override = None
            self.update_suggestions()

        sys.modules.pop(f"{__package__}.gesture", None)
        if sync_controls:
            self.sync_gesture_controls()
            self.sync_visual_feedback_controls()
        if save:
            self.save_settings()

    def on_tray_about(self, widget):
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_modal(True)
        about_dialog.set_program_name(APP_DISPLAY_NAME)
        about_dialog.set_version(VERSION)
        about_dialog.set_comments(
            "A lightweight, customizable virtual keyboard for GNU/Linux with Wayland support.\n\n"
            "Originally created by mdev588. The original project was archived, "
            "and it is now maintained by Archisman Panigrahi.\n\n"
            "Original project: https://github.com/mdev588/vboard\n"
            "Special thanks to honjow for the icon and patches.\n"
            "Thanks to Yavuz Kagan Yadigar for the enhanced theme inspiration.\n"
            "Thanks to onboard developers for the droid theme inspiration.\n"
            "Thanks to the Hunspell project for the suggestion engine.\n"
            "This project is licensed under GPLv3."
        )
        about_dialog.set_copyright(
            "Copyright © 2025 mdev588\n"
            "Copyright © 2026 Archisman Panigrahi"
        )
        about_dialog.set_website("https://github.com/archisman-panigrahi/vboard")
        about_dialog.set_website_label("Homepage")
        about_dialog.set_logo_icon_name(self.get_app_icon_name())
        about_dialog.run()
        about_dialog.destroy()

    def cleanup_on_destroy(self):
        if getattr(self, "_cleaned_up", False):
            return
        self._cleaned_up = True
        self.stop_all_active_keys()
        self.cancel_inactivity_timer()
        if self._scale_timer_id is not None:
            GLib.source_remove(self._scale_timer_id)
            self._scale_timer_id = None
        if self._watchdog_source is not None:
            GLib.source_remove(self._watchdog_source)
            self._watchdog_source = None
        if self._keep_above_timer_id is not None:
            GLib.source_remove(self._keep_above_timer_id)
            self._keep_above_timer_id = None
        if self.gesture_controller is not None:
            self.gesture_controller.destroy()
            self.gesture_controller = None
        if getattr(self, "backend", None) is not None:
            self.backend.destroy()
        self.close_system_layout_sync()
        self.save_settings()
        self.clear_tray_icon()

    def on_tray_quit(self, widget):
        self.exiting = True
        self.cleanup_on_destroy()
        self.destroy()

    def on_report_bugs(self, widget=None):
        self.open_bug_report_url()

    def open_bug_report_url(self):
        try:
            Gio.AppInfo.launch_default_for_uri(BUG_REPORT_URL, None)
        except GLib.Error as exc:
            print(f"Warning: Could not open bug report URL ({exc}).")

    def on_delete_event(self, widget, event):
        if self.exiting:
            return False
        if self.tray_icon is None:
            self.cleanup_on_destroy()
            return False
        self.stop_all_active_keys()
        self.cancel_inactivity_timer()
        self.save_settings()
        self.hide()
        self.update_tray_menu()
        return True

    def create_settings(self):
        self.esc_button = Gtk.Button(label="ESC")
        self.esc_button.set_can_focus(False)
        self.esc_button.set_focus_on_click(False)
        self.esc_button.connect("clicked", lambda widget: self.emit_key("Esc"))
        self.esc_button.set_name("esc-button")
        self.header.pack_start(self.esc_button)

        self.layout_button_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=2,
        )
        self.layout_button_box.set_name("layout-button-box")
        self.header.pack_start(self.layout_button_box)
        self.rebuild_layout_buttons()

        self.menu_button = self.create_button(
            "", self.change_visibility, callbacks=1, hide_with_menu=False
        )
        self.menu_button.set_tooltip_text("Toggle quick background & opacity controls")
        set_button_vector_icon(
            self.menu_button, "menu", size_px=15, color=self.get_active_icon_color()
        )
        self.create_button(
            "Options",
            self.open_settings_dialog,
            callbacks=1,
            hide_with_menu=False,
        )
        self.create_button("+", self.change_opacity, True, 2)
        self.create_button("-", self.change_opacity, False, 2)
        self.create_button(f"{self.opacity}")
        self.color_combobox.append_text("Theme")
        self.color_combobox.connect("changed", self.change_color)
        self.color_combobox.set_name("combobox")
        self.header.pack_end(self.color_combobox)

        for label, _color in COLOR_CHOICES:
            self.color_combobox.append_text(label)

        active_label = self.get_active_theme_label()
        active_index = 0
        if active_label is not None:
            for index, (label, _color) in enumerate(COLOR_CHOICES, start=1):
                if label == active_label:
                    active_index = index
                    break

        self.color_combobox.set_active(active_index)

    def _sync_custom_color_defaults_from_theme(self):
        base = get_base_theme_colors(self.style_variant, self.bg_color, self.text_color)
        self.custom_window_bg = base["window_bg"]
        self.custom_key_bg = base["key_bg"]
        self.custom_modifier_bg = base["modifier_bg"]
        self.custom_text_color = base["text_color"]
        self.custom_key_border_color = base["key_border_color"]
        self.window_border_color = base["window_border_color"]

    def set_theme_by_label(self, selected_label, save=True):
        selected_color = self.color_map.get(selected_label)
        if selected_color is None:
            return
        if selected_color == GRAPHITE_DARK_BACKGROUND_PRESET:
            self.style_variant = "graphite_dark"
            self.text_color = "#F5F5F7"
        elif selected_color == FROST_LIGHT_BACKGROUND_PRESET:
            self.style_variant = "frost_light"
            self.text_color = "#1D1D1F"
        elif selected_color == ONBOARD_BACKGROUND_PRESET:
            self.style_variant = "onboard"
            self.text_color = "#F2F5FA"
        elif selected_color == HIGH_CONTRAST_TV_BACKGROUND_PRESET:
            self.style_variant = "high_contrast_tv"
            self.text_color = "#FFFFFF"
        elif (
            isinstance(selected_color, tuple)
            and len(selected_color) == 2
            and selected_color[0] == ENHANCED_BACKGROUND_PRESET
        ):
            self.style_variant = "enhanced"
            self.bg_color = selected_color[1]
            self.text_color = (
                "#1C1C1C" if self.bg_color in LIGHT_BACKGROUND_COLORS else "#F5F5F7"
            )
        else:
            self.style_variant = "classic"
            self.bg_color = selected_color
            self.text_color = (
                "#1C1C1C" if self.bg_color in LIGHT_BACKGROUND_COLORS else "#F5F5F7"
            )
        self.use_custom_colors = False
        self._sync_custom_color_defaults_from_theme()
        self.apply_css()
        self.sync_settings_dialog_controls()
        if save:
            self.save_settings()

    def get_preset_snapshot(self):
        return {
            "style_variant": self.style_variant,
            "bg_color": self.bg_color,
            "text_color": self.text_color,
            "opacity": self.opacity,
            "accent_color": self.accent_color,
            "font_scale": self.font_scale,
            "font_weight": self.font_weight,
            "key_corner_radius": self.key_corner_radius,
            "key_spacing": self.key_spacing,
            "key_border_width": self.key_border_width,
            "window_border_width": self.window_border_width,
            "window_border_color": self.window_border_color,
            "key_shadow_enabled": self.key_shadow_enabled,
            "use_custom_colors": self.use_custom_colors,
            "custom_window_bg": self.custom_window_bg,
            "custom_key_bg": self.custom_key_bg,
            "custom_modifier_bg": self.custom_modifier_bg,
            "custom_text_color": self.custom_text_color,
            "custom_key_border_color": self.custom_key_border_color,
            "keyboard_mode": self.keyboard_mode,
            "show_media_row": self.show_media_row,
            "show_current_text_bar": self.show_current_text_bar,
            "show_fast_layout_bar": self.show_fast_layout_bar,
            "show_modifier_hints": self.show_modifier_hints,
            "text_prediction_enabled": self.text_prediction_enabled,
        }

    def apply_preset_dict(self, preset_dict, save=True):
        if not isinstance(preset_dict, dict):
            return
        if "style_variant" in preset_dict:
            self.style_variant = normalize_style_variant(preset_dict["style_variant"])
        if "bg_color" in preset_dict:
            self.bg_color = str(preset_dict["bg_color"]).replace(" ", "")
        if "text_color" in preset_dict:
            self.text_color = str(preset_dict["text_color"])
        if "opacity" in preset_dict:
            self.opacity = f"{self._parse_opacity(preset_dict['opacity']):.2f}"
        if "accent_color" in preset_dict and str(preset_dict["accent_color"]).startswith("#"):
            self.accent_color = str(preset_dict["accent_color"])
        if "font_scale" in preset_dict:
            try:
                self.font_scale = max(0.75, min(1.60, round(float(preset_dict["font_scale"]), 2)))
            except (TypeError, ValueError):
                pass
        if "font_weight" in preset_dict and str(preset_dict["font_weight"]) in ("400", "500", "600", "700"):
            self.font_weight = str(preset_dict["font_weight"])
        if "key_corner_radius" in preset_dict:
            try:
                self.key_corner_radius = max(0, min(16, int(round(float(preset_dict["key_corner_radius"])))))
            except (TypeError, ValueError):
                pass
        if "key_spacing" in preset_dict:
            try:
                self.key_spacing = max(1, min(8, int(round(float(preset_dict["key_spacing"])))))
            except (TypeError, ValueError):
                pass
        if "key_border_width" in preset_dict:
            try:
                self.key_border_width = max(0, min(3, int(round(float(preset_dict["key_border_width"])))))
            except (TypeError, ValueError):
                pass
        if "window_border_width" in preset_dict:
            try:
                self.window_border_width = max(0, min(4, int(round(float(preset_dict["window_border_width"])))))
            except (TypeError, ValueError):
                pass
        for color_attr in (
            "window_border_color",
            "custom_window_bg",
            "custom_key_bg",
            "custom_modifier_bg",
            "custom_text_color",
            "custom_key_border_color",
        ):
            val = preset_dict.get(color_attr)
            if isinstance(val, str) and val.startswith("#"):
                setattr(self, color_attr, val.upper())
        if "key_shadow_enabled" in preset_dict:
            self.key_shadow_enabled = bool(preset_dict["key_shadow_enabled"])
        if "use_custom_colors" in preset_dict:
            self.use_custom_colors = bool(preset_dict["use_custom_colors"])
        if "show_media_row" in preset_dict:
            self.show_media_row = bool(preset_dict["show_media_row"])
            self.update_media_bar_visibility()
        if "show_current_text_bar" in preset_dict:
            self.show_current_text_bar = bool(preset_dict["show_current_text_bar"])
            self.update_current_text_bar_visibility()
        if "show_fast_layout_bar" in preset_dict:
            self.show_fast_layout_bar = bool(preset_dict["show_fast_layout_bar"])
            self.update_fast_layout_bar_visibility()
        if "show_modifier_hints" in preset_dict:
            self.show_modifier_hints = bool(preset_dict["show_modifier_hints"])
            self.update_modifier_hints()
        if "text_prediction_enabled" in preset_dict:
            self.text_prediction_enabled = bool(preset_dict["text_prediction_enabled"])
            self.update_suggestion_bar_visibility()
        if "keyboard_mode" in preset_dict:
            target_mode = self.normalize_keyboard_mode(preset_dict["keyboard_mode"])
            if target_mode != self.keyboard_mode:
                self.set_keyboard_mode(target_mode, save=False)

        if hasattr(self, "opacity_btn") and self.opacity_btn is not None:
            self.opacity_btn.set_label(self.opacity)
        self._last_suggestion_scale = None
        self.update_suggestion_bar_scale()
        self.apply_css()
        self.sync_settings_dialog_controls()
        self.sync_tray_items()
        if save:
            self.save_settings()

    def save_user_preset(self, name):
        cleaned = (name or "").strip()
        if not cleaned:
            return None
        path = self.preset_manager.save_preset(cleaned, self.get_preset_snapshot())
        self.active_preset_name = cleaned
        self.refresh_preset_combobox()
        self.save_settings()
        return path

    def load_user_preset(self, name, save=True):
        settings = self.preset_manager.load_preset(name)
        if settings is None:
            return False
        self.active_preset_name = name
        self.apply_preset_dict(settings, save=save)
        return True

    def delete_user_preset(self, name):
        if not name:
            return False
        deleted = self.preset_manager.delete_preset(name)
        if deleted and self.active_preset_name == name:
            self.active_preset_name = ""
        self.refresh_preset_combobox()
        self.save_settings()
        return deleted

    def set_font_scale(self, scale, save=True):
        clamped = max(0.75, min(1.60, round(float(scale), 2)))
        if clamped == self.font_scale:
            return
        self.font_scale = clamped
        self._last_suggestion_scale = None
        self.update_suggestion_bar_scale()
        self.apply_css()
        if save:
            self.save_settings()

    def set_font_weight(self, weight, save=True):
        weight_str = str(weight)
        if weight_str not in ("400", "500", "600", "700"):
            return
        if weight_str == self.font_weight:
            return
        self.font_weight = weight_str
        self.apply_css()
        if save:
            self.save_settings()

    def set_key_corner_radius(self, radius, save=True):
        clamped = max(0, min(16, int(round(radius))))
        if clamped == self.key_corner_radius:
            return
        self.key_corner_radius = clamped
        self.apply_css()
        if save:
            self.save_settings()

    def set_key_spacing(self, spacing, save=True):
        clamped = max(1, min(8, int(round(spacing))))
        if clamped == self.key_spacing:
            return
        self.key_spacing = clamped
        self.apply_css()
        if save:
            self.save_settings()

    def set_key_border_width(self, width, save=True):
        clamped = max(0, min(3, int(round(width))))
        if clamped == self.key_border_width:
            return
        self.key_border_width = clamped
        self.apply_css()
        if save:
            self.save_settings()

    def set_window_border_width(self, width, save=True):
        clamped = max(0, min(4, int(round(width))))
        if clamped == self.window_border_width:
            return
        self.window_border_width = clamped
        self.apply_css()
        if save:
            self.save_settings()

    def set_window_border_color(self, hex_color, save=True):
        if not isinstance(hex_color, str) or not hex_color.startswith("#"):
            return
        normalized = hex_color.upper()
        if normalized == self.window_border_color:
            return
        self.window_border_color = normalized
        self.apply_css()
        if save:
            self.save_settings()

    def set_key_shadow_enabled(self, enabled, save=True):
        enabled = bool(enabled)
        if enabled == self.key_shadow_enabled:
            return
        self.key_shadow_enabled = enabled
        self.apply_css()
        if save:
            self.save_settings()

    def set_use_custom_colors(self, enabled, save=True):
        enabled = bool(enabled)
        if enabled == self.use_custom_colors:
            return
        self.use_custom_colors = enabled
        self.apply_css()
        self.sync_settings_dialog_controls()
        if save:
            self.save_settings()

    def set_custom_color(self, attr_name, hex_color, save=True):
        allowed = {
            "custom_window_bg",
            "custom_key_bg",
            "custom_modifier_bg",
            "custom_text_color",
            "custom_key_border_color",
        }
        if attr_name not in allowed or not isinstance(hex_color, str) or not hex_color.startswith("#"):
            return
        normalized = hex_color.upper()
        setattr(self, attr_name, normalized)
        self.use_custom_colors = True
        self.apply_css()
        self.sync_settings_dialog_controls()
        if save:
            self.save_settings()

    def set_accent_color(self, accent_hex, save=True):
        if not isinstance(accent_hex, str) or not accent_hex.startswith("#"):
            return
        normalized = accent_hex.upper()
        if normalized == self.accent_color:
            return
        self.accent_color = normalized
        self.apply_css()
        self.sync_settings_dialog_controls()
        if save:
            self.save_settings()

    def set_show_media_row(self, enabled, save=True):
        enabled = bool(enabled)
        if enabled == self.show_media_row:
            return
        self.show_media_row = enabled
        self.update_media_bar_visibility()
        self._last_suggestion_scale = None
        self.update_suggestion_bar_scale()
        if save:
            self.save_settings()

    def set_show_current_text_bar(self, enabled, save=True):
        enabled = bool(enabled)
        if enabled == self.show_current_text_bar:
            return
        self.show_current_text_bar = enabled
        self.update_current_text_bar_visibility()
        self._last_suggestion_scale = None
        self.update_suggestion_bar_scale()
        if save:
            self.save_settings()

    def set_show_fast_layout_bar(self, enabled, save=True):
        enabled = bool(enabled)
        if enabled == self.show_fast_layout_bar:
            return
        self.show_fast_layout_bar = enabled
        self.update_fast_layout_bar_visibility()
        if save:
            self.save_settings()

    def set_show_modifier_hints(self, enabled, save=True):
        enabled = bool(enabled)
        if enabled == self.show_modifier_hints:
            return
        self.show_modifier_hints = enabled
        self.update_modifier_hints()
        if save:
            self.save_settings()

    def set_input_trigger_mode(self, mode, save=True):
        if mode not in (INPUT_TRIGGER_PRESS, INPUT_TRIGGER_RELEASE):
            return
        if mode == self.input_trigger_mode:
            return
        self.input_trigger_mode = mode
        self._pending_release_key = None
        if save:
            self.save_settings()

    def set_auto_capitalize(self, enabled, save=True):
        enabled = bool(enabled)
        if enabled == self.auto_capitalize:
            return
        self.auto_capitalize = enabled
        if save:
            self.save_settings()

    def set_auto_space_after_suggestion(self, enabled, save=True):
        enabled = bool(enabled)
        if enabled == self.auto_space_after_suggestion:
            return
        self.auto_space_after_suggestion = enabled
        if save:
            self.save_settings()

    def set_sticky_modifier_lock(self, enabled, save=True):
        enabled = bool(enabled)
        if enabled == self.sticky_modifier_lock:
            return
        self.sticky_modifier_lock = enabled
        if not enabled:
            for mod_key in self.locked_modifiers:
                self.locked_modifiers[mod_key] = False
            self.apply_modifier_styles()
        if save:
            self.save_settings()

    def set_dwell_enabled(self, enabled, save=True):
        enabled = bool(enabled)
        if enabled == self.dwell_enabled:
            return
        self.dwell_enabled = enabled
        if not enabled:
            self.cancel_dwell_timer()
        if self.settings_dwell_scale is not None:
            self.settings_dwell_scale.set_sensitive(enabled)
        if save:
            self.save_settings()

    def set_dwell_time_ms(self, dwell_ms, save=True):
        clamped = max(300, min(2500, int(round(dwell_ms))))
        if clamped == self.dwell_time_ms:
            return
        self.dwell_time_ms = clamped
        if save:
            self.save_settings()

    def set_fade_on_inactivity(self, enabled, save=True):
        enabled = bool(enabled)
        if enabled == self.fade_on_inactivity:
            return
        self.fade_on_inactivity = enabled
        self.reset_inactivity_timer()
        if self.settings_fade_delay_spin is not None:
            self.settings_fade_delay_spin.set_sensitive(enabled)
        if self.settings_fade_opacity_scale is not None:
            self.settings_fade_opacity_scale.set_sensitive(enabled)
        if save:
            self.save_settings()

    def set_inactivity_delay_seconds(self, seconds, save=True):
        clamped = max(3, min(120, int(round(seconds))))
        if clamped == self.inactivity_delay_seconds:
            return
        self.inactivity_delay_seconds = clamped
        self.reset_inactivity_timer()
        if save:
            self.save_settings()

    def set_inactivity_fade_opacity(self, fade_opacity, save=True):
        clamped = max(0.10, min(0.85, round(float(fade_opacity), 2)))
        if clamped == self.inactivity_fade_opacity:
            return
        self.inactivity_fade_opacity = clamped
        if self._is_faded:
            self.set_faded_state(False)
            self.set_faded_state(True)
        if save:
            self.save_settings()

    def reset_appearance_defaults(self, _widget=None):
        self.style_variant = "graphite_dark"
        self.accent_color = DEFAULT_ACCENT_COLOR
        self.opacity = "0.92"
        self.font_scale = DEFAULT_FONT_SCALE
        self.font_weight = DEFAULT_FONT_WEIGHT
        self.key_corner_radius = DEFAULT_KEY_RADIUS
        self.key_spacing = DEFAULT_KEY_SPACING
        self.key_border_width = DEFAULT_KEY_BORDER_WIDTH
        self.window_border_width = DEFAULT_WINDOW_BORDER_WIDTH
        self.key_shadow_enabled = DEFAULT_KEY_SHADOW_ENABLED
        self.use_custom_colors = False
        self.active_preset_name = ""
        self._sync_custom_color_defaults_from_theme()
        if hasattr(self, "opacity_btn") and self.opacity_btn is not None:
            self.opacity_btn.set_label(self.opacity)
        self._last_suggestion_scale = None
        self.update_suggestion_bar_scale()
        self.apply_css()
        self.sync_settings_dialog_controls()
        self.save_settings()

    def open_settings_dialog(self, widget=None):
        if self.settings_dialog is not None:
            self.settings_dialog.present()
            return

        dialog = Gtk.Dialog(
            title="Customize Vboard",
            transient_for=self,
            modal=True,
        )
        dialog.set_default_size(540, 520)
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        dialog.connect("response", self.on_settings_dialog_response)
        dialog.connect("destroy", self.on_settings_dialog_destroy)

        content = dialog.get_content_area()
        content.set_border_width(10)
        content.set_spacing(10)

        notebook = Gtk.Notebook()
        content.pack_start(notebook, True, True, 0)

        # --- Tab 1: Appearance & Presets ---
        appearance_scroll = Gtk.ScrolledWindow()
        appearance_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        appearance_scroll.set_min_content_height(380)

        appearance_grid = Gtk.Grid(column_spacing=10, row_spacing=8)
        appearance_grid.set_border_width(12)
        appearance_scroll.add(appearance_grid)

        row = 0

        # Presets manager bar
        preset_label = Gtk.Label(label="My Presets", xalign=0)
        preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        preset_combo = Gtk.ComboBoxText()
        preset_combo.set_hexpand(True)
        preset_combo.connect("changed", self.on_settings_preset_changed)
        save_preset_btn = Gtk.Button(label="Save…")
        save_preset_btn.set_tooltip_text("Save current appearance & toolbar settings as a preset")
        save_preset_btn.connect("clicked", self.on_settings_save_preset_clicked)
        delete_preset_btn = Gtk.Button(label="Delete")
        delete_preset_btn.set_tooltip_text("Delete selected user preset")
        delete_preset_btn.connect("clicked", self.on_settings_delete_preset_clicked)
        preset_box.pack_start(preset_combo, True, True, 0)
        preset_box.pack_start(save_preset_btn, False, False, 0)
        preset_box.pack_start(delete_preset_btn, False, False, 0)
        appearance_grid.attach(preset_label, 0, row, 1, 1)
        appearance_grid.attach(preset_box, 1, row, 2, 1)
        self.settings_preset_combo = preset_combo
        self.settings_preset_delete_btn = delete_preset_btn
        self.refresh_preset_combobox()
        row += 1

        appearance_grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 3, 1)
        row += 1

        theme_label = Gtk.Label(label="Theme Base", xalign=0)
        theme_combo = Gtk.ComboBoxText()
        for label, _color in COLOR_CHOICES:
            theme_combo.append(label, label)
        active_theme_label = self.get_active_theme_label()
        if active_theme_label:
            theme_combo.set_active_id(active_theme_label)
        theme_combo.connect("changed", self.on_settings_theme_changed)
        appearance_grid.attach(theme_label, 0, row, 1, 1)
        appearance_grid.attach(theme_combo, 1, row, 2, 1)
        self.settings_theme_combo = theme_combo
        row += 1

        accent_label = Gtk.Label(label="Accent Color", xalign=0)
        accent_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        accent_combo = Gtk.ComboBoxText()
        accent_combo.set_hexpand(True)
        for accent_name, accent_hex in ACCENT_COLOR_CHOICES:
            accent_combo.append(accent_hex, accent_name)
        accent_combo.append("__custom__", "Custom")
        if not accent_combo.set_active_id(self.accent_color):
            accent_combo.set_active_id("__custom__")
        accent_combo.connect("changed", self.on_settings_accent_changed)
        accent_color_btn = Gtk.ColorButton.new_with_rgba(
            self._hex_to_gdk_rgba(self.accent_color)
        )
        accent_color_btn.set_title("Choose Accent Color")
        accent_color_btn.connect("color-set", self.on_settings_accent_color_btn_set)
        accent_box.pack_start(accent_combo, True, True, 0)
        accent_box.pack_start(accent_color_btn, False, False, 0)
        appearance_grid.attach(accent_label, 0, row, 1, 1)
        appearance_grid.attach(accent_box, 1, row, 2, 1)
        self.settings_accent_combo = accent_combo
        self.settings_accent_color_btn = accent_color_btn
        row += 1

        custom_colors_check = Gtk.CheckButton(
            label="Customize Individual Colors (Background, Keys, Modifiers, Text & Icons)"
        )
        custom_colors_check.set_active(self.use_custom_colors)
        custom_colors_check.connect("toggled", self.on_settings_custom_colors_toggled)
        appearance_grid.attach(custom_colors_check, 0, row, 3, 1)
        self.settings_custom_colors_check = custom_colors_check
        row += 1

        colors_grid = Gtk.Grid(column_spacing=12, row_spacing=6)
        color_specs = (
            ("Window BG", "custom_window_bg", "settings_win_bg_btn", 0, 0),
            ("Key BG", "custom_key_bg", "settings_key_bg_btn", 2, 0),
            ("Modifier BG", "custom_modifier_bg", "settings_mod_bg_btn", 0, 1),
            ("Text & Icons", "custom_text_color", "settings_text_color_btn", 2, 1),
            ("Key Border", "custom_key_border_color", "settings_key_border_color_btn", 0, 2),
            ("Window Outline", "window_border_color", "settings_win_border_color_btn", 2, 2),
        )
        for title, attr_name, widget_attr, col_idx, row_idx in color_specs:
            lbl = Gtk.Label(label=title, xalign=0)
            cbtn = Gtk.ColorButton.new_with_rgba(
                self._hex_to_gdk_rgba(getattr(self, attr_name))
            )
            cbtn.set_title(f"Choose {title} Color")
            cbtn.set_hexpand(True)
            if attr_name == "window_border_color":
                cbtn.connect("color-set", self.on_settings_win_border_color_set)
            else:
                cbtn.connect("color-set", self.on_settings_custom_color_set, attr_name)
            colors_grid.attach(lbl, col_idx, row_idx, 1, 1)
            colors_grid.attach(cbtn, col_idx + 1, row_idx, 1, 1)
            setattr(self, widget_attr, cbtn)
        appearance_grid.attach(colors_grid, 0, row, 3, 1)
        row += 1

        appearance_grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 3, 1)
        row += 1

        win_border_label = Gtk.Label(label="Window Outline Width (px)", xalign=0)
        win_border_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 4, 1)
        win_border_scale.set_digits(0)
        win_border_scale.set_hexpand(True)
        win_border_scale.set_value(self.window_border_width)
        win_border_scale.connect("value-changed", self.on_settings_win_border_width_changed)
        appearance_grid.attach(win_border_label, 0, row, 1, 1)
        appearance_grid.attach(win_border_scale, 1, row, 2, 1)
        self.settings_win_border_width_scale = win_border_scale
        row += 1

        key_border_label = Gtk.Label(label="Key Border Width (px)", xalign=0)
        key_border_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 3, 1)
        key_border_scale.set_digits(0)
        key_border_scale.set_hexpand(True)
        key_border_scale.set_value(self.key_border_width)
        key_border_scale.connect("value-changed", self.on_settings_key_border_width_changed)
        appearance_grid.attach(key_border_label, 0, row, 1, 1)
        appearance_grid.attach(key_border_scale, 1, row, 2, 1)
        self.settings_key_border_width_scale = key_border_scale
        row += 1

        opacity_label = Gtk.Label(label="Opacity (%)", xalign=0)
        opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 30, 100, 1)
        opacity_scale.set_digits(0)
        opacity_scale.set_hexpand(True)
        opacity_scale.set_value(round(self._parse_opacity(self.opacity) * 100))
        opacity_scale.connect("value-changed", self.on_settings_opacity_changed)
        appearance_grid.attach(opacity_label, 0, row, 1, 1)
        appearance_grid.attach(opacity_scale, 1, row, 2, 1)
        self.settings_opacity_scale = opacity_scale
        row += 1

        font_label = Gtk.Label(label="Key Font Scale (%)", xalign=0)
        font_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 75, 160, 5)
        font_scale.set_digits(0)
        font_scale.set_hexpand(True)
        font_scale.set_value(round(self.font_scale * 100))
        font_scale.connect("value-changed", self.on_settings_font_scale_changed)
        appearance_grid.attach(font_label, 0, row, 1, 1)
        appearance_grid.attach(font_scale, 1, row, 2, 1)
        self.settings_font_scale = font_scale
        row += 1

        font_weight_label = Gtk.Label(label="Key Font Weight", xalign=0)
        font_weight_combo = Gtk.ComboBoxText()
        for weight_id, weight_name in FONT_WEIGHT_CHOICES:
            font_weight_combo.append(weight_id, weight_name)
        font_weight_combo.set_active_id(str(self.font_weight))
        font_weight_combo.connect("changed", self.on_settings_font_weight_changed)
        appearance_grid.attach(font_weight_label, 0, row, 1, 1)
        appearance_grid.attach(font_weight_combo, 1, row, 2, 1)
        self.settings_font_weight_combo = font_weight_combo
        row += 1

        radius_label = Gtk.Label(label="Key Corner Radius (px)", xalign=0)
        radius_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 16, 1)
        radius_scale.set_digits(0)
        radius_scale.set_hexpand(True)
        radius_scale.set_value(self.key_corner_radius)
        radius_scale.connect("value-changed", self.on_settings_radius_changed)
        appearance_grid.attach(radius_label, 0, row, 1, 1)
        appearance_grid.attach(radius_scale, 1, row, 2, 1)
        self.settings_radius_scale = radius_scale
        row += 1

        spacing_label = Gtk.Label(label="Key Spacing (px)", xalign=0)
        spacing_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 8, 1)
        spacing_scale.set_digits(0)
        spacing_scale.set_hexpand(True)
        spacing_scale.set_value(self.key_spacing)
        spacing_scale.connect("value-changed", self.on_settings_spacing_changed)
        appearance_grid.attach(spacing_label, 0, row, 1, 1)
        appearance_grid.attach(spacing_scale, 1, row, 2, 1)
        self.settings_spacing_scale = spacing_scale
        row += 1

        shadow_check = Gtk.CheckButton(label="Keycap Depth Shadow")
        shadow_check.set_active(self.key_shadow_enabled)
        shadow_check.connect("toggled", self.on_settings_key_shadow_toggled)
        appearance_grid.attach(shadow_check, 0, row, 3, 1)
        self.settings_key_shadow_check = shadow_check
        row += 1

        reset_btn = Gtk.Button(label="Reset to Graphite Dark Defaults")
        reset_btn.connect("clicked", self.reset_appearance_defaults)
        appearance_grid.attach(reset_btn, 0, row, 3, 1)

        notebook.append_page(appearance_scroll, Gtk.Label(label="Appearance"))

        # --- Tab 2: Toolbars & Layout ---
        layout_grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        layout_grid.set_border_width(12)

        mode_label = Gtk.Label(label="Keyboard Style", xalign=0)
        mode_combo = Gtk.ComboBoxText()
        for mode_id, mode_name in KEYBOARD_MODE_CHOICES:
            mode_combo.append(mode_id, mode_name)
        mode_combo.set_active_id(self.keyboard_mode)
        mode_combo.connect("changed", self.on_settings_mode_changed)
        layout_grid.attach(mode_label, 0, 0, 1, 1)
        layout_grid.attach(mode_combo, 1, 0, 2, 1)
        self.settings_mode_combo = mode_combo

        layout_label = Gtk.Label(label="Keyboard Layout", xalign=0)
        layout_combo = Gtk.ComboBoxText()
        for layout_key, layout_name in self.keyboard_layout_choices:
            layout_combo.append(layout_key, layout_name)
        if self.keyboard_layout not in dict(self.keyboard_layout_choices):
            active_config = self.keyboard_layouts.get(self.keyboard_layout)
            if active_config is not None:
                layout_combo.append(self.keyboard_layout, active_config["label"])
        layout_combo.set_active_id(self.keyboard_layout)
        layout_combo.connect("changed", self.on_settings_layout_changed)
        layout_grid.attach(layout_label, 0, 1, 1, 1)
        layout_grid.attach(layout_combo, 1, 1, 2, 1)
        self.settings_layout_combo = layout_combo

        sync_layout_check = Gtk.CheckButton(label="Sync with System Keyboard Layout")
        sync_layout_check.set_active(self.sync_system_layout)
        sync_layout_check.connect("toggled", self.on_settings_sync_layout_toggled)
        layout_grid.attach(sync_layout_check, 0, 2, 3, 1)
        self.settings_sync_layout_check = sync_layout_check

        prediction_check = Gtk.CheckButton(label="Show Typing Suggestions Toolbar")
        prediction_check.set_active(self.text_prediction_enabled)
        prediction_check.connect("toggled", self.on_settings_prediction_toggled)
        layout_grid.attach(prediction_check, 0, 3, 3, 1)
        self.settings_prediction_check = prediction_check

        current_text_check = Gtk.CheckButton(label="Show Current Text Preview Toolbar")
        current_text_check.set_active(self.show_current_text_bar)
        current_text_check.connect("toggled", self.on_settings_current_text_toggled)
        layout_grid.attach(current_text_check, 0, 4, 3, 1)
        self.settings_current_text_check = current_text_check

        media_row_check = Gtk.CheckButton(
            label="Show System & Media Controls Row (Brightness, Volume, Playback)"
        )
        media_row_check.set_active(self.show_media_row)
        media_row_check.connect("toggled", self.on_settings_media_row_toggled)
        layout_grid.attach(media_row_check, 0, 5, 3, 1)
        self.settings_media_row_check = media_row_check

        fast_layout_check = Gtk.CheckButton(
            label="Show Top-Bar Fast Language Switcher (PL / UA / RU / EN / AR)"
        )
        fast_layout_check.set_active(self.show_fast_layout_bar)
        fast_layout_check.connect("toggled", self.on_settings_fast_layout_toggled)
        layout_grid.attach(fast_layout_check, 0, 6, 3, 1)
        self.settings_fast_layout_check = fast_layout_check

        modifier_hints_check = Gtk.CheckButton(
            label="Highlight Alternate / Accent Keys in Orange (AltGr Viewer)"
        )
        modifier_hints_check.set_active(self.show_modifier_hints)
        modifier_hints_check.connect("toggled", self.on_settings_modifier_hints_toggled)
        layout_grid.attach(modifier_hints_check, 0, 7, 3, 1)
        self.settings_modifier_hints_check = modifier_hints_check

        notebook.append_page(layout_grid, Gtk.Label(label="Toolbars & Layout"))

        # --- Tab 3: Typing & Accessibility ---
        typing_grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        typing_grid.set_border_width(12)

        trigger_label = Gtk.Label(label="Key Activation", xalign=0)
        trigger_combo = Gtk.ComboBoxText()
        for mode_id, mode_label in INPUT_TRIGGER_CHOICES:
            trigger_combo.append(mode_id, mode_label)
        trigger_combo.set_active_id(self.input_trigger_mode)
        trigger_combo.connect("changed", self.on_settings_trigger_changed)
        typing_grid.attach(trigger_label, 0, 0, 1, 1)
        typing_grid.attach(trigger_combo, 1, 0, 2, 1)
        self.settings_trigger_combo = trigger_combo

        auto_cap_check = Gtk.CheckButton(label="Auto-Capitalize Sentences (. ! ?)")
        auto_cap_check.set_active(self.auto_capitalize)
        auto_cap_check.connect("toggled", self.on_settings_auto_cap_toggled)
        typing_grid.attach(auto_cap_check, 0, 1, 3, 1)
        self.settings_auto_cap_check = auto_cap_check

        auto_space_check = Gtk.CheckButton(
            label="Insert Space Automatically After Accepting Suggestion"
        )
        auto_space_check.set_active(self.auto_space_after_suggestion)
        auto_space_check.connect("toggled", self.on_settings_auto_space_toggled)
        typing_grid.attach(auto_space_check, 0, 2, 3, 1)
        self.settings_auto_space_check = auto_space_check

        sticky_lock_check = Gtk.CheckButton(
            label="Sticky Modifiers (Tap Twice to Lock Shift / Ctrl / Alt / AltGr)"
        )
        sticky_lock_check.set_active(self.sticky_modifier_lock)
        sticky_lock_check.connect("toggled", self.on_settings_sticky_lock_toggled)
        typing_grid.attach(sticky_lock_check, 0, 3, 3, 1)
        self.settings_sticky_lock_check = sticky_lock_check

        gesture_check = Gtk.CheckButton(label="Touch / Swipe Typing")
        gesture_check.set_active(self.gesture_enabled)
        gesture_check.connect("toggled", self.on_settings_gesture_toggled)
        typing_grid.attach(gesture_check, 0, 4, 3, 1)
        self.settings_gesture_check = gesture_check

        visual_feedback_check = Gtk.CheckButton(label="Swipe Trail Visual Feedback")
        visual_feedback_check.set_active(self.gesture_visual_feedback_enabled)
        visual_feedback_check.set_sensitive(self.gesture_enabled)
        visual_feedback_check.connect(
            "toggled", self.on_settings_visual_feedback_toggled
        )
        typing_grid.attach(visual_feedback_check, 0, 5, 3, 1)
        self.settings_visual_feedback_check = visual_feedback_check

        dwell_check = Gtk.CheckButton(label="Hover Dwell Typing (Auto-Click on Rest)")
        dwell_check.set_active(self.dwell_enabled)
        dwell_check.connect("toggled", self.on_settings_dwell_toggled)
        typing_grid.attach(dwell_check, 0, 6, 3, 1)
        self.settings_dwell_check = dwell_check

        dwell_label = Gtk.Label(label="Dwell Delay (ms)", xalign=0)
        dwell_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 300, 2000, 50)
        dwell_scale.set_digits(0)
        dwell_scale.set_hexpand(True)
        dwell_scale.set_value(self.dwell_time_ms)
        dwell_scale.set_sensitive(self.dwell_enabled)
        dwell_scale.connect("value-changed", self.on_settings_dwell_time_changed)
        typing_grid.attach(dwell_label, 0, 7, 1, 1)
        typing_grid.attach(dwell_scale, 1, 7, 2, 1)
        self.settings_dwell_scale = dwell_scale

        notebook.append_page(typing_grid, Gtk.Label(label="Typing & Accessibility"))

        # --- Tab 4: Fade & Window ---
        window_grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        window_grid.set_border_width(12)

        fade_check = Gtk.CheckButton(
            label="Fade Keyboard Panel After Inactivity (Hover to Wake)"
        )
        fade_check.set_active(self.fade_on_inactivity)
        fade_check.connect("toggled", self.on_settings_fade_toggled)
        window_grid.attach(fade_check, 0, 0, 3, 1)
        self.settings_fade_check = fade_check

        fade_delay_label = Gtk.Label(label="Inactivity Delay (seconds)", xalign=0)
        fade_delay_spin = Gtk.SpinButton.new_with_range(3, 120, 1)
        fade_delay_spin.set_value(self.inactivity_delay_seconds)
        fade_delay_spin.set_sensitive(self.fade_on_inactivity)
        fade_delay_spin.connect("value-changed", self.on_settings_fade_delay_changed)
        window_grid.attach(fade_delay_label, 0, 1, 1, 1)
        window_grid.attach(fade_delay_spin, 1, 1, 2, 1)
        self.settings_fade_delay_spin = fade_delay_spin

        fade_opacity_label = Gtk.Label(label="Faded Opacity (%)", xalign=0)
        fade_opacity_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 10, 85, 5
        )
        fade_opacity_scale.set_digits(0)
        fade_opacity_scale.set_hexpand(True)
        fade_opacity_scale.set_value(round(self.inactivity_fade_opacity * 100))
        fade_opacity_scale.set_sensitive(self.fade_on_inactivity)
        fade_opacity_scale.connect(
            "value-changed", self.on_settings_fade_opacity_changed
        )
        window_grid.attach(fade_opacity_label, 0, 2, 1, 1)
        window_grid.attach(fade_opacity_scale, 1, 2, 2, 1)
        self.settings_fade_opacity_scale = fade_opacity_scale

        start_minimized_check = Gtk.CheckButton(label="Start Minimized to System Tray")
        start_minimized_check.set_active(self.start_minimized)
        start_minimized_check.connect(
            "toggled", self.on_settings_start_minimized_toggled
        )
        window_grid.attach(start_minimized_check, 0, 3, 3, 1)
        self.settings_start_minimized_check = start_minimized_check

        backend_info = Gtk.Label(
            label=f"Active input backend: {getattr(self.backend, 'name', 'unknown')} (stuck-key watchdog active)",
            xalign=0,
        )
        window_grid.attach(backend_info, 0, 4, 3, 1)

        notebook.append_page(window_grid, Gtk.Label(label="Fade & Window"))

        # Bottom utility buttons
        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        about_button = Gtk.Button(label="About")
        about_button.connect("clicked", self.on_settings_about_clicked)
        report_bugs_button = Gtk.Button(label="Report bugs")
        report_bugs_button.connect("clicked", self.on_settings_report_bugs_clicked)
        quit_button = Gtk.Button(label="Quit")
        quit_button.connect("clicked", self.on_settings_quit_clicked)
        footer_box.pack_start(about_button, False, False, 0)
        footer_box.pack_start(report_bugs_button, False, False, 0)
        footer_box.pack_end(quit_button, False, False, 0)
        content.pack_start(footer_box, False, False, 0)

        self.settings_dialog = dialog
        dialog.show_all()

    def on_settings_dialog_response(self, dialog, response_id):
        dialog.destroy()

    def on_settings_dialog_destroy(self, dialog):
        self.settings_dialog = None
        self.settings_preset_combo = None
        self.settings_preset_delete_btn = None
        self.settings_gesture_check = None
        self.settings_visual_feedback_check = None
        self.settings_sync_layout_check = None
        self.settings_layout_combo = None
        self.settings_mode_combo = None
        self.settings_theme_combo = None
        self.settings_accent_combo = None
        self.settings_accent_color_btn = None
        self.settings_custom_colors_check = None
        self.settings_win_bg_btn = None
        self.settings_key_bg_btn = None
        self.settings_mod_bg_btn = None
        self.settings_text_color_btn = None
        self.settings_key_border_color_btn = None
        self.settings_win_border_color_btn = None
        self.settings_win_border_width_scale = None
        self.settings_key_border_width_scale = None
        self.settings_font_weight_combo = None
        self.settings_key_shadow_check = None
        self.settings_opacity_scale = None
        self.settings_font_scale = None
        self.settings_radius_scale = None
        self.settings_spacing_scale = None
        self.settings_prediction_check = None
        self.settings_media_row_check = None
        self.settings_current_text_check = None
        self.settings_fast_layout_check = None
        self.settings_modifier_hints_check = None
        self.settings_trigger_combo = None
        self.settings_auto_cap_check = None
        self.settings_auto_space_check = None
        self.settings_sticky_lock_check = None
        self.settings_dwell_check = None
        self.settings_dwell_scale = None
        self.settings_fade_check = None
        self.settings_fade_delay_spin = None
        self.settings_fade_opacity_scale = None
        self.settings_start_minimized_check = None

    def on_settings_preset_changed(self, widget):
        if self._syncing_settings_dialog:
            return
        preset_name = widget.get_active_id()
        if self.settings_preset_delete_btn is not None:
            self.settings_preset_delete_btn.set_sensitive(bool(preset_name))
        if preset_name:
            self.load_user_preset(preset_name)

    def on_settings_save_preset_clicked(self, _widget):
        parent = self.settings_dialog or self
        prompt = Gtk.Dialog(
            title="Save Preset",
            transient_for=parent,
            modal=True,
        )
        prompt.set_default_size(340, 120)
        prompt.add_button("Cancel", Gtk.ResponseType.CANCEL)
        prompt.add_button("Save", Gtk.ResponseType.OK)
        prompt.set_default_response(Gtk.ResponseType.OK)

        area = prompt.get_content_area()
        area.set_border_width(12)
        area.set_spacing(8)
        label = Gtk.Label(
            label="Enter a name for this keyboard preset:", xalign=0
        )
        entry = Gtk.Entry()
        entry.set_activates_default(True)
        entry.set_text(self.active_preset_name or "My Custom Preset")
        area.pack_start(label, False, False, 0)
        area.pack_start(entry, False, False, 0)
        prompt.show_all()

        response = prompt.run()
        name = entry.get_text().strip()
        prompt.destroy()
        if response == Gtk.ResponseType.OK and name:
            self.save_user_preset(name)

    def on_settings_delete_preset_clicked(self, _widget):
        if self.settings_preset_combo is None:
            return
        preset_name = self.settings_preset_combo.get_active_id()
        if preset_name:
            self.delete_user_preset(preset_name)

    def on_settings_theme_changed(self, widget):
        if self._syncing_settings_dialog:
            return
        selected = widget.get_active_id()
        if selected is not None:
            self.set_theme_by_label(selected)

    def on_settings_accent_changed(self, widget):
        if self._syncing_settings_dialog:
            return
        accent_hex = widget.get_active_id()
        if accent_hex is not None and accent_hex.startswith("#"):
            self.set_accent_color(accent_hex)

    def on_settings_accent_color_btn_set(self, widget):
        if not self._syncing_settings_dialog:
            self.set_accent_color(self._gdk_rgba_to_hex(widget.get_rgba()))

    def on_settings_custom_colors_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_use_custom_colors(widget.get_active())

    def on_settings_custom_color_set(self, widget, attr_name):
        if not self._syncing_settings_dialog:
            self.set_custom_color(attr_name, self._gdk_rgba_to_hex(widget.get_rgba()))

    def on_settings_win_border_color_set(self, widget):
        if not self._syncing_settings_dialog:
            self.set_window_border_color(self._gdk_rgba_to_hex(widget.get_rgba()))

    def on_settings_win_border_width_changed(self, widget):
        if not self._syncing_settings_dialog:
            self.set_window_border_width(widget.get_value())

    def on_settings_key_border_width_changed(self, widget):
        if not self._syncing_settings_dialog:
            self.set_key_border_width(widget.get_value())

    def on_settings_font_weight_changed(self, widget):
        if not self._syncing_settings_dialog:
            weight = widget.get_active_id()
            if weight is not None:
                self.set_font_weight(weight)

    def on_settings_key_shadow_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_key_shadow_enabled(widget.get_active())

    def on_settings_opacity_changed(self, widget):
        if self._syncing_settings_dialog:
            return
        val = max(0.30, min(1.0, round(widget.get_value() / 100.0, 2)))
        self.opacity = f"{val:.2f}"
        if hasattr(self, "opacity_btn") and self.opacity_btn is not None:
            self.opacity_btn.set_label(self.opacity)
        self.apply_css()
        self.save_settings()

    def on_settings_font_scale_changed(self, widget):
        if not self._syncing_settings_dialog:
            self.set_font_scale(widget.get_value() / 100.0)

    def on_settings_radius_changed(self, widget):
        if not self._syncing_settings_dialog:
            self.set_key_corner_radius(widget.get_value())

    def on_settings_spacing_changed(self, widget):
        if not self._syncing_settings_dialog:
            self.set_key_spacing(widget.get_value())

    def on_settings_media_row_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_show_media_row(widget.get_active())

    def on_settings_current_text_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_show_current_text_bar(widget.get_active())

    def on_settings_fast_layout_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_show_fast_layout_bar(widget.get_active())

    def on_settings_modifier_hints_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_show_modifier_hints(widget.get_active())

    def on_settings_trigger_changed(self, widget):
        if not self._syncing_settings_dialog:
            mode = widget.get_active_id()
            if mode is not None:
                self.set_input_trigger_mode(mode)

    def on_settings_auto_cap_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_auto_capitalize(widget.get_active())

    def on_settings_auto_space_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_auto_space_after_suggestion(widget.get_active())

    def on_settings_sticky_lock_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_sticky_modifier_lock(widget.get_active())

    def on_settings_dwell_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_dwell_enabled(widget.get_active())

    def on_settings_dwell_time_changed(self, widget):
        if not self._syncing_settings_dialog:
            self.set_dwell_time_ms(widget.get_value())

    def on_settings_fade_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_fade_on_inactivity(widget.get_active())

    def on_settings_fade_delay_changed(self, widget):
        if not self._syncing_settings_dialog:
            self.set_inactivity_delay_seconds(widget.get_value())

    def on_settings_fade_opacity_changed(self, widget):
        if not self._syncing_settings_dialog:
            self.set_inactivity_fade_opacity(widget.get_value() / 100.0)

    def on_settings_prediction_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_text_prediction_enabled(widget.get_active())

    def on_settings_gesture_toggled(self, widget):
        if self._syncing_settings_dialog:
            return
        if widget.get_active():
            self.enable_gesture_typing()
        else:
            self.disable_gesture_typing()
        if self.settings_visual_feedback_check is not None:
            self.settings_visual_feedback_check.set_sensitive(self.gesture_enabled)

    def on_settings_visual_feedback_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_gesture_visual_feedback_enabled(widget.get_active())

    def on_settings_start_minimized_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_start_minimized(widget.get_active())

    def on_settings_sync_layout_toggled(self, widget):
        if not self._syncing_settings_dialog:
            self.set_sync_system_layout(widget.get_active())

    def on_settings_layout_changed(self, widget):
        if self._syncing_settings_dialog:
            return
        layout_key = widget.get_active_id()
        if layout_key is not None:
            self.set_keyboard_layout(layout_key)

    def on_settings_mode_changed(self, widget):
        if self._syncing_settings_dialog:
            return
        mode_id = widget.get_active_id()
        if mode_id is not None:
            self.set_keyboard_mode(mode_id)

    def on_settings_about_clicked(self, widget):
        self.on_tray_about(widget)

    def on_settings_report_bugs_clicked(self, widget):
        self.open_bug_report_url()

    def on_settings_quit_clicked(self, widget):
        self.on_tray_quit(widget)

    def create_suggestion_buttons(self):
        for _ in range(SUGGESTION_LIMIT):
            button = Gtk.Button()
            button.set_name("suggestion-button")
            button.set_label(" ")
            button.set_sensitive(False)
            button.connect("clicked", self.on_suggestion_clicked)
            self.suggestion_bar.pack_start(button, True, True, 0)
            self.suggestion_buttons.append(button)

    def update_suggestion_bar_visibility(self):
        self.suggestion_revealer.set_reveal_child(self.text_prediction_enabled)
        if self.text_prediction_enabled:
            self.suggestion_revealer.show()
            self.suggestion_bar.show_all()
        else:
            self.suggestion_revealer.hide()
        self._last_suggestion_scale = None
        self.update_suggestion_bar_scale()

    def set_text_prediction_enabled(self, enabled):
        enabled = bool(enabled)
        if enabled == self.text_prediction_enabled:
            return

        self.text_prediction_enabled = enabled
        self.current_word = ""
        self.clear_suggestion_override(update=False)
        self.update_suggestion_bar_visibility()
        self.update_suggestions()
        if self.text_prediction_enabled:
            GLib.idle_add(self.preload_suggestions)
        self.sync_tray_items()

        self.save_settings()

    def set_start_minimized(self, enabled):
        enabled = bool(enabled)
        if enabled == self.start_minimized:
            return

        self.start_minimized = enabled
        self.sync_tray_items()
        self.save_settings()

    def preload_suggestions(self):
        self.suggestion_engine.ensure_loaded()
        return False

    def schedule_scale_update(self, delay_ms=50):
        if self._scale_timer_id is not None:
            GLib.source_remove(self._scale_timer_id)
        self._scale_timer_id = GLib.timeout_add(
            delay_ms, self._run_scheduled_scale_update
        )

    def _run_scheduled_scale_update(self):
        self._scale_timer_id = None
        self.update_suggestion_bar_scale()
        return False

    def on_resize(self, widget, event):
        self.width, self.height = self.get_size()
        x, y = self.get_position()
        if x > 0 and y > 0:
            self.pos_x, self.pos_y = x, y
        if self.gesture_controller is not None:
            self.gesture_controller.refresh_layout_cache()
        self.schedule_scale_update(50)

    def on_grid_size_allocate(self, widget, allocation):
        if self.gesture_controller is not None:
            self.gesture_controller.refresh_layout_cache()
            self.gesture_controller.queue_overlay_draw()
        self.schedule_scale_update(50)

    def update_suggestion_bar_scale(self):
        grid_width = self.grid.get_allocated_width() if hasattr(self, "grid") else 0
        grid_height = self.grid.get_allocated_height() if hasattr(self, "grid") else 0
        win_width, win_height = self.get_size()
        if grid_width <= 1:
            grid_width = max(1, (win_width or self.width or self.BASE_GRID_WIDTH) - 6)
        if grid_height <= 1:
            est_h = win_height or self.height or (5 * self.BASE_KEY_HEIGHT + 80)
            grid_height = max(1, est_h - 80)

        num_rows = max(1, len(self.get_active_key_rows()))
        base_grid_height = num_rows * self.BASE_KEY_HEIGHT
        height_scale = grid_height / max(1, base_grid_height)
        width_scale = grid_width / max(1, self.BASE_GRID_WIDTH)
        base_scale = max(0.55, min(2.2, min(width_scale, height_scale)))
        effective_scale = base_scale * self.font_scale

        key_font_size = max(
            8,
            min(42, int(round(self.BASE_KEY_FONT_SIZE * effective_scale))),
        )
        secondary_key_font_size = max(
            7,
            min(26, int(round(key_font_size * 0.74))),
        )
        header_font_size = max(
            9,
            min(18, int(round(self.BASE_HEADER_FONT_SIZE * min(1.25, effective_scale)))),
        )
        suggestion_font_size = max(
            9,
            min(28, int(round(self.BASE_SUGGESTION_FONT_SIZE * effective_scale))),
        )
        spacing = max(1, int(round(self.BASE_SUGGESTION_SPACING * base_scale)))
        margin = max(1, int(round(self.BASE_SUGGESTION_MARGIN * base_scale)))
        margin_bottom = max(
            0, int(round(self.BASE_SUGGESTION_MARGIN_BOTTOM * base_scale))
        )

        menu_open = (
            hasattr(self, "color_combobox")
            and self.color_combobox is not None
            and self.color_combobox.get_visible()
        )
        min_title_w = 720 if menu_open else 460
        show_title = (win_width or grid_width) >= min_title_w
        quantized_scale = round(effective_scale, 2)

        scale_values = (
            key_font_size,
            secondary_key_font_size,
            header_font_size,
            suggestion_font_size,
            spacing,
            margin,
            margin_bottom,
            quantized_scale,
            show_title,
            self.text_prediction_enabled,
        )

        if scale_values == self._last_suggestion_scale:
            return False

        self._last_suggestion_scale = scale_values
        self.key_font_size = key_font_size
        self.secondary_key_font_size = secondary_key_font_size
        self.header_font_size = header_font_size
        self.suggestion_font_size = suggestion_font_size
        self.layout_scale = quantized_scale

        if hasattr(self, "header") and self.header is not None:
            self.header.set_title(APP_DISPLAY_NAME if show_title else "")

        if hasattr(self, "suggestion_bar") and self.suggestion_bar is not None:
            self.suggestion_bar.set_spacing(spacing)
            self.suggestion_bar.set_margin_start(margin)
            self.suggestion_bar.set_margin_end(margin)
            self.suggestion_bar.set_margin_top(margin)
            self.suggestion_bar.set_margin_bottom(margin_bottom)

        self.apply_css()
        return False

    def on_map_keep_above(self, widget, event):
        self.request_keep_above()
        self._keep_above_retries = 30
        if self._keep_above_timer_id is None:
            self._keep_above_timer_id = GLib.timeout_add(500, self.keep_above_tick)
        return False

    def request_keep_above(self):
        self.set_keep_above(True)
        self.stick()

    def keep_above_tick(self):
        self.request_keep_above()
        self._keep_above_retries -= 1
        if self._keep_above_retries <= 0:
            self._keep_above_timer_id = None
            return False
        return True

    def on_window_state_changed(self, widget, event):
        if (event.new_window_state & Gdk.WindowState.ABOVE) == 0:
            self.request_keep_above()
        return False

    def create_button(
        self,
        label_="",
        callback=None,
        callback2=None,
        callbacks=0,
        hide_with_menu=True,
    ):
        button = Gtk.Button(label=label_)
        button.set_can_focus(False)
        button.set_focus_on_click(False)
        button.set_name("headbar-button")
        if callbacks == 1:
            button.connect("clicked", callback)
        elif callbacks == 2:
            button.connect("clicked", callback, callback2)

        if label_ == self.opacity:
            self.opacity_btn = button
            self.opacity_btn.set_tooltip_text("opacity")

        button.get_style_context().add_class("header-button")
        self.header.pack_end(button)
        if hide_with_menu:
            self.buttons.append(button)
        return button

    def change_visibility(self, widget=None):
        for button in self.buttons:
            if button is not self.menu_button:
                button.set_visible(not button.get_visible())
        self.color_combobox.set_visible(not self.color_combobox.get_visible())
        self._last_suggestion_scale = None
        self.update_suggestion_bar_scale()

    def change_color(self, widget):
        selected_label = self.color_combobox.get_active_text()
        if selected_label and selected_label in self.color_map:
            self.set_theme_by_label(selected_label, save=False)

    @staticmethod
    def _parse_opacity(value, default=0.90):
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return default
        return max(0.05, min(1.0, numeric))

    def change_opacity(self, widget, increase_opacity):
        current = self._parse_opacity(self.opacity)
        if increase_opacity:
            updated = min(1.0, round(current + 0.01, 2))
        else:
            updated = max(0.05, round(current - 0.01, 2))
        self.opacity = f"{updated:.2f}"
        self.opacity_btn.set_label(self.opacity)
        self.apply_css()
        self.sync_settings_dialog_controls()

    def apply_css(self):
        css = build_theme_css(
            style_variant=self.style_variant,
            bg_color=self.bg_color,
            text_color=self.text_color,
            theme_opacity=self._parse_opacity(self.opacity),
            desktop_env=DESKTOP_ENV,
            accent_hex=self.accent_color,
            key_font_size=self.key_font_size,
            secondary_key_font_size=self.secondary_key_font_size,
            header_font_size=self.header_font_size,
            suggestion_font_size=self.suggestion_font_size,
            key_radius=self.key_corner_radius,
            key_spacing=self.key_spacing,
            font_weight=self.font_weight,
            key_border_width=self.key_border_width,
            window_border_width=self.window_border_width,
            window_border_color=self.window_border_color,
            key_shadow_enabled=self.key_shadow_enabled,
            use_custom_colors=self.use_custom_colors,
            custom_window_bg=self.custom_window_bg,
            custom_key_bg=self.custom_key_bg,
            custom_modifier_bg=self.custom_modifier_bg,
            custom_text_color=self.custom_text_color,
            custom_key_border_color=self.custom_key_border_color,
        )

        try:
            self.css_provider.load_from_data(css.encode("utf-8"))
        except GLib.GError as exc:
            print(f"CSS Error: {exc.message}")
            return

        screen = self.get_screen()
        if screen is not None and not self._css_provider_registered:
            Gtk.StyleContext.add_provider_for_screen(
                screen,
                self.css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER,
            )
            self._css_provider_registered = True

        self.refresh_vector_icons()

    def create_row(self, grid, row_index, keys):
        col = 0

        for key_event in keys:
            width = KEY_WIDTHS.get(key_event, 2)
            self.attach_grid_cell(grid, key_event, col, row_index, width, 1)
            col += width

    def _key_vector_icon_name(self, key_event):
        if key_event == TV_ACTION_OPTIONS:
            return "settings"
        if key_event == "Backspace" and self.keyboard_mode == KEYBOARD_MODE_COMPACT_TV:
            return "backspace"
        return None

    def attach_grid_cell(self, grid, key_event, col, row_index, width, height=1):
        if key_event.startswith(SPACER_KEY_PREFIX):
            spacer = Gtk.Box()
            spacer.set_sensitive(False)
            grid.attach(spacer, col, row_index, width, height)
            return

        icon_name = self._key_vector_icon_name(key_event)
        label_text = "" if icon_name else self.get_button_label(key_event)
        button = Gtk.Button() if icon_name else Gtk.Button(label=label_text)
        if icon_name:
            key_icon_px = max(15, min(30, int(round(self.key_font_size * 1.15))))
            set_button_vector_icon(
                button, icon_name, size_px=key_icon_px, color=self.get_active_icon_color()
            )
        button.set_can_focus(False)
        button.set_focus_on_click(False)
        ctx = button.get_style_context()
        if width <= 2 and len(label_text) >= 4:
            ctx.add_class("compact-label")
        if key_event in MODIFIER_KEYS or key_event in {
            "CapsLock",
            "Tab",
            "Backspace",
            "Enter",
            "Delete",
            "Esc",
        }:
            ctx.add_class("modifier-key")
        button.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.BUTTON1_MOTION_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        button.connect("button-press-event", self.on_key_button_press_event, key_event)
        button.connect("motion-notify-event", self.on_key_button_motion_event, key_event)
        button.connect("button-release-event", self.on_key_button_release_event, key_event)
        button.connect("enter-notify-event", self.on_key_button_enter_notify_event, key_event)
        button.connect("leave-notify-event", self.on_key_button_leave_notify_event)

        if key_event in TV_ACTION_KEYS:
            ctx.add_class("sidebar-key")
            tooltips = {
                TV_ACTION_HIDE: "Hide keyboard",
                TV_ACTION_LANG: "Switch keyboard layout (right-click to choose)",
                TV_ACTION_LAYER_ALPHA: "Letters layer",
                TV_ACTION_LAYER_NUMBERS: "Numbers, function keys, and navigation layer",
                TV_ACTION_OPTIONS: "Open Vboard customization options",
            }
            if key_event in tooltips:
                button.set_tooltip_text(tooltips[key_event])
        elif key_event == "Backspace" and icon_name:
            button.set_tooltip_text("Backspace")

        self.key_buttons[key_event] = button
        if key_event in self.modifiers:
            self.modifier_buttons[key_event] = button

        grid.attach(button, col, row_index, width, height)

    def get_button_label(self, key_event):
        if key_event == TV_ACTION_HIDE:
            return "Hide"
        if key_event == TV_ACTION_LANG:
            return self.get_current_layout_short_label()
        if key_event == TV_ACTION_LAYER_ALPHA:
            return "ABC"
        if key_event == TV_ACTION_LAYER_NUMBERS:
            return "123"
        if key_event == TV_ACTION_OPTIONS:
            return ""

        special_labels = {
            "CapsLock": "Caps",
            "Delete": "Del",
            "Insert": "Ins",
            "Home": "Home",
            "End": "End",
            "PageUp": "PgUp",
            "PageDown": "PgDn",
            "Print": "PrtSc",
            "ScrollLock": "ScrLk",
            "Pause": "Pause",
            "NumLock": "Num",
            "KP_Divide": "/",
            "KP_Multiply": "*",
            "KP_Subtract": "-",
            "KP_Add": "+",
            "KP_Enter": "↵",
            "KP_Decimal": ".",
            **{f"KP_{digit}": str(digit) for digit in range(10)},
        }
        if key_event == "Backspace" and self.keyboard_mode == KEYBOARD_MODE_COMPACT_TV:
            return ""
        if key_event in special_labels:
            return special_labels[key_event]

        if key_event == "Alt_R" and (
            self.keyboard_mode == KEYBOARD_MODE_COMPACT_TV
            or bool(self.get_active_altgr_map())
        ):
            return "AltGr"

        if key_event in MODIFIER_KEYS:
            return key_event[:-2]

        key_labels = self.get_active_key_labels()
        shifted_map = self.get_active_shifted_map()
        altgr_map = self.get_active_altgr_map()
        altgr_shifted_map = self.get_active_altgr_shifted_map()
        shift_active = self.modifiers["Shift_L"] or self.modifiers["Shift_R"]
        altgr_active = self.modifiers.get("Alt_R", False)
        uppercase_active = shift_active != self.caps_lock_active

        if altgr_active:
            if uppercase_active and key_event in altgr_shifted_map:
                return altgr_shifted_map[key_event]
            if key_event in altgr_map:
                altgr_label = altgr_map[key_event]
                if len(altgr_label) == 1 and altgr_label.isalpha():
                    return (
                        altgr_label.upper()
                        if uppercase_active
                        else altgr_label.lower()
                    )
                return altgr_label

        key_label = key_labels.get(key_event, key_event)

        if len(key_label) == 1 and key_label.isalpha():
            return key_label.upper() if uppercase_active else key_label.lower()

        if shift_active and key_event in shifted_map:
            return shifted_map[key_event]

        return key_label

    def update_key_labels(self):
        for key_label, button in self.key_buttons.items():
            if self._key_vector_icon_name(key_label):
                continue
            button.set_label(self.get_button_label(key_label))

    def update_modifier(self, key_event, value, locked=False):
        self.modifiers[key_event] = bool(value)
        if not value:
            self.locked_modifiers[key_event] = False
        else:
            self.locked_modifiers[key_event] = bool(locked)
        button = self.modifier_buttons.get(key_event)
        if button is not None:
            style_context = button.get_style_context()
            modifier_class = (
                "active-command-modifier"
                if key_event.startswith(("Shift", "Ctrl", "Alt"))
                else "active-modifier"
            )
            style_context.remove_class("active-modifier")
            style_context.remove_class("active-command-modifier")
            style_context.remove_class("locked-modifier")
            if value:
                style_context.add_class(modifier_class)
                if self.locked_modifiers[key_event]:
                    style_context.add_class("locked-modifier")
        if key_event == "Alt_R":
            self.update_modifier_hints()

    def toggle_modifier_key(self, key_event):
        if self.sticky_modifier_lock:
            if not self.modifiers[key_event]:
                self.update_modifier(key_event, True, locked=False)
            elif not self.locked_modifiers.get(key_event, False):
                self.update_modifier(key_event, True, locked=True)
            else:
                self.update_modifier(key_event, False, locked=False)
        else:
            self.update_modifier(key_event, not self.modifiers[key_event], locked=False)

        if self.modifiers["Shift_L"] and self.modifiers["Shift_R"]:
            self.update_modifier("Shift_L", False)
            self.update_modifier("Shift_R", False)

        self.update_key_labels()

    def set_caps_lock_active(self, active, update_system=True):
        active = bool(active)
        if update_system and active != self.caps_lock_active:
            empty_modifiers = {modifier: False for modifier in MODIFIER_KEYS}
            if self.gesture_controller is not None:
                self.gesture_controller.note_non_gesture_key()
            self.backend.emit_key("CapsLock", empty_modifiers)

        if active == self.caps_lock_active:
            return

        self.caps_lock_active = active
        button = self.key_buttons.get("CapsLock")
        if button is not None:
            style_context = button.get_style_context()
            style_context.remove_class("active-modifier")
            style_context.remove_class("active-command-modifier")
            if active:
                style_context.add_class("active-command-modifier")
        self.update_key_labels()

    def toggle_caps_lock(self):
        self.set_caps_lock_active(not self.caps_lock_active)
        self.current_word = ""
        self.update_suggestions()

    def handle_tv_action_key(self, widget, event, key_event):
        if key_event == TV_ACTION_HIDE:
            if self.tray_icon is not None:
                self.toggle_visibility()
            else:
                self.iconify()
            return True
        if key_event == TV_ACTION_LANG:
            if event.button == 3:
                self.popup_layout_menu(widget, event)
            else:
                self.cycle_keyboard_layout()
            return True
        if key_event == TV_ACTION_LAYER_ALPHA:
            self.set_compact_tv_layer(COMPACT_TV_LAYER_ALPHA)
            return True
        if key_event == TV_ACTION_LAYER_NUMBERS:
            self.set_compact_tv_layer(COMPACT_TV_LAYER_NUMBERS)
            return True
        if key_event == TV_ACTION_OPTIONS:
            self.open_settings_dialog()
            return True
        return False

    def on_key_button_press_event(self, widget, event, key_event):
        if event.type in (Gdk.EventType._2BUTTON_PRESS, Gdk.EventType._3BUTTON_PRESS):
            return True

        self.reset_inactivity_timer()
        self.cancel_dwell_timer()
        self.stop_key_repeat()
        self._pending_release_key = None
        self.clear_key_button_visual_states(except_button=widget)
        self.clear_suggestion_override(update=False)

        if key_event in TV_ACTION_KEYS:
            if event.button in (1, 3):
                self.handle_tv_action_key(widget, event, key_event)
                return True
            return False

        if event.button == 3:
            if key_event not in self.modifiers:
                self.emit_shifted_key(key_event)
            return True

        if event.button != 1:
            return False

        if key_event == "CapsLock":
            self.toggle_caps_lock()
            self.reset_modifiers()
            return False

        if key_event in self.modifiers:
            self.toggle_modifier_key(key_event)
            return False

        if self.gesture_controller is not None and self.gesture_controller.handle_key_press(
            widget,
            event,
            key_event,
        ):
            return False

        if self.input_trigger_mode == INPUT_TRIGGER_RELEASE:
            self._pending_release_key = (widget, key_event)
            return False

        self.emit_key(key_event)
        self.delay_source = GLib.timeout_add(400, self.start_repeat, key_event)
        return False

    def on_key_button_motion_event(self, widget, event, key_event):
        if self.gesture_controller is not None:
            self.gesture_controller.handle_key_motion(widget, event)
        return False

    def on_key_button_release_event(self, widget, event, key_event):
        self.schedule_key_button_visual_reset()
        if event.button != 1:
            return False

        if self.gesture_controller is not None and self.gesture_controller.handle_key_release(
            widget,
            event,
            key_event,
        ):
            return False

        if (
            self._pending_release_key is not None
            and self._pending_release_key[0] is widget
        ):
            _pending_widget, pending_key = self._pending_release_key
            self._pending_release_key = None
            self.emit_key(pending_key)
            return False

        self.stop_key_repeat()
        return False

    def on_key_button_enter_notify_event(self, widget, event, key_event):
        self.reset_inactivity_timer()
        if self.dwell_enabled:
            self.start_dwell_timer(widget, key_event)
        return False

    def on_key_button_leave_notify_event(self, widget, event):
        if (
            self._pending_release_key is not None
            and self._pending_release_key[0] is widget
        ):
            self._pending_release_key = None
        if self._dwell_target is not None and self._dwell_target[0] is widget:
            self.cancel_dwell_timer()
        widget.unset_state_flags(Gtk.StateFlags.ACTIVE | Gtk.StateFlags.PRELIGHT)
        return False

    def on_window_button_release_event(self, widget, event):
        if (
            getattr(event, "button", 1) == 1
            and self.gesture_controller is not None
            and self.gesture_controller.active_gesture is not None
        ):
            self.gesture_controller.handle_key_release(widget, event)
            self.schedule_key_button_visual_reset()
            return False
        self.stop_all_active_keys()
        if self.gesture_controller is not None:
            self.gesture_controller.cancel_gesture()
        self.schedule_key_button_visual_reset()
        return False

    def on_window_leave_notify_event(self, widget, event):
        detail = getattr(event, "detail", None)
        mode = getattr(event, "mode", None)
        if detail == Gdk.NotifyType.INFERIOR:
            return False
        if mode in (Gdk.CrossingMode.GRAB, Gdk.CrossingMode.UNGRAB):
            return False
        if (
            self.gesture_controller is not None
            and self.gesture_controller.active_gesture is not None
        ):
            return False
        self.stop_all_active_keys()
        self.schedule_key_button_visual_reset()
        return False

    def schedule_key_button_visual_reset(self):
        GLib.idle_add(self.clear_key_button_visual_states)

    def clear_key_button_visual_states(self, except_button=None):
        stale_flags = (
            Gtk.StateFlags.ACTIVE
            | Gtk.StateFlags.PRELIGHT
            | Gtk.StateFlags.FOCUSED
        )
        for button in self.key_buttons.values():
            if button is except_button:
                continue
            button.unset_state_flags(stale_flags)
        return False

    def stop_key_repeat(self):
        delay_source = getattr(self, "delay_source", None)
        if delay_source is not None:
            GLib.source_remove(delay_source)
            self.delay_source = None
        repeat_source = getattr(self, "repeat_source", None)
        if repeat_source is not None:
            GLib.source_remove(repeat_source)
            self.repeat_source = None

    def start_repeat(self, key_event):
        self.delay_source = None
        self.repeat_source = GLib.timeout_add(100, self.repeat_key, key_event)
        return False

    def repeat_key(self, key_event):
        self.emit_key(key_event)
        return True

    def emit_shifted_key(self, key_event):
        modifiers = dict(self.modifiers)
        modifiers["Shift_L"] = True
        self.emit_key(key_event, modifiers)

    def _update_text_preview_and_autocap(self, key_event, active_modifiers):
        if key_event == "Backspace":
            self.current_text_buffer = self.current_text_buffer[:-1]
            self._auto_cap_armed = False
            self.update_current_text_label()
            return

        if key_event == "Enter":
            self.current_text_buffer = ""
            self._auto_cap_armed = bool(self.auto_capitalize)
            self.update_current_text_label()
            return

        if key_event == "Space":
            ended_sentence = self.current_text_buffer.rstrip().endswith((".", "!", "?"))
            self.current_text_buffer = (self.current_text_buffer + " ")[-120:]
            if self.auto_capitalize and ended_sentence:
                self._auto_cap_armed = True
            self.update_current_text_label()
            return

        if self.has_active_command_modifier(
            active_modifiers
        ) and not self.is_altgr_character_key(key_event, active_modifiers):
            return

        typed_char = self.key_event_to_character(key_event, active_modifiers)
        if typed_char:
            self.current_text_buffer = (self.current_text_buffer + typed_char)[-120:]
            self._auto_cap_armed = False
            self.update_current_text_label()

    def emit_key(self, key_event, modifiers=None):
        self.reset_inactivity_timer()
        active_modifiers = dict(self.modifiers if modifiers is None else modifiers)
        if self.gesture_controller is not None:
            self.gesture_controller.note_non_gesture_key()
        self.track_current_word(key_event, active_modifiers)
        self._update_text_preview_and_autocap(key_event, active_modifiers)
        self.backend.emit_key(key_event, active_modifiers)
        self.reset_modifiers()
        if (
            self.auto_capitalize
            and self._auto_cap_armed
            and not self.caps_lock_active
            and not self.modifiers["Shift_L"]
            and not self.modifiers["Shift_R"]
        ):
            self.update_modifier("Shift_L", True, locked=False)
            self.update_key_labels()
            self._auto_cap_armed = False

    def emit_text(self, text):
        self.reset_inactivity_timer()
        for char in text:
            key_event, modifiers = self.character_to_key_event(char)
            if key_event is None:
                continue
            self.backend.emit_key(key_event, modifiers)
        if text:
            self.current_text_buffer = (self.current_text_buffer + text)[-120:]
            self.update_current_text_label()

    def reset_modifiers(self):
        for mod_key, active in self.modifiers.items():
            if active and not self.locked_modifiers.get(mod_key, False):
                self.update_modifier(mod_key, False)
        self.update_key_labels()

    def clear_suggestion_override(self, update=False):
        has_gesture_commit = (
            self.gesture_controller is not None and self.gesture_controller.has_committed_text()
        )
        if self.suggestion_override is None and not has_gesture_commit:
            return

        self.suggestion_override = None
        if self.gesture_controller is not None:
            self.gesture_controller.clear_committed_text()
        if update:
            self.update_suggestions()

    def is_altgr_character_key(self, key_event, modifiers=None):
        active_modifiers = self.modifiers if modifiers is None else modifiers
        if not active_modifiers.get("Alt_R", False):
            return False
        other_command_mods = (
            mod for mod in COMMAND_MODIFIER_KEYS if mod != "Alt_R"
        )
        if any(active_modifiers.get(mod, False) for mod in other_command_mods):
            return False
        return (
            key_event in self.get_active_altgr_map()
            or key_event in self.get_active_altgr_shifted_map()
        )

    def track_current_word(self, key_event, modifiers=None):
        active_modifiers = self.modifiers if modifiers is None else modifiers
        self.clear_suggestion_override(update=False)

        if not self.text_prediction_enabled:
            self.current_word = ""
            return

        if self.has_active_command_modifier(
            active_modifiers
        ) and not self.is_altgr_character_key(key_event, active_modifiers):
            self.current_word = ""
            self.update_suggestions()
            return

        if key_event == "Backspace":
            self.current_word = self.current_word[:-1]
            self.update_suggestions()
            return

        if key_event in {
            "Space",
            "Tab",
            "Enter",
            "Esc",
            "CapsLock",
            "Delete",
            "Insert",
            "Home",
            "End",
            "PageUp",
            "PageDown",
            "←",
            "→",
            "↑",
            "↓",
        }:
            self.current_word = ""
            self.update_suggestions()
            return

        typed_char = self.key_event_to_character(key_event, active_modifiers)
        if typed_char and all(
            char.isalpha() or char in SUPPORTED_WORD_CONNECTORS
            for char in typed_char
        ):
            self.current_word += typed_char
        else:
            self.current_word = ""

        self.update_suggestions()

    def has_active_command_modifier(self, modifiers=None):
        active_modifiers = self.modifiers if modifiers is None else modifiers
        return any(active_modifiers[modifier] for modifier in COMMAND_MODIFIER_KEYS)

    def key_event_to_character(self, key_event, modifiers=None):
        active_modifiers = self.modifiers if modifiers is None else modifiers
        shift_active = active_modifiers["Shift_L"] or active_modifiers["Shift_R"]
        altgr_active = active_modifiers.get("Alt_R", False)
        uppercase_active = shift_active != self.caps_lock_active
        key_labels = self.get_active_key_labels()
        shifted_map = self.get_active_shifted_map()
        altgr_map = self.get_active_altgr_map()
        altgr_shifted_map = self.get_active_altgr_shifted_map()

        if altgr_active:
            if uppercase_active and key_event in altgr_shifted_map:
                return altgr_shifted_map[key_event]
            if key_event in altgr_map:
                altgr_label = altgr_map[key_event]
                if len(altgr_label) == 1 and altgr_label.isalpha():
                    return (
                        altgr_label.upper()
                        if uppercase_active
                        else altgr_label.lower()
                    )
                if len(altgr_label) == 1:
                    return altgr_label

        key_label = key_labels.get(key_event, key_event)

        if len(key_label) == 1 and key_label.isalpha():
            return key_label.upper() if uppercase_active else key_label.lower()

        if shift_active and key_event in shifted_map:
            return shifted_map[key_event]

        if len(key_label) == 1:
            return key_label

        return None

    def update_suggestions(self):
        if not self.text_prediction_enabled:
            suggestions = []
        elif self.suggestion_override is not None:
            suggestions = self.suggestion_override
        else:
            suggestions = self.suggestion_engine.get_suggestions(
                self.current_word,
                SUGGESTION_LIMIT,
            )

        for index, button in enumerate(self.suggestion_buttons):
            style_context = button.get_style_context()
            if index < len(suggestions):
                label = suggestions[index]
                if self.suggestion_override is None:
                    label = self.apply_suggestion_case(label)
                button.set_label(label)
                button.set_sensitive(True)
                style_context.add_class("has-suggestion")
            else:
                button.set_label(" ")
                button.set_sensitive(False)
                style_context.remove_class("has-suggestion")
            button.show()

        self.suggestion_revealer.set_reveal_child(self.text_prediction_enabled)

    def apply_suggestion_case(self, suggestion):
        if self.current_word.isupper():
            return suggestion.upper()
        if self.current_word[:1].isupper() and self.current_word[1:].islower():
            return suggestion.capitalize()
        return suggestion

    def on_suggestion_clicked(self, widget):
        self.reset_inactivity_timer()
        suggestion = widget.get_label().strip()
        if not suggestion:
            return

        if (
            self.gesture_controller is not None
            and self.suggestion_override is not None
            and self.gesture_controller.has_committed_text()
        ):
            self.gesture_controller.replace_committed_word(suggestion)
            return

        if not self.current_word:
            return

        for modifier in MODIFIER_KEYS:
            if self.modifiers[modifier] and not self.locked_modifiers.get(modifier, False):
                self.update_modifier(modifier, False)

        empty_mods = {modifier: False for modifier in MODIFIER_KEYS}
        is_exact_prefix = suggestion.lower().startswith(self.current_word.lower())
        if is_exact_prefix:
            completion = suggestion[len(self.current_word):]
            if not completion:
                return
            for char in completion:
                key_event, modifiers = self.character_to_key_event(char)
                if key_event is None:
                    continue
                self.backend.emit_key(key_event, modifiers)
            self.current_text_buffer = (self.current_text_buffer + completion)[-120:]
        else:
            # Spell-check or diacritic replacement: erase typed word, then type corrected word
            erase_count = len(self.current_word)
            for _ in range(erase_count):
                self.backend.emit_key("Backspace", empty_mods)
            for char in suggestion:
                key_event, modifiers = self.character_to_key_event(char)
                if key_event is None:
                    continue
                self.backend.emit_key(key_event, modifiers)
            if self.current_text_buffer.lower().endswith(self.current_word.lower()):
                self.current_text_buffer = (
                    self.current_text_buffer[:-erase_count] + suggestion
                )[-120:]
            else:
                self.current_text_buffer = (self.current_text_buffer + suggestion)[-120:]

        if self.auto_space_after_suggestion:
            self.backend.emit_key("Space", empty_mods)
            self.current_text_buffer = (self.current_text_buffer + " ")[-120:]
            self.current_word = ""
        else:
            self.current_word = suggestion
        self.update_current_text_label()
        self.update_suggestions()

    def character_to_key_event(self, char):
        modifiers = {modifier: False for modifier in MODIFIER_KEYS}

        if char == " ":
            return "Space", modifiers

        entry = self.layout_character_lookup.get(char)
        if entry is not None:
            if len(entry) == 3:
                key_event, needs_shift, needs_altgr = entry
            else:
                key_event, needs_shift = entry
                needs_altgr = False
            if self.caps_lock_active and char.isalpha():
                needs_shift = not needs_shift
            if needs_shift:
                modifiers["Shift_L"] = True
            if needs_altgr:
                modifiers["Alt_R"] = True
            return key_event, modifiers

        return None, modifiers

    def read_settings(self):
        try:
            os.makedirs(self.CONFIG_DIR, exist_ok=True)
        except PermissionError:
            print("Warning: No permission to create the config directory. Proceeding without it.")

        try:
            if os.path.exists(self.CONFIG_FILE):
                self.config.read(self.CONFIG_FILE)
                self.bg_color = self.config.get(
                    "DEFAULT", "bg_color", fallback=self.bg_color
                ).replace(" ", "")
                raw_opacity = self.config.get(
                    "DEFAULT", "opacity", fallback=self.opacity
                )
                self.opacity = f"{self._parse_opacity(raw_opacity):.2f}"
                self.text_color = self.config.get(
                    "DEFAULT", "text_color", fallback="#F5F5F7"
                )
                self.style_variant = normalize_style_variant(
                    self.config.get(
                        "DEFAULT", "style_variant", fallback="graphite_dark"
                    )
                )
                self.accent_color = self.config.get(
                    "DEFAULT", "accent_color", fallback=DEFAULT_ACCENT_COLOR
                )
                try:
                    self.font_scale = max(
                        0.75,
                        min(
                            1.60,
                            float(
                                self.config.get(
                                    "DEFAULT",
                                    "font_scale",
                                    fallback=str(DEFAULT_FONT_SCALE),
                                )
                            ),
                        ),
                    )
                except ValueError:
                    self.font_scale = DEFAULT_FONT_SCALE
                raw_fw = self.config.get(
                    "DEFAULT", "font_weight", fallback=DEFAULT_FONT_WEIGHT
                ).strip()
                self.font_weight = (
                    raw_fw
                    if raw_fw in ("400", "500", "600", "700")
                    else DEFAULT_FONT_WEIGHT
                )
                try:
                    self.key_corner_radius = max(
                        0,
                        min(
                            16,
                            self.config.getint(
                                "DEFAULT",
                                "key_corner_radius",
                                fallback=DEFAULT_KEY_RADIUS,
                            ),
                        ),
                    )
                except ValueError:
                    self.key_corner_radius = DEFAULT_KEY_RADIUS
                try:
                    self.key_spacing = max(
                        1,
                        min(
                            8,
                            self.config.getint(
                                "DEFAULT",
                                "key_spacing",
                                fallback=DEFAULT_KEY_SPACING,
                            ),
                        ),
                    )
                except ValueError:
                    self.key_spacing = DEFAULT_KEY_SPACING
                try:
                    self.key_border_width = max(
                        0,
                        min(
                            3,
                            self.config.getint(
                                "DEFAULT",
                                "key_border_width",
                                fallback=DEFAULT_KEY_BORDER_WIDTH,
                            ),
                        ),
                    )
                except ValueError:
                    self.key_border_width = DEFAULT_KEY_BORDER_WIDTH
                try:
                    self.window_border_width = max(
                        0,
                        min(
                            4,
                            self.config.getint(
                                "DEFAULT",
                                "window_border_width",
                                fallback=DEFAULT_WINDOW_BORDER_WIDTH,
                            ),
                        ),
                    )
                except ValueError:
                    self.window_border_width = DEFAULT_WINDOW_BORDER_WIDTH
                base_defaults = get_base_theme_colors(
                    self.style_variant, self.bg_color, self.text_color
                )
                self.window_border_color = self.config.get(
                    "DEFAULT",
                    "window_border_color",
                    fallback=base_defaults["window_border_color"],
                )
                self.key_shadow_enabled = self.config.getboolean(
                    "DEFAULT",
                    "key_shadow_enabled",
                    fallback=DEFAULT_KEY_SHADOW_ENABLED,
                )
                self.use_custom_colors = self.config.getboolean(
                    "DEFAULT",
                    "use_custom_colors",
                    fallback=False,
                )
                self.custom_window_bg = self.config.get(
                    "DEFAULT", "custom_window_bg", fallback=base_defaults["window_bg"]
                )
                self.custom_key_bg = self.config.get(
                    "DEFAULT", "custom_key_bg", fallback=base_defaults["key_bg"]
                )
                self.custom_modifier_bg = self.config.get(
                    "DEFAULT",
                    "custom_modifier_bg",
                    fallback=base_defaults["modifier_bg"],
                )
                self.custom_text_color = self.config.get(
                    "DEFAULT", "custom_text_color", fallback=base_defaults["text_color"]
                )
                self.custom_key_border_color = self.config.get(
                    "DEFAULT",
                    "custom_key_border_color",
                    fallback=base_defaults["key_border_color"],
                )
                self.active_preset_name = self.config.get(
                    "DEFAULT", "active_preset_name", fallback=""
                )
                self.gesture_enabled = self.config.getboolean(
                    "DEFAULT", "gesture_enabled", fallback=True
                )
                self.gesture_visual_feedback_enabled = self.config.getboolean(
                    "DEFAULT",
                    "gesture_visual_feedback_enabled",
                    fallback=True,
                )
                self.text_prediction_enabled = self.config.getboolean(
                    "DEFAULT",
                    "text_prediction_enabled",
                    fallback=True,
                )
                self.show_media_row = self.config.getboolean(
                    "DEFAULT",
                    "show_media_row",
                    fallback=False,
                )
                self.show_current_text_bar = self.config.getboolean(
                    "DEFAULT",
                    "show_current_text_bar",
                    fallback=False,
                )
                self.show_fast_layout_bar = self.config.getboolean(
                    "DEFAULT",
                    "show_fast_layout_bar",
                    fallback=True,
                )
                self.show_modifier_hints = self.config.getboolean(
                    "DEFAULT",
                    "show_modifier_hints",
                    fallback=True,
                )
                raw_trigger = self.config.get(
                    "DEFAULT", "input_trigger_mode", fallback=INPUT_TRIGGER_PRESS
                )
                self.input_trigger_mode = (
                    raw_trigger
                    if raw_trigger in (INPUT_TRIGGER_PRESS, INPUT_TRIGGER_RELEASE)
                    else INPUT_TRIGGER_PRESS
                )
                self.auto_capitalize = self.config.getboolean(
                    "DEFAULT", "auto_capitalize", fallback=False
                )
                self.auto_space_after_suggestion = self.config.getboolean(
                    "DEFAULT", "auto_space_after_suggestion", fallback=False
                )
                self.sticky_modifier_lock = self.config.getboolean(
                    "DEFAULT", "sticky_modifier_lock", fallback=True
                )
                self.fade_on_inactivity = self.config.getboolean(
                    "DEFAULT", "fade_on_inactivity", fallback=False
                )
                try:
                    self.inactivity_delay_seconds = max(
                        3,
                        min(
                            120,
                            self.config.getint(
                                "DEFAULT",
                                "inactivity_delay_seconds",
                                fallback=DEFAULT_INACTIVITY_DELAY_SECONDS,
                            ),
                        ),
                    )
                except ValueError:
                    self.inactivity_delay_seconds = DEFAULT_INACTIVITY_DELAY_SECONDS
                try:
                    self.inactivity_fade_opacity = max(
                        0.10,
                        min(
                            0.85,
                            float(
                                self.config.get(
                                    "DEFAULT",
                                    "inactivity_fade_opacity",
                                    fallback=str(DEFAULT_INACTIVITY_FADE_OPACITY),
                                )
                            ),
                        ),
                    )
                except ValueError:
                    self.inactivity_fade_opacity = DEFAULT_INACTIVITY_FADE_OPACITY
                self.dwell_enabled = self.config.getboolean(
                    "DEFAULT", "dwell_enabled", fallback=False
                )
                try:
                    self.dwell_time_ms = max(
                        300,
                        min(
                            2500,
                            self.config.getint(
                                "DEFAULT",
                                "dwell_time_ms",
                                fallback=DEFAULT_DWELL_TIME_MS,
                            ),
                        ),
                    )
                except ValueError:
                    self.dwell_time_ms = DEFAULT_DWELL_TIME_MS
                self.start_minimized = self.config.getboolean(
                    "DEFAULT",
                    "start_minimized",
                    fallback=False,
                )
                self.sync_system_layout = self.config.getboolean(
                    "DEFAULT",
                    "sync_system_layout",
                    fallback=True,
                )
                self.keyboard_mode = self.normalize_keyboard_mode(
                    self.config.get(
                        "DEFAULT",
                        "keyboard_mode",
                        fallback=KEYBOARD_MODE_STANDARD,
                    )
                )
                self.keyboard_layout = self.normalize_keyboard_layout(
                    self.config.get(
                        "DEFAULT",
                        "keyboard_layout",
                        fallback=DEFAULT_KEYBOARD_LAYOUT,
                    )
                )
                try:
                    self.width = max(0, self.config.getint("DEFAULT", "width", fallback=0))
                    self.height = max(0, self.config.getint("DEFAULT", "height", fallback=0))
                except ValueError:
                    self.width = 0
                    self.height = 0
                pos_x_str = self.config.get("DEFAULT", "pos_x", fallback="0")
                pos_y_str = self.config.get("DEFAULT", "pos_y", fallback="0")
                try:
                    self.pos_x = int(pos_x_str)
                    self.pos_y = int(pos_y_str)
                    self.config_pos_x = self.pos_x
                    self.config_pos_y = self.pos_y
                except ValueError:
                    self.pos_x = self.config_pos_x = 0
                    self.pos_y = self.config_pos_y = 0

        except (configparser.Error, ValueError) as exc:
            print(f"Warning: Could not read config file ({exc}). Using default values.")

    def save_settings(self):
        saved_layout = (
            self.keyboard_layout
            if not self.keyboard_layouts.get(self.keyboard_layout, {}).get("dynamic")
            else DEFAULT_KEYBOARD_LAYOUT
        )
        self.config["DEFAULT"] = {
            "bg_color": self.bg_color,
            "opacity": self.opacity,
            "text_color": self.text_color,
            "style_variant": self.style_variant,
            "accent_color": self.accent_color,
            "font_scale": f"{self.font_scale:.2f}",
            "font_weight": str(self.font_weight),
            "key_corner_radius": str(self.key_corner_radius),
            "key_spacing": str(self.key_spacing),
            "key_border_width": str(self.key_border_width),
            "window_border_width": str(self.window_border_width),
            "window_border_color": self.window_border_color,
            "key_shadow_enabled": str(self.key_shadow_enabled),
            "use_custom_colors": str(self.use_custom_colors),
            "custom_window_bg": self.custom_window_bg,
            "custom_key_bg": self.custom_key_bg,
            "custom_modifier_bg": self.custom_modifier_bg,
            "custom_text_color": self.custom_text_color,
            "custom_key_border_color": self.custom_key_border_color,
            "active_preset_name": self.active_preset_name,
            "text_prediction_enabled": str(self.text_prediction_enabled),
            "show_media_row": str(self.show_media_row),
            "show_current_text_bar": str(self.show_current_text_bar),
            "show_fast_layout_bar": str(self.show_fast_layout_bar),
            "show_modifier_hints": str(self.show_modifier_hints),
            "input_trigger_mode": self.input_trigger_mode,
            "auto_capitalize": str(self.auto_capitalize),
            "auto_space_after_suggestion": str(self.auto_space_after_suggestion),
            "sticky_modifier_lock": str(self.sticky_modifier_lock),
            "fade_on_inactivity": str(self.fade_on_inactivity),
            "inactivity_delay_seconds": str(self.inactivity_delay_seconds),
            "inactivity_fade_opacity": f"{self.inactivity_fade_opacity:.2f}",
            "dwell_enabled": str(self.dwell_enabled),
            "dwell_time_ms": str(self.dwell_time_ms),
            "start_minimized": str(self.start_minimized),
            "sync_system_layout": str(self.sync_system_layout),
            "keyboard_mode": self.keyboard_mode,
            "gesture_enabled": str(self.gesture_enabled),
            "gesture_visual_feedback_enabled": str(
                self.gesture_visual_feedback_enabled
            ),
            "keyboard_layout": saved_layout,
            "width": str(self.width),
            "height": str(self.height),
            "pos_x": str(self.pos_x),
            "pos_y": str(self.pos_y),
        }

        try:
            with open(self.CONFIG_FILE, "w") as configfile:
                self.config.write(configfile)
        except (configparser.Error, IOError) as exc:
            print(f"Warning: Could not write to config file ({exc}). Changes will not be saved.")
