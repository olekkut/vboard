APP_DISPLAY_NAME = "Vboard"
APP_ID = "io.github.archisman-panigrahi.vboard"
VERSION = "2.7.4"

MODIFIER_KEYS = (
    "Shift_L",
    "Shift_R",
    "Ctrl_L",
    "Ctrl_R",
    "Alt_L",
    "Alt_R",
    "Super_L",
    "Super_R",
)

FUNCTION_KEYS = tuple(f"F{number}" for number in range(1, 13))

NAVIGATION_KEYS = (
    "Delete",
    "Insert",
    "Home",
    "End",
    "PageUp",
    "PageDown",
)

SYSTEM_KEYS = (
    "Print",
    "ScrollLock",
    "Pause",
)

NUMPAD_KEYS = (
    "NumLock",
    "KP_Divide",
    "KP_Multiply",
    "KP_Subtract",
    "KP_Add",
    "KP_Enter",
    "KP_Decimal",
    "KP_0",
    "KP_1",
    "KP_2",
    "KP_3",
    "KP_4",
    "KP_5",
    "KP_6",
    "KP_7",
    "KP_8",
    "KP_9",
)

DEFAULT_KEYBOARD_LAYOUT = "en"
QUICK_SWITCH_LAYOUTS = ("en", "pl", "uk", "ru")

KEYBOARD_MODE_STANDARD = "standard"
KEYBOARD_MODE_COMPACT_TV = "compact_tv"
KEYBOARD_MODE_CHOICES = (
    (KEYBOARD_MODE_STANDARD, "Standard"),
    (KEYBOARD_MODE_COMPACT_TV, "Compact for TV"),
)

COMPACT_TV_LAYER_ALPHA = "alpha"
COMPACT_TV_LAYER_NUMBERS = "numbers"

TV_ACTION_HIDE = "__tv_hide__"
TV_ACTION_LANG = "__tv_lang__"
TV_ACTION_LAYER_ALPHA = "__tv_layer_alpha__"
TV_ACTION_LAYER_NUMBERS = "__tv_layer_numbers__"
TV_ACTION_OPTIONS = "__tv_options__"
TV_ACTION_KEYS = frozenset(
    {
        TV_ACTION_HIDE,
        TV_ACTION_LANG,
        TV_ACTION_LAYER_ALPHA,
        TV_ACTION_LAYER_NUMBERS,
        TV_ACTION_OPTIONS,
    }
)

SPACER_KEY_PREFIX = "Spacer:"

COMMAND_MODIFIER_KEYS = (
    "Ctrl_L",
    "Ctrl_R",
    "Alt_L",
    "Alt_R",
    "Super_L",
    "Super_R",
)

ONBOARD_BACKGROUND_PRESET = "__onboard__"
HIGH_CONTRAST_TV_BACKGROUND_PRESET = "__high_contrast_tv__"
ENHANCED_BACKGROUND_PRESET = "__enhanced__"

COLOR_PRESETS = [
    ("Black", "0,0,0"),
    ("Red", "255,0,0"),
    ("Pink", "255,105,183"),
    ("White", "255,255,255"),
    ("Green", "0,255,0"),
    ("Blue", "0,0,110"),
    ("Gray", "128,128,128"),
    ("Dark Gray", "64,64,64"),
    ("Slate", "51,65,85"),
    ("Orange", "255,165,0"),
    ("Yellow", "255,255,0"),
    ("Purple", "128,0,128"),
    ("Cyan", "0,255,255"),
    ("Teal", "0,128,128"),
    ("Brown", "139,69,19"),
    ("Gold", "255,215,0"),
    ("Silver", "192,192,192"),
    ("Turquoise", "64,224,208"),
    ("Magenta", "255,0,255"),
    ("Olive", "128,128,0"),
    ("Maroon", "128,0,0"),
    ("Indigo", "75,0,130"),
    ("Beige", "245,245,220"),
    ("Lavender", "230,230,250"),
]

COLOR_CHOICES = [
    ("Onboard Droid Theme", ONBOARD_BACKGROUND_PRESET),
    ("High Contrast TV", HIGH_CONTRAST_TV_BACKGROUND_PRESET),
    *[
        (f"Enhanced {label}", (ENHANCED_BACKGROUND_PRESET, color))
        for label, color in COLOR_PRESETS
    ],
    *COLOR_PRESETS,
]

LIGHT_BACKGROUND_COLORS = {
    "255,255,255",
    "0,255,0",
    "255,255,0",
    "245,245,220",
    "230,230,250",
    "255,215,0",
}

KEY_WIDTHS = {
    "Space": 12,
    "CapsLock": 3,
    "Shift_R": 2,
    "Shift_L": 2,
    "Backspace": 5,
    "`": 1,
    "\\": 4,
    "Enter": 5,
    "<": 2,
}

SUPPORTED_WORD_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'-")
SUPPORTED_WORD_CONNECTORS = {"'", "\u2019", "\u02bc", "-"}
SUGGESTION_LIMIT = 5
