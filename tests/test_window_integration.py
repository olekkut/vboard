import os
import tempfile
import unittest
from unittest import mock

from vboard.constants import (
    COMPACT_TV_LAYER_ALPHA,
    COMPACT_TV_LAYER_NUMBERS,
    KEYBOARD_MODE_COMPACT_TV,
    TV_ACTION_LANG,
    TV_ACTION_LAYER_ALPHA,
    TV_ACTION_LAYER_NUMBERS,
)
from vboard.system_layouts import SystemLayoutController, SystemLayoutEntry
from vboard.window import VirtualKeyboard


class FakePlasmaBackend:
    name = "plasma"

    def __init__(self, entries, current_index=2):
        self.entries = list(entries)
        self.current_index = current_index
        self.on_changed = None

    def refresh(self):
        return list(self.entries)

    def get_layouts(self):
        return tuple(self.entries)

    def get_current_index(self):
        return self.current_index

    def set_layout_index(self, index):
        if 0 <= index < len(self.entries):
            self.current_index = index
            return True
        return False

    def emit_external_change(self, index):
        self.current_index = index
        if self.on_changed is not None:
            self.on_changed(self.entries[index])

    def close(self):
        return


class VirtualKeyboardIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.home_patch = mock.patch.dict(os.environ, {"HOME": self.temp_dir.name})
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)

        self.entries = [
            SystemLayoutEntry(0, "us", "", "English (US)"),
            SystemLayoutEntry(1, "pl", "", "Polish"),
            SystemLayoutEntry(2, "ua", "", "Ukrainian"),
            SystemLayoutEntry(3, "ru", "", "Russian"),
        ]
        self.fake_backend = FakePlasmaBackend(self.entries, current_index=2)

        def create_controller(keyboard_layouts, on_layout_changed=None):
            return SystemLayoutController(
                self.fake_backend,
                keyboard_layouts,
                on_layout_changed=on_layout_changed,
            )

        self.controller_patch = mock.patch.object(
            SystemLayoutController,
            "create",
            side_effect=create_controller,
        )
        self.controller_patch.start()
        self.addCleanup(self.controller_patch.stop)

        self.tray_patch = mock.patch.object(VirtualKeyboard, "create_tray_icon")
        self.tray_patch.start()
        self.addCleanup(self.tray_patch.stop)

        self.uinput_patch = mock.patch(
            "vboard.window.UInputBackend",
            side_effect=RuntimeError("headless test"),
        )
        self.uinput_patch.start()
        self.addCleanup(self.uinput_patch.stop)

        self.window = VirtualKeyboard()
        self.addCleanup(self.window.destroy)

    def test_startup_syncs_to_active_ukrainian_system_layout(self):
        self.assertEqual(self.window.keyboard_layout, "uk")
        self.assertEqual(self.window.layout_button.get_label(), "UA")
        self.assertEqual(self.window.key_buttons["Q"].get_label(), "й")
        self.assertEqual(self.window.key_buttons["S"].get_label(), "і")
        self.assertEqual(self.window.key_buttons["]"].get_label(), "ї")

    def test_external_system_layout_switch_updates_vboard_labels(self):
        self.fake_backend.emit_external_change(3)  # Russian
        self.assertEqual(self.window.keyboard_layout, "ru")
        self.assertEqual(self.window.layout_button.get_label(), "RU")
        self.assertEqual(self.window.key_buttons["S"].get_label(), "ы")

        self.fake_backend.emit_external_change(1)  # Polish
        self.assertEqual(self.window.keyboard_layout, "pl")
        self.assertEqual(self.window.layout_button.get_label(), "PL")
        self.assertEqual(self.window.key_buttons["Q"].get_label(), "q")

        # Toggle AltGr on Polish and verify diacritic labels appear on buttons
        self.window.update_modifier("Alt_R", True)
        self.window.update_key_labels()
        self.assertEqual(self.window.key_buttons["A"].get_label(), "ą")
        self.assertEqual(self.window.key_buttons["L"].get_label(), "ł")
        self.assertEqual(self.window.key_buttons["Z"].get_label(), "ż")

    def test_top_bar_cycle_switches_system_layout(self):
        # Currently index 2 (Ukrainian) -> cycle to 3 (Russian) -> 0 (English) -> 1 (Polish)
        self.window.cycle_keyboard_layout()
        self.assertEqual(self.fake_backend.current_index, 3)
        self.assertEqual(self.window.keyboard_layout, "ru")
        self.assertEqual(self.window.layout_button.get_label(), "RU")

        self.window.cycle_keyboard_layout()
        self.assertEqual(self.fake_backend.current_index, 0)
        self.assertEqual(self.window.keyboard_layout, "en")
        self.assertEqual(self.window.layout_button.get_label(), "EN")

        self.window.cycle_keyboard_layout()
        self.assertEqual(self.fake_backend.current_index, 1)
        self.assertEqual(self.window.keyboard_layout, "pl")
        self.assertEqual(self.window.layout_button.get_label(), "PL")

    def test_compact_tv_mode_and_high_contrast_tv_theme(self):
        self.window.style_variant = "high_contrast_tv"
        self.window.apply_css()

        self.window.set_keyboard_mode(KEYBOARD_MODE_COMPACT_TV)
        self.assertEqual(self.window.compact_tv_layer, COMPACT_TV_LAYER_ALPHA)
        self.assertEqual(self.window.key_buttons["Backspace"].get_label(), "⌫")
        self.assertEqual(self.window.key_buttons["Delete"].get_label(), "Del")
        self.assertEqual(self.window.key_buttons[TV_ACTION_LANG].get_label(), "UA")
        self.assertTrue(
            self.window.key_buttons[TV_ACTION_LAYER_ALPHA]
            .get_style_context()
            .has_class("active-layer")
        )

        # Switch to Numbers/Fn/Nav/Numpad layer
        self.window.set_compact_tv_layer(COMPACT_TV_LAYER_NUMBERS)
        self.assertIn("F12", self.window.key_buttons)
        self.assertIn("Home", self.window.key_buttons)
        self.assertIn("KP_Enter", self.window.key_buttons)
        self.assertTrue(
            self.window.key_buttons[TV_ACTION_LAYER_NUMBERS]
            .get_style_context()
            .has_class("active-layer")
        )

        # Resetting modifiers on layer 1 (where Shift_R is absent) must not raise
        self.window.modifiers["Shift_R"] = True
        self.window.reset_modifiers()
        self.assertFalse(self.window.modifiers["Shift_R"])


if __name__ == "__main__":
    unittest.main()
