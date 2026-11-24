import atexit
import sys
import time

from .constants import FUNCTION_KEYS, MAX_KEY_HOLD_SECONDS, MODIFIER_KEYS

try:
    import uinput
except ImportError:
    uinput = None

try:
    import evdev
except ImportError:
    evdev = None


CORE_KEY_NAME_MAP = {
    "Esc": ("KEY_ESC",),
    "1": ("KEY_1",),
    "2": ("KEY_2",),
    "3": ("KEY_3",),
    "4": ("KEY_4",),
    "5": ("KEY_5",),
    "6": ("KEY_6",),
    "7": ("KEY_7",),
    "8": ("KEY_8",),
    "9": ("KEY_9",),
    "0": ("KEY_0",),
    "-": ("KEY_MINUS",),
    "=": ("KEY_EQUAL",),
    "Backspace": ("KEY_BACKSPACE",),
    "Tab": ("KEY_TAB",),
    "Q": ("KEY_Q",),
    "W": ("KEY_W",),
    "E": ("KEY_E",),
    "R": ("KEY_R",),
    "T": ("KEY_T",),
    "Y": ("KEY_Y",),
    "U": ("KEY_U",),
    "I": ("KEY_I",),
    "O": ("KEY_O",),
    "P": ("KEY_P",),
    "[": ("KEY_LEFTBRACE",),
    "]": ("KEY_RIGHTBRACE",),
    "Enter": ("KEY_ENTER",),
    "Ctrl_L": ("KEY_LEFTCTRL",),
    "Ctrl_R": ("KEY_RIGHTCTRL",),
    "A": ("KEY_A",),
    "S": ("KEY_S",),
    "D": ("KEY_D",),
    "F": ("KEY_F",),
    "G": ("KEY_G",),
    "H": ("KEY_H",),
    "J": ("KEY_J",),
    "K": ("KEY_K",),
    "L": ("KEY_L",),
    ";": ("KEY_SEMICOLON",),
    "'": ("KEY_APOSTROPHE",),
    "`": ("KEY_GRAVE",),
    "Shift_L": ("KEY_LEFTSHIFT",),
    "Shift_R": ("KEY_RIGHTSHIFT",),
    "\\": ("KEY_BACKSLASH",),
    "Z": ("KEY_Z",),
    "X": ("KEY_X",),
    "C": ("KEY_C",),
    "V": ("KEY_V",),
    "B": ("KEY_B",),
    "N": ("KEY_N",),
    "M": ("KEY_M",),
    ",": ("KEY_COMMA",),
    ".": ("KEY_DOT",),
    "/": ("KEY_SLASH",),
    "Alt_L": ("KEY_LEFTALT",),
    "Alt_R": ("KEY_RIGHTALT",),
    "Space": ("KEY_SPACE",),
    "CapsLock": ("KEY_CAPSLOCK",),
    "→": ("KEY_RIGHT",),
    "←": ("KEY_LEFT",),
    "↓": ("KEY_DOWN",),
    "↑": ("KEY_UP",),
    "Super_L": ("KEY_LEFTMETA",),
    "Super_R": ("KEY_RIGHTMETA",),
}

OPTIONAL_KEY_NAME_MAP = {
    "<": ("KEY_LESS", "KEY_102ND"),
    "Delete": ("KEY_DELETE",),
    "Insert": ("KEY_INSERT",),
    "Home": ("KEY_HOME",),
    "End": ("KEY_END",),
    "PageUp": ("KEY_PAGEUP",),
    "PageDown": ("KEY_PAGEDOWN",),
    "Print": ("KEY_SYSRQ", "KEY_PRINT"),
    "ScrollLock": ("KEY_SCROLLLOCK",),
    "Pause": ("KEY_PAUSE",),
    "NumLock": ("KEY_NUMLOCK",),
    "KP_Divide": ("KEY_KPSLASH",),
    "KP_Multiply": ("KEY_KPASTERISK",),
    "KP_Subtract": ("KEY_KPMINUS",),
    "KP_Add": ("KEY_KPPLUS",),
    "KP_Enter": ("KEY_KPENTER",),
    "KP_Decimal": ("KEY_KPDOT",),
    "VolumeMute": ("KEY_MUTE",),
    "VolumeDown": ("KEY_VOLUMEDOWN",),
    "VolumeUp": ("KEY_VOLUMEUP",),
    "PreviousSong": ("KEY_PREVIOUSSONG",),
    "PlayPause": ("KEY_PLAYPAUSE",),
    "NextSong": ("KEY_NEXTSONG",),
    "BrightnessDown": ("KEY_BRIGHTNESSDOWN",),
    "BrightnessUp": ("KEY_BRIGHTNESSUP",),
    **{f"KP_{digit}": (f"KEY_KP{digit}",) for digit in range(10)},
    **{function_key: (f"KEY_{function_key}",) for function_key in FUNCTION_KEYS},
}

TAP_ONLY_ACTION_KEYS = frozenset({"Print"})


class InputBackend:
    name = "unknown"

    def emit_key(self, key_label, modifiers):
        raise NotImplementedError

    def release_all_keys(self):
        return

    def check_stuck_keys(self, max_hold_seconds=MAX_KEY_HOLD_SECONDS):
        return []

    def destroy(self):
        return


class NullInputBackend(InputBackend):
    name = "disabled"

    def __init__(self, reason=None):
        self.reason = reason
        if reason:
            print(f"Warning: {reason}")

    def emit_key(self, key_label, modifiers):
        return


class _BaseUInputBackend(InputBackend):
    def _init_watchdog(self):
        self.pressed_keys = {}
        self._destroyed = False
        atexit.register(self.destroy)
        self._install_excepthook()

    def _install_excepthook(self):
        old_hook = sys.excepthook

        def _hook(exc_type, exc_value, exc_traceback):
            try:
                self.release_all_keys()
            except Exception:
                pass
            if old_hook is not None:
                old_hook(exc_type, exc_value, exc_traceback)

        sys.excepthook = _hook

    def _emit_raw(self, key_event, value, syn=True):
        raise NotImplementedError

    def _press_key(self, key_event, syn=True):
        self._emit_raw(key_event, 1, syn=syn)
        self.pressed_keys[key_event] = time.monotonic()

    def _release_key(self, key_event, syn=True):
        try:
            self._emit_raw(key_event, 0, syn=syn)
        finally:
            self.pressed_keys.pop(key_event, None)

    def release_all_keys(self):
        released = []
        for key_event in list(self.pressed_keys.keys()):
            try:
                self._emit_raw(key_event, 0, syn=True)
                released.append(key_event)
            except Exception:
                pass
            finally:
                self.pressed_keys.pop(key_event, None)
        return released

    def check_stuck_keys(self, max_hold_seconds=MAX_KEY_HOLD_SECONDS):
        now = time.monotonic()
        stuck = [
            key_event
            for key_event, pressed_at in list(self.pressed_keys.items())
            if now - pressed_at >= max_hold_seconds
        ]
        released = []
        for key_event in stuck:
            try:
                self._emit_raw(key_event, 0, syn=True)
                released.append(key_event)
            except Exception:
                pass
            finally:
                self.pressed_keys.pop(key_event, None)
        return released

    def emit_key(self, key_label, modifiers):
        key_event = self.key_map.get(key_label)
        if key_event is None:
            return

        applied_mods = []
        try:
            for mod_key in self.modifier_order:
                if modifiers.get(mod_key, False):
                    mod_event = self.key_map[mod_key]
                    self._press_key(mod_event, syn=False)
                    applied_mods.append(mod_event)

            self._press_key(key_event, syn=True)
            if key_label in TAP_ONLY_ACTION_KEYS:
                time.sleep(0.015)
            self._release_key(key_event, syn=True)
        finally:
            for mod_event in reversed(applied_mods):
                try:
                    self._release_key(mod_event, syn=True)
                except Exception:
                    pass


class UInputBackend(_BaseUInputBackend):
    name = "uinput"

    def __init__(self):
        if uinput is None:
            raise RuntimeError("python-uinput is not installed")

        self.key_map = {
            label: self._uinput_key(*names, required=True)
            for label, names in CORE_KEY_NAME_MAP.items()
        }
        for label, names in OPTIONAL_KEY_NAME_MAP.items():
            key_code = self._uinput_key(*names, required=False)
            if key_code is not None:
                self.key_map[label] = key_code

        self.modifier_order = [key for key in MODIFIER_KEYS if key in self.key_map]
        device_keys = list(dict.fromkeys(self.key_map.values()))
        self.device = uinput.Device(device_keys)
        self._init_watchdog()

    @staticmethod
    def _uinput_key(*names, required=True):
        for name in names:
            key = getattr(uinput, name, None)
            if key is not None:
                return key
        if required:
            raise RuntimeError(
                "python-uinput is missing required key constant(s): "
                + ", ".join(names)
            )
        return None

    def _emit_raw(self, key_event, value, syn=True):
        if self.device is None:
            return
        try:
            self.device.emit(key_event, value, syn=syn)
        except TypeError:
            self.device.emit(key_event, value)

    def destroy(self):
        if getattr(self, "_destroyed", False):
            return
        self._destroyed = True
        self.release_all_keys()
        device = getattr(self, "device", None)
        if device is not None:
            self.device = None
            destroy_fn = getattr(device, "destroy", None)
            if callable(destroy_fn):
                try:
                    destroy_fn()
                except Exception:
                    pass


class EvdevUInputBackend(_BaseUInputBackend):
    name = "evdev-uinput"

    def __init__(self):
        if evdev is None:
            raise RuntimeError("python-evdev is not installed")

        ecodes = evdev.ecodes
        self._ev_key = ecodes.EV_KEY
        self.key_map = {
            label: self._evdev_key(ecodes, *names, required=True)
            for label, names in CORE_KEY_NAME_MAP.items()
        }
        for label, names in OPTIONAL_KEY_NAME_MAP.items():
            key_code = self._evdev_key(ecodes, *names, required=False)
            if key_code is not None:
                self.key_map[label] = key_code

        self.modifier_order = [key for key in MODIFIER_KEYS if key in self.key_map]
        device_keys = list(dict.fromkeys(self.key_map.values()))
        self.device = evdev.UInput(
            {self._ev_key: device_keys},
            name="vboard",
        )
        self._init_watchdog()

    @staticmethod
    def _evdev_key(ecodes, *names, required=True):
        for name in names:
            key = getattr(ecodes, name, None)
            if key is not None:
                return key
        if required:
            raise RuntimeError(
                "python-evdev is missing required key constant(s): "
                + ", ".join(names)
            )
        return None

    def _emit_raw(self, key_event, value, syn=True):
        if self.device is None:
            return
        self.device.write(self._ev_key, key_event, value)
        if syn:
            self.device.syn()

    def destroy(self):
        if getattr(self, "_destroyed", False):
            return
        self._destroyed = True
        self.release_all_keys()
        device = getattr(self, "device", None)
        if device is not None:
            self.device = None
            close_fn = getattr(device, "close", None)
            if callable(close_fn):
                try:
                    close_fn()
                except Exception:
                    pass


def create_uinput_backend():
    errors = []
    if uinput is not None:
        try:
            return UInputBackend()
        except Exception as exc:
            errors.append(f"python-uinput: {exc}")

    if evdev is not None:
        try:
            return EvdevUInputBackend()
        except Exception as exc:
            errors.append(f"python-evdev: {exc}")

    if errors:
        raise RuntimeError("; ".join(errors))
    raise RuntimeError("Neither python-uinput nor python-evdev is installed")
