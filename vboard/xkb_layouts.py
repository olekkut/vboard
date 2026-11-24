import ctypes
from functools import lru_cache

from .layouts import ISO_LAYOUT_ROWS, STANDARD_LAYOUT_ROWS


# Linux evdev keycodes + 8 = XKB keycodes (xkbcommon / evdev rules).
VBOARD_KEY_TO_XKB_KEYCODE = {
    "`": 41 + 8,
    "1": 2 + 8,
    "2": 3 + 8,
    "3": 4 + 8,
    "4": 5 + 8,
    "5": 6 + 8,
    "6": 7 + 8,
    "7": 8 + 8,
    "8": 9 + 8,
    "9": 10 + 8,
    "0": 11 + 8,
    "-": 12 + 8,
    "=": 13 + 8,
    "Q": 16 + 8,
    "W": 17 + 8,
    "E": 18 + 8,
    "R": 19 + 8,
    "T": 20 + 8,
    "Y": 21 + 8,
    "U": 22 + 8,
    "I": 23 + 8,
    "O": 24 + 8,
    "P": 25 + 8,
    "[": 26 + 8,
    "]": 27 + 8,
    "A": 30 + 8,
    "S": 31 + 8,
    "D": 32 + 8,
    "F": 33 + 8,
    "G": 34 + 8,
    "H": 35 + 8,
    "J": 36 + 8,
    "K": 37 + 8,
    "L": 38 + 8,
    ";": 39 + 8,
    "'": 40 + 8,
    "\\": 43 + 8,
    "<": 86 + 8,
    "Z": 44 + 8,
    "X": 45 + 8,
    "C": 46 + 8,
    "V": 47 + 8,
    "B": 48 + 8,
    "N": 49 + 8,
    "M": 50 + 8,
    ",": 51 + 8,
    ".": 52 + 8,
    "/": 53 + 8,
}

# Common XKB dead keysyms mapped to readable keycap labels.
DEAD_KEYSYM_LABELS = {
    0xFE50: "`",  # dead_grave
    0xFE51: "´",  # dead_acute
    0xFE52: "^",  # dead_circumflex
    0xFE53: "~",  # dead_tilde
    0xFE54: "¯",  # dead_macron
    0xFE55: "˘",  # dead_breve
    0xFE56: "˙",  # dead_abovedot
    0xFE57: "¨",  # dead_diaeresis
    0xFE58: "°",  # dead_abovering
    0xFE59: "˝",  # dead_doubleacute
    0xFE5A: "ˇ",  # dead_caron
    0xFE5B: "¸",  # dead_cedilla
    0xFE5C: "˛",  # dead_ogonek
    0xFE63: "/",  # dead_stroke
}

ISO_XKB_LAYOUTS = frozenset(
    {
        "be",
        "ch",
        "cz",
        "de",
        "dk",
        "es",
        "fi",
        "fr",
        "gb",
        "hr",
        "hu",
        "is",
        "it",
        "nl",
        "no",
        "pt",
        "ro",
        "se",
        "si",
        "sk",
        "tr",
    }
)


class _XkbRuleNames(ctypes.Structure):
    _fields_ = [
        ("rules", ctypes.c_char_p),
        ("model", ctypes.c_char_p),
        ("layout", ctypes.c_char_p),
        ("variant", ctypes.c_char_p),
        ("options", ctypes.c_char_p),
    ]


_XKB_LIB = None
_XKB_LIB_LOADED = False


def _load_xkbcommon():
    global _XKB_LIB, _XKB_LIB_LOADED
    if _XKB_LIB_LOADED:
        return _XKB_LIB

    _XKB_LIB_LOADED = True
    for lib_name in ("libxkbcommon.so.0", "libxkbcommon.so"):
        try:
            lib = ctypes.CDLL(lib_name)
        except OSError:
            continue

        lib.xkb_context_new.argtypes = [ctypes.c_int]
        lib.xkb_context_new.restype = ctypes.c_void_p
        lib.xkb_context_unref.argtypes = [ctypes.c_void_p]
        lib.xkb_context_unref.restype = None

        lib.xkb_keymap_new_from_names.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_XkbRuleNames),
            ctypes.c_int,
        ]
        lib.xkb_keymap_new_from_names.restype = ctypes.c_void_p
        lib.xkb_keymap_unref.argtypes = [ctypes.c_void_p]
        lib.xkb_keymap_unref.restype = None

        lib.xkb_keymap_key_get_syms_by_level.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.POINTER(ctypes.c_uint32)),
        ]
        lib.xkb_keymap_key_get_syms_by_level.restype = ctypes.c_int

        lib.xkb_keysym_to_utf8.argtypes = [
            ctypes.c_uint32,
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]
        lib.xkb_keysym_to_utf8.restype = ctypes.c_int

        _XKB_LIB = lib
        return _XKB_LIB

    _XKB_LIB = None
    return None


def _keysym_to_label(lib, keysym):
    if keysym in DEAD_KEYSYM_LABELS:
        return DEAD_KEYSYM_LABELS[keysym]

    buf = ctypes.create_string_buffer(32)
    length = lib.xkb_keysym_to_utf8(keysym, buf, 32)
    if length <= 0:
        return ""
    text = buf.value.decode("utf-8", errors="ignore")
    if not text or not text.isprintable() or text.isspace():
        return ""
    return text


def _read_key_level(lib, keymap, keycode, level):
    syms = ctypes.POINTER(ctypes.c_uint32)()
    count = lib.xkb_keymap_key_get_syms_by_level(
        keymap,
        keycode,
        0,
        level,
        ctypes.byref(syms),
    )
    if count < 1 or not syms:
        return ""
    return _keysym_to_label(lib, int(syms[0]))


def make_dynamic_xkb_layout_id(xkb_layout, xkb_variant=""):
    if xkb_variant:
        return f"xkb:{xkb_layout}:{xkb_variant}"
    return f"xkb:{xkb_layout}"


@lru_cache(maxsize=64)
def _extract_xkb_maps(xkb_layout, xkb_variant):
    lib = _load_xkbcommon()
    if lib is None:
        return None

    context = lib.xkb_context_new(0)
    if not context:
        return None

    try:
        names = _XkbRuleNames(
            b"evdev",
            b"pc105",
            xkb_layout.encode("utf-8"),
            xkb_variant.encode("utf-8"),
            b"",
        )
        keymap = lib.xkb_keymap_new_from_names(context, ctypes.byref(names), 0)
        if not keymap:
            return None

        try:
            labels = {}
            shifted = {}
            altgr = {}
            altgr_shifted = {}

            for key_event, keycode in VBOARD_KEY_TO_XKB_KEYCODE.items():
                lvl0 = _read_key_level(lib, keymap, keycode, 0)
                lvl1 = _read_key_level(lib, keymap, keycode, 1)
                lvl2 = _read_key_level(lib, keymap, keycode, 2)
                lvl3 = _read_key_level(lib, keymap, keycode, 3)

                if lvl0:
                    labels[key_event] = lvl0
                if lvl1 and lvl1 != lvl0:
                    shifted[key_event] = lvl1
                if lvl2 and lvl2 != lvl0:
                    altgr[key_event] = lvl2
                if lvl3 and lvl3 != lvl2 and lvl3 != lvl1:
                    altgr_shifted[key_event] = lvl3

            if not labels:
                return None

            return (labels, shifted, altgr, altgr_shifted)
        finally:
            lib.xkb_keymap_unref(keymap)
    finally:
        lib.xkb_context_unref(context)


def build_layout_from_xkb(xkb_layout, xkb_variant="", display_name=None):
    """Build a Vboard layout dictionary dynamically from the system XKB keymap."""
    if not xkb_layout:
        return None

    extracted = _extract_xkb_maps(xkb_layout, xkb_variant or "")
    if extracted is None:
        return None

    labels, shifted, altgr, altgr_shifted = extracted
    layout_id = make_dynamic_xkb_layout_id(xkb_layout, xkb_variant or "")
    if display_name:
        label = display_name
    elif xkb_variant:
        label = f"{xkb_layout.upper()} ({xkb_variant})"
    else:
        label = xkb_layout.upper()

    rows = (
        [list(row) for row in ISO_LAYOUT_ROWS]
        if xkb_layout in ISO_XKB_LAYOUTS
        else [list(row) for row in STANDARD_LAYOUT_ROWS]
    )

    return {
        "id": layout_id,
        "label": label,
        "short_label": xkb_layout[:3].upper(),
        "order": None,
        "xkb_layout": xkb_layout,
        "xkb_variant": xkb_variant or "",
        "rows": rows,
        "labels": dict(labels),
        "shifted": dict(shifted),
        "altgr": dict(altgr),
        "altgr_shifted": dict(altgr_shifted),
        "dynamic": True,
    }
