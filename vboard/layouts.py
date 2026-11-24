import json
import os

from .constants import (
    DEFAULT_KEYBOARD_LAYOUT,
    TV_ACTION_HIDE,
    TV_ACTION_LANG,
    TV_ACTION_LAYER_ALPHA,
    TV_ACTION_LAYER_NUMBERS,
    TV_ACTION_OPTIONS,
)


SYSTEM_LAYOUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "layouts")
USER_LAYOUT_DIR = os.path.expanduser("~/.config/vboard/layouts")
REQUIRED_LAYOUT_FIELDS = ("id", "label", "rows")
LAYOUT_SHORT_LABELS = {
    "ar": "AR",
    "de": "DE",
    "en": "EN",
    "fr": "FR",
    "pl": "PL",
    "ru": "RU",
    "sv": "SV",
    "uk": "UA",
}

STANDARD_LAYOUT_ROWS = [
    ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Backspace"],
    ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
    ["CapsLock", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter"],
    ["Shift_L", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Shift_R", "↑"],
    ["Ctrl_L", "Super_L", "Alt_L", "Space", "Alt_R", "Super_R", "Ctrl_R", "←", "↓", "→"],
]

ISO_LAYOUT_ROWS = [
    ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Backspace"],
    ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
    ["CapsLock", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter"],
    ["Shift_L", "<", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Shift_R", "↑"],
    ["Ctrl_L", "Super_L", "Alt_L", "Space", "Alt_R", "Super_R", "Ctrl_R", "←", "↓", "→"],
]


def get_layout_directories(user_layout_dir=USER_LAYOUT_DIR):
    return (SYSTEM_LAYOUT_DIR, user_layout_dir)


def load_keyboard_layouts(user_layout_dir=USER_LAYOUT_DIR):
    layouts = {}
    for layout_dir in get_layout_directories(user_layout_dir):
        if not os.path.isdir(layout_dir):
            continue

        for filename in sorted(os.listdir(layout_dir)):
            if not filename.endswith(".json"):
                continue

            path = os.path.join(layout_dir, filename)
            try:
                layout = load_keyboard_layout(path)
            except (OSError, ValueError) as exc:
                print(f"Warning: Could not load keyboard layout {path} ({exc}).")
                continue

            layouts[layout["id"]] = layout

    if not layouts:
        searched_dirs = ", ".join(get_layout_directories(user_layout_dir))
        raise RuntimeError(f"No keyboard layouts found. Checked: {searched_dirs}")

    return layouts


def load_keyboard_layout(path):
    with open(path, "r", encoding="utf-8") as layout_file:
        layout = json.load(layout_file)

    validate_keyboard_layout(layout, path)
    return {
        "id": layout["id"],
        "label": layout["label"],
        "short_label": layout.get("short_label"),
        "order": layout.get("order"),
        "xkb_layout": layout.get("xkb_layout"),
        "xkb_variant": layout.get("xkb_variant", ""),
        "rows": layout["rows"],
        "labels": layout.get("labels", {}),
        "shifted": layout.get("shifted", {}),
        "altgr": layout.get("altgr", {}),
        "altgr_shifted": layout.get("altgr_shifted", {}),
    }


def validate_keyboard_layout(layout, path):
    if not isinstance(layout, dict):
        raise ValueError("layout must be a JSON object")

    for field in REQUIRED_LAYOUT_FIELDS:
        if field not in layout:
            raise ValueError(f"missing required field: {field}")

    if not isinstance(layout["id"], str) or not layout["id"]:
        raise ValueError("id must be a non-empty string")
    if not isinstance(layout["label"], str) or not layout["label"]:
        raise ValueError("label must be a non-empty string")
    if not isinstance(layout["rows"], list) or not layout["rows"]:
        raise ValueError("rows must be a non-empty list")
    if "order" in layout and not isinstance(layout["order"], int):
        raise ValueError("order must be an integer")
    for str_field in ("short_label", "xkb_layout", "xkb_variant"):
        if str_field in layout and not isinstance(layout[str_field], str):
            raise ValueError(f"{str_field} must be a string")

    for row in layout["rows"]:
        if not isinstance(row, list) or not row:
            raise ValueError("each row must be a non-empty list")
        for key in row:
            if not isinstance(key, str) or not key:
                raise ValueError("each key must be a non-empty string")

    for field in ("labels", "shifted", "altgr", "altgr_shifted"):
        if field not in layout:
            continue
        if not isinstance(layout[field], dict):
            raise ValueError(f"{field} must be an object")
        for key, value in layout[field].items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(f"{field} keys and values must be strings")


def get_layout_choices(layouts):
    choices = []
    for layout_id, layout in layouts.items():
        if layout.get("dynamic"):
            continue
        choices.append((layout_id, layout["label"], layout.get("order")))
    sorted_choices = sorted(choices, key=get_layout_choice_sort_key)
    return tuple((layout_id, label) for layout_id, label, _order in sorted_choices)


def get_layout_choice_sort_key(choice):
    layout_id, label, order = choice
    if isinstance(order, int):
        return (0, order, label.lower(), layout_id)
    if layout_id == DEFAULT_KEYBOARD_LAYOUT:
        return (1, 0, "", "")
    return (1, 1, label.lower(), layout_id)


def get_default_layout_key(layouts):
    if DEFAULT_KEYBOARD_LAYOUT in layouts:
        return DEFAULT_KEYBOARD_LAYOUT
    return next(iter(layouts))


def get_layout_short_label(layout_id, layouts=None):
    if layouts and layout_id in layouts:
        explicit = layouts[layout_id].get("short_label")
        if explicit:
            return explicit.upper()
        xkb_layout = layouts[layout_id].get("xkb_layout")
        if xkb_layout:
            return xkb_layout.split("(", 1)[0][:3].upper()
    if layout_id in LAYOUT_SHORT_LABELS:
        return LAYOUT_SHORT_LABELS[layout_id]
    if layout_id.startswith("xkb:"):
        xkb_part = layout_id.split(":", 2)[1]
        if xkb_part:
            return xkb_part[:3].upper()
    cleaned = layout_id.split("_", 1)[0].split("-", 1)[0]
    if cleaned.isascii() and cleaned.isalpha() and 2 <= len(cleaned) <= 3:
        return cleaned.upper()
    return layout_id[:3].upper()


def _compact_tv_sidebar_cells():
    return (
        (TV_ACTION_HIDE, 30, 0, 3, 1),
        (TV_ACTION_LANG, 30, 1, 3, 1),
        (TV_ACTION_LAYER_ALPHA, 30, 2, 3, 1),
        (TV_ACTION_LAYER_NUMBERS, 30, 3, 3, 1),
        (TV_ACTION_OPTIONS, 30, 4, 3, 1),
    )


def build_compact_tv_alpha_cells(layout_config):
    """Build grid cells matching Onboard's Compact-for-TV Alpha layer (33 cols x 5 rows)."""
    has_iso_key = any("<" in row for row in layout_config.get("rows", ()))
    rows_spec = (
        (
            ("`", 2),
            ("1", 2),
            ("2", 2),
            ("3", 2),
            ("4", 2),
            ("5", 2),
            ("6", 2),
            ("7", 2),
            ("8", 2),
            ("9", 2),
            ("0", 2),
            ("-", 2),
            ("=", 2),
            ("Backspace", 2),
            ("Delete", 2),
        ),
        (
            ("Tab", 3),
            ("Q", 2),
            ("W", 2),
            ("E", 2),
            ("R", 2),
            ("T", 2),
            ("Y", 2),
            ("U", 2),
            ("I", 2),
            ("O", 2),
            ("P", 2),
            ("[", 2),
            ("]", 2),
            ("\\", 3),
        ),
        (
            ("CapsLock", 4),
            ("A", 2),
            ("S", 2),
            ("D", 2),
            ("F", 2),
            ("G", 2),
            ("H", 2),
            ("J", 2),
            ("K", 2),
            ("L", 2),
            (";", 2),
            ("'", 2),
            ("Enter", 4),
        ),
        (
            (("Shift_L", 3), ("<", 2)) if has_iso_key else (("Shift_L", 4),)
        )
        + (
            ("Z", 2),
            ("X", 2),
            ("C", 2),
            ("V", 2),
            ("B", 2),
            ("N", 2),
            ("M", 2),
            (",", 2),
            (".", 2),
            ("/", 2),
            ("Shift_R", 5 if has_iso_key else 6),
        ),
        (
            ("Ctrl_L", 3),
            ("Super_L", 3),
            ("Alt_L", 3),
            ("Space", 10),
            ("Alt_R", 3),
            ("←", 2),
            ("→", 2),
            ("↑", 2),
            ("↓", 2),
        ),
    )

    cells = []
    for row_index, row_keys in enumerate(rows_spec):
        col = 0
        for key_event, width in row_keys:
            cells.append((key_event, col, row_index, width, 1))
            col += width

    cells.extend(_compact_tv_sidebar_cells())
    return cells


def build_compact_tv_numbers_cells():
    """Build grid cells matching Onboard's Compact-for-TV Numbers/Fn layer (33 cols x 5 rows)."""
    cells = [
        # Row 0: Esc, F1-F6 | Ins Home PgUp | NumLock / * -
        ("Esc", 0, 0, 2, 1),
        ("F1", 2, 0, 2, 1),
        ("F2", 4, 0, 2, 1),
        ("F3", 6, 0, 2, 1),
        ("F4", 8, 0, 2, 1),
        ("F5", 10, 0, 2, 1),
        ("F6", 12, 0, 2, 1),
        ("Spacer:1", 14, 0, 1, 1),
        ("Insert", 15, 0, 2, 1),
        ("Home", 17, 0, 2, 1),
        ("PageUp", 19, 0, 2, 1),
        ("Spacer:1", 21, 0, 1, 1),
        ("NumLock", 22, 0, 2, 1),
        ("KP_Divide", 24, 0, 2, 1),
        ("KP_Multiply", 26, 0, 2, 1),
        ("KP_Subtract", 28, 0, 2, 1),
        # Row 1: F7-F12 | Del End PgDn | 7 8 9 + (rowspan 2)
        ("Spacer:2", 0, 1, 2, 1),
        ("F7", 2, 1, 2, 1),
        ("F8", 4, 1, 2, 1),
        ("F9", 6, 1, 2, 1),
        ("F10", 8, 1, 2, 1),
        ("F11", 10, 1, 2, 1),
        ("F12", 12, 1, 2, 1),
        ("Spacer:1", 14, 1, 1, 1),
        ("Delete", 15, 1, 2, 1),
        ("End", 17, 1, 2, 1),
        ("PageDown", 19, 1, 2, 1),
        ("Spacer:1", 21, 1, 1, 1),
        ("KP_7", 22, 1, 2, 1),
        ("KP_8", 24, 1, 2, 1),
        ("KP_9", 26, 1, 2, 1),
        ("KP_Add", 28, 1, 2, 2),
        # Row 2: Spacer | 4 5 6 (+ continues)
        ("Spacer:22", 0, 2, 22, 1),
        ("KP_4", 22, 2, 2, 1),
        ("KP_5", 24, 2, 2, 1),
        ("KP_6", 26, 2, 2, 1),
        # Row 3: PrtSc Scroll Pause | Up | 1 2 3 Enter (rowspan 2)
        ("Spacer:4", 0, 3, 4, 1),
        ("Print", 4, 3, 3, 1),
        ("ScrollLock", 7, 3, 3, 1),
        ("Pause", 10, 3, 3, 1),
        ("Spacer:4", 13, 3, 4, 1),
        ("↑", 17, 3, 2, 1),
        ("Spacer:3", 19, 3, 3, 1),
        ("KP_1", 22, 3, 2, 1),
        ("KP_2", 24, 3, 2, 1),
        ("KP_3", 26, 3, 2, 1),
        ("KP_Enter", 28, 3, 2, 2),
        # Row 4: Modifiers (for Alt+F4 / Ctrl+Home on TV) | Left Down Right | 0 . (Enter continues)
        ("Ctrl_L", 0, 4, 3, 1),
        ("Super_L", 3, 4, 3, 1),
        ("Alt_L", 6, 4, 3, 1),
        ("Shift_L", 9, 4, 3, 1),
        ("Spacer:3", 12, 4, 3, 1),
        ("←", 15, 4, 2, 1),
        ("↓", 17, 4, 2, 1),
        ("→", 19, 4, 2, 1),
        ("Spacer:1", 21, 4, 1, 1),
        ("KP_0", 22, 4, 4, 1),
        ("KP_Decimal", 26, 4, 2, 1),
    ]
    cells.extend(_compact_tv_sidebar_cells())
    return cells
