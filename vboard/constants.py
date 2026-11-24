APP_DISPLAY_NAME = "Vboard"
APP_ID = "io.github.archisman-panigrahi.vboard"
VERSION = "2.9.0"

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

MEDIA_KEYS = (
    "VolumeMute",
    "VolumeDown",
    "VolumeUp",
    "PreviousSong",
    "PlayPause",
    "NextSong",
    "BrightnessDown",
    "BrightnessUp",
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

MAX_KEY_HOLD_SECONDS = 5.0

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

GRAPHITE_DARK_BACKGROUND_PRESET = "__graphite_dark__"
FROST_LIGHT_BACKGROUND_PRESET = "__frost_light__"
ONBOARD_BACKGROUND_PRESET = "__onboard__"
HIGH_CONTRAST_TV_BACKGROUND_PRESET = "__high_contrast_tv__"
ENHANCED_BACKGROUND_PRESET = "__enhanced__"

ACCENT_COLOR_CHOICES = (
    ("Cobalt Blue", "#0A84FF"),
    ("Sky Blue", "#007AFF"),
    ("Amber Orange", "#FF9F0A"),
    ("Emerald Green", "#30D158"),
    ("Violet", "#BF5AF2"),
    ("Rose Pink", "#FF375F"),
    ("Teal", "#00CACB"),
)

FONT_WEIGHT_CHOICES = (
    ("400", "Regular (400)"),
    ("500", "Medium (500)"),
    ("600", "Semi-Bold (600)"),
    ("700", "Bold (700)"),
)

DEFAULT_ACCENT_COLOR = "#0A84FF"
DEFAULT_FONT_SCALE = 1.0
DEFAULT_FONT_WEIGHT = "500"
DEFAULT_KEY_RADIUS = 8
DEFAULT_KEY_SPACING = 3
DEFAULT_KEY_BORDER_WIDTH = 1
DEFAULT_WINDOW_BORDER_WIDTH = 2
DEFAULT_WINDOW_BORDER_COLOR = "#FFFFFF"
DEFAULT_KEY_SHADOW_ENABLED = True
DEFAULT_CUSTOM_WINDOW_BG = "#1E1E22"
DEFAULT_CUSTOM_KEY_BG = "#4A4A50"
DEFAULT_CUSTOM_MODIFIER_BG = "#323238"
DEFAULT_CUSTOM_TEXT_COLOR = "#F5F5F7"
DEFAULT_CUSTOM_KEY_BORDER_COLOR = "#64646C"
DEFAULT_INACTIVITY_DELAY_SECONDS = 10
DEFAULT_INACTIVITY_FADE_OPACITY = 0.25
DEFAULT_DWELL_TIME_MS = 800

INPUT_TRIGGER_PRESS = "press"
INPUT_TRIGGER_RELEASE = "release"
INPUT_TRIGGER_CHOICES = (
    (INPUT_TRIGGER_PRESS, "On Press (Mouse Down)"),
    (INPUT_TRIGGER_RELEASE, "On Release (Mouse Up)"),
)

COLOR_PRESETS = [
    ("Midnight", "18,24,33"),
    ("Charcoal", "44,44,48"),
    ("Slate", "51,65,85"),
    ("Teal", "0,110,115"),
    ("Indigo", "62,40,112"),
    ("Lavender", "230,230,250"),
    ("Black", "0,0,0"),
    ("White", "255,255,255"),
]

COLOR_CHOICES = [
    ("Graphite Dark", GRAPHITE_DARK_BACKGROUND_PRESET),
    ("Frost Light", FROST_LIGHT_BACKGROUND_PRESET),
    ("Onboard Droid", ONBOARD_BACKGROUND_PRESET),
    ("High Contrast TV", HIGH_CONTRAST_TV_BACKGROUND_PRESET),
    ("Enhanced Midnight", (ENHANCED_BACKGROUND_PRESET, "18,24,33")),
    ("Enhanced Charcoal", (ENHANCED_BACKGROUND_PRESET, "44,44,48")),
    ("Enhanced Slate", (ENHANCED_BACKGROUND_PRESET, "51,65,85")),
    ("Enhanced Teal", (ENHANCED_BACKGROUND_PRESET, "0,110,115")),
    ("Enhanced Indigo", (ENHANCED_BACKGROUND_PRESET, "62,40,112")),
    ("Enhanced Lavender", (ENHANCED_BACKGROUND_PRESET, "230,230,250")),
    ("Classic Black", "0,0,0"),
    ("Classic White", "255,255,255"),
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
