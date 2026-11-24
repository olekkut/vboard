import unittest

from vboard.constants import (
    TV_ACTION_HIDE,
    TV_ACTION_LANG,
    TV_ACTION_LAYER_ALPHA,
    TV_ACTION_LAYER_NUMBERS,
    TV_ACTION_OPTIONS,
)
from vboard.layouts import (
    build_compact_tv_alpha_cells,
    build_compact_tv_numbers_cells,
    get_layout_short_label,
    load_keyboard_layouts,
)


def assert_exact_grid_tiling(test_case, cells, expected_cols=33, expected_rows=5):
    occupied = set()
    for key_event, col, row, width, height in cells:
        test_case.assertGreater(width, 0, f"Non-positive width for {key_event}")
        test_case.assertGreater(height, 0, f"Non-positive height for {key_event}")
        for r in range(row, row + height):
            for c in range(col, col + width):
                test_case.assertNotIn(
                    (c, r),
                    occupied,
                    f"Overlap at ({c}, {r}) for {key_event}",
                )
                occupied.add((c, r))
    expected = {(c, r) for r in range(expected_rows) for c in range(expected_cols)}
    test_case.assertEqual(occupied, expected)


class LayoutsTest(unittest.TestCase):
    def setUp(self):
        self.layouts = load_keyboard_layouts(user_layout_dir="/nonexistent")

    def test_bundled_layouts_include_ukrainian_and_polish(self):
        for layout_id in ("en", "uk", "pl", "ru", "de", "fr", "sv"):
            self.assertIn(layout_id, self.layouts)

    def test_ukrainian_jcuken_mapping(self):
        uk = self.layouts["uk"]
        self.assertEqual(uk["label"], "Ukrainian")
        self.assertEqual(get_layout_short_label("uk", self.layouts), "UA")
        self.assertEqual(uk["labels"]["Q"], "й")
        self.assertEqual(uk["labels"]["S"], "і")
        self.assertEqual(uk["labels"]["]"], "ї")
        self.assertEqual(uk["labels"]["\\"], "ґ")
        self.assertEqual(uk["labels"]["'"], "є")
        self.assertEqual(uk["labels"]["`"], "'")
        self.assertEqual(uk["shifted"]["`"], "ʼ")
        self.assertEqual(uk["shifted"]["/"], ",")
        self.assertEqual(uk["altgr_shifted"]["3"], "₴")

    def test_polish_altgr_diacritics(self):
        pl = self.layouts["pl"]
        self.assertEqual(pl["label"], "Polish")
        self.assertEqual(get_layout_short_label("pl", self.layouts), "PL")
        expected_altgr = {
            "A": "ą",
            "C": "ć",
            "E": "ę",
            "L": "ł",
            "N": "ń",
            "O": "ó",
            "S": "ś",
            "X": "ź",
            "Z": "ż",
        }
        for key, char in expected_altgr.items():
            self.assertEqual(pl["altgr"][key], char)
            self.assertEqual(pl["altgr_shifted"][key], char.upper())

    def test_russian_jcuken_mapping(self):
        ru = self.layouts["ru"]
        self.assertEqual(ru["label"], "Russian")
        self.assertEqual(get_layout_short_label("ru", self.layouts), "RU")
        self.assertEqual(ru["xkb_layout"], "ru")
        self.assertEqual(ru["labels"]["`"], "ё")
        self.assertEqual(ru["labels"]["Q"], "й")
        self.assertEqual(ru["labels"]["S"], "ы")
        self.assertEqual(ru["labels"]["]"], "ъ")
        self.assertEqual(ru["labels"]["'"], "э")
        self.assertEqual(ru["labels"]["/"], ".")
        self.assertEqual(ru["shifted"]["`"], "Ё")
        self.assertEqual(ru["shifted"]["Q"], "Й")
        self.assertEqual(ru["shifted"]["S"], "Ы")
        self.assertEqual(ru["shifted"]["]"], "Ъ")
        self.assertEqual(ru["shifted"]["\\"], "/")
        self.assertEqual(ru["shifted"]["/"], ",")
        self.assertEqual(ru["altgr"]["8"], "₽")

    def test_compact_tv_alpha_tiles_exact_grid_ansi_and_iso(self):
        ansi_cells = build_compact_tv_alpha_cells(self.layouts["uk"])
        assert_exact_grid_tiling(self, ansi_cells, expected_cols=33, expected_rows=5)
        ansi_keys = {cell[0] for cell in ansi_cells}
        self.assertIn("Delete", ansi_keys)
        self.assertIn("Backspace", ansi_keys)
        self.assertNotIn("<", ansi_keys)
        for sidebar_key in (
            TV_ACTION_HIDE,
            TV_ACTION_LANG,
            TV_ACTION_LAYER_ALPHA,
            TV_ACTION_LAYER_NUMBERS,
            TV_ACTION_OPTIONS,
        ):
            self.assertIn(sidebar_key, ansi_keys)

        iso_cells = build_compact_tv_alpha_cells(self.layouts["sv"])
        assert_exact_grid_tiling(self, iso_cells, expected_cols=33, expected_rows=5)
        self.assertIn("<", {cell[0] for cell in iso_cells})

    def test_compact_tv_numbers_tiles_exact_grid(self):
        numbers_cells = build_compact_tv_numbers_cells()
        assert_exact_grid_tiling(self, numbers_cells, expected_cols=33, expected_rows=5)
        numbers_keys = {cell[0] for cell in numbers_cells}
        for key in (
            "Esc",
            "F1",
            "F12",
            "Insert",
            "Delete",
            "Home",
            "End",
            "PageUp",
            "PageDown",
            "Print",
            "ScrollLock",
            "Pause",
            "NumLock",
            "KP_0",
            "KP_9",
            "KP_Add",
            "KP_Enter",
            "KP_Decimal",
        ):
            self.assertIn(key, numbers_keys)


if __name__ == "__main__":
    unittest.main()
