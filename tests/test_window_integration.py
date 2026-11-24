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

    def test_russian_layout_shift_altgr_and_gestures(self):
        self.window.set_keyboard_layout("ru")
        self.assertEqual(self.fake_backend.current_index, 3)
        self.assertEqual(self.window.layout_button.get_label(), "RU")
        self.assertEqual(self.window.key_buttons["`"].get_label(), "ё")
        self.assertEqual(self.window.key_buttons["S"].get_label(), "ы")
        self.assertEqual(self.window.key_buttons["]"].get_label(), "ъ")
        self.assertEqual(self.window.key_buttons["'"].get_label(), "э")

        # Shift updates Russian letters and shifted punctuation (including \ -> / and / -> ,)
        self.window.update_modifier("Shift_L", True)
        self.window.update_key_labels()
        self.assertEqual(self.window.key_buttons["`"].get_label(), "Ё")
        self.assertEqual(self.window.key_buttons["S"].get_label(), "Ы")
        self.assertEqual(self.window.key_buttons["\\"].get_label(), "/")
        self.assertEqual(self.window.key_buttons["/"].get_label(), ",")
        self.window.reset_modifiers()

        # AltGr shows the ruble sign on key 8
        self.window.update_modifier("Alt_R", True)
        self.window.update_key_labels()
        self.assertEqual(self.window.key_buttons["8"].get_label(), "₽")
        self.window.reset_modifiers()

        # Character lookup resolves Cyrillic lowercase, uppercase, and ruble sign
        key_event, mods = self.window.character_to_key_event("ё")
        self.assertEqual((key_event, mods["Shift_L"], mods["Alt_R"]), ("`", False, False))
        key_event, mods = self.window.character_to_key_event("Ы")
        self.assertEqual((key_event, mods["Shift_L"], mods["Alt_R"]), ("S", True, False))
        key_event, mods = self.window.character_to_key_event("₽")
        self.assertEqual((key_event, mods["Shift_L"], mods["Alt_R"]), ("8", False, True))

        # Gesture typing resolves Cyrillic punctuation-key letters
        self.assertIsNotNone(self.window.gesture_controller)
        self.assertEqual(
            self.window.gesture_controller.key_event_to_active_gesture_char("["), "х"
        )
        self.assertEqual(
            self.window.gesture_controller.key_event_to_active_gesture_char("]"), "ъ"
        )
        self.assertEqual(
            self.window.gesture_controller.key_event_to_active_gesture_char(";"), "ж"
        )
        self.assertEqual(
            self.window.gesture_controller.key_event_to_active_gesture_char("'"), "э"
        )

    def test_top_bar_fast_switch_buttons_include_ru_ua_pl(self):
        labels = [btn.get_label() for btn, _lid, _entry in self.window.layout_buttons]
        self.assertEqual(labels, ["EN", "PL", "UA", "RU"])

        # Active button (UA at startup) has active-layout class
        ua_btn = next(btn for btn, lid, _ in self.window.layout_buttons if lid == "uk")
        ru_btn = next(btn for btn, lid, _ in self.window.layout_buttons if lid == "ru")
        pl_btn = next(btn for btn, lid, _ in self.window.layout_buttons if lid == "pl")
        self.assertTrue(ua_btn.get_style_context().has_class("active-layout"))
        self.assertFalse(ru_btn.get_style_context().has_class("active-layout"))

        # Direct one-click switch to RU updates both system backend and active highlight
        ru_entry = next(entry for _, lid, entry in self.window.layout_buttons if lid == "ru")
        self.window.select_system_layout_entry(ru_entry)
        self.assertEqual(self.fake_backend.current_index, 3)
        self.assertEqual(self.window.keyboard_layout, "ru")
        self.assertTrue(ru_btn.get_style_context().has_class("active-layout"))
        self.assertFalse(ua_btn.get_style_context().has_class("active-layout"))

        # Even if Plasma only has PL + UA configured (no RU in KDE System Settings):
        # 1. Switching to RU must glow ONLY RU (never UA + RU at once!)
        # 2. Cycling via the sidebar button under Hide must cycle PL -> UA -> RU -> PL
        self.fake_backend.entries = [
            SystemLayoutEntry(0, "pl", "", "Polish"),
            SystemLayoutEntry(1, "ua", "", "Ukrainian"),
        ]
        self.fake_backend.current_index = 1  # Plasma stuck on UA
        self.window.set_keyboard_mode(KEYBOARD_MODE_COMPACT_TV, save=False)
        self.window.set_keyboard_layout("uk", sync_system=False, save=False)
        self.window.rebuild_layout_buttons()

        labels_without_ru_in_plasma = [
            btn.get_label() for btn, _lid, _entry in self.window.layout_buttons
        ]
        self.assertEqual(labels_without_ru_in_plasma, ["PL", "UA", "RU"])

        # Switch to RU: ONLY RU glows; UA and PL must NOT glow
        self.window.activate_fast_switch_item("ru", None)
        glowing = [
            btn.get_label()
            for btn, _lid, _entry in self.window.layout_buttons
            if btn.get_style_context().has_class("active-layout")
        ]
        self.assertEqual(glowing, ["RU"])
        self.assertEqual(self.window.key_buttons[TV_ACTION_LANG].get_label(), "RU")

        # Cycle via the button under Hide: RU -> PL -> UA -> RU
        visited = []
        for _ in range(3):
            self.window.cycle_keyboard_layout()
            visited.append(self.window.key_buttons[TV_ACTION_LANG].get_label())
            glowing = [
                btn.get_label()
                for btn, _lid, _entry in self.window.layout_buttons
                if btn.get_style_context().has_class("active-layout")
            ]
            self.assertEqual(len(glowing), 1)
            self.assertEqual(glowing[0], visited[-1])
        self.assertEqual(visited, ["PL", "UA", "RU"])

    def test_status_notifier_dbus_xml_and_menu_serialization(self):
        from vboard.gtk import Gio, GLib
        from vboard.window import (
            DBUS_MENU_XML,
            STATUS_NOTIFIER_ITEM_XML,
            StatusNotifierTrayIcon,
        )

        sni_info = Gio.DBusNodeInfo.new_for_xml(STATUS_NOTIFIER_ITEM_XML)
        menu_info = Gio.DBusNodeInfo.new_for_xml(DBUS_MENU_XML)
        self.assertEqual(sni_info.interfaces[0].name, "org.kde.StatusNotifierItem")
        self.assertEqual(menu_info.interfaces[0].name, "com.canonical.dbusmenu")

        tray = StatusNotifierTrayIcon.__new__(StatusNotifierTrayIcon)
        tray.window = self.window
        tray.menu_revision = 1

        root_layout = tray.get_menu_layout(0)
        root_variant = GLib.Variant("(u(ia{sv}av))", (1, root_layout))
        self.assertEqual(root_variant.unpack()[1][0], 0)

        submenu_layout = tray.get_menu_layout(StatusNotifierTrayIcon.MENU_LAYOUT_ID)
        submenu_variant = GLib.Variant("(u(ia{sv}av))", (1, submenu_layout))
        self.assertEqual(submenu_variant.unpack()[1][0], StatusNotifierTrayIcon.MENU_LAYOUT_ID)
        self.assertGreaterEqual(len(submenu_variant.unpack()[1][2]), 3)

        group_variant = GLib.Variant(
            "(a(ia{sv}))",
            ([(1, tray.get_menu_properties(1)), (12, tray.get_menu_properties(12))],),
        )
        self.assertEqual(len(group_variant.unpack()[0]), 2)

    def test_toggle_visibility_preserves_collapsed_header_controls(self):
        self.window.show_all()
        self.window.change_visibility()
        self.assertFalse(self.window.color_combobox.get_visible())

        self.window.toggle_visibility()  # hide
        self.assertFalse(self.window.get_visible())
        self.window.toggle_visibility()  # show again
        self.assertTrue(self.window.get_visible())
        self.assertFalse(self.window.color_combobox.get_visible())

    def test_opacity_formatting_and_resilient_settings_read(self):
        self.window.opacity = "0.90"
        self.window.change_opacity(None, True)
        self.assertEqual(self.window.opacity, "0.91")
        self.window.change_opacity(None, False)
        self.assertEqual(self.window.opacity, "0.90")

        with open(self.window.CONFIG_FILE, "w", encoding="utf-8") as handle:
            handle.write("[DEFAULT]\nopacity = not_a_number\nwidth = bad\n")
        self.window.read_settings()
        self.assertEqual(self.window.opacity, "0.90")
        self.assertEqual(self.window.width, 0)

    def test_kwin_rule_installer_creates_missing_dir_and_preserves_position(self):
        import subprocess

        script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "scripts", "install-kwin-rule.sh")
        )
        with tempfile.TemporaryDirectory() as fake_home:
            env = dict(os.environ, HOME=fake_home, XDG_CONFIG_HOME=os.path.join(fake_home, ".config"))
            first = subprocess.run(
                ["bash", script_path, "--scope=user"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            rules_path = os.path.join(fake_home, ".config", "kwinrulesrc")
            self.assertTrue(os.path.isfile(rules_path))
            with open(rules_path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("wmclass=io.github.archisman-panigrahi.vboard", content)

            # Customize position and verify re-running preserves it and stays idempotent
            updated = content.replace("position=0,0", "position=120,340")
            with open(rules_path, "w", encoding="utf-8") as handle:
                handle.write(updated)
            second = subprocess.run(
                ["bash", script_path, "--scope=user"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(second.stdout.strip(), "")
            with open(rules_path, encoding="utf-8") as handle:
                self.assertIn("position=120,340", handle.read())

    def test_apple_themes_responsive_scaling_and_altgr_orange_hints(self):
        # Verify both Apple macOS themes load valid GTK3 CSS without errors
        for theme_label, expected_variant in (
            ("Apple macOS Dark", "apple_dark"),
            ("Apple macOS Light", "apple_light"),
        ):
            self.window.set_theme_by_label(theme_label, save=False)
            self.assertEqual(self.window.style_variant, expected_variant)
            self.assertEqual(self.window.get_active_theme_label(), theme_label)

        # Verify responsive font scaling reacts to font_scale & window sizing
        self.window.set_font_scale(0.80, save=False)
        small_font = self.window.key_font_size
        self.window.set_font_scale(1.50, save=False)
        large_font = self.window.key_font_size
        self.assertGreater(large_font, small_font)

        # Verify AltGr orange accent hints light up Polish diacritic keys
        self.window.set_keyboard_layout("pl", sync_system=False, save=False)
        self.window.update_modifier("Alt_R", True)
        self.assertTrue(
            self.window.key_buttons["A"].get_style_context().has_class("altgr-hint")
        )
        self.assertFalse(
            self.window.key_buttons["F"].get_style_context().has_class("altgr-hint")
        )
        self.window.update_modifier("Alt_R", False)
        self.assertFalse(
            self.window.key_buttons["A"].get_style_context().has_class("altgr-hint")
        )

    def test_sticky_modifier_lock_autocap_toolbars_dwell_fade_and_customize_dialog(self):
        from vboard.constants import INPUT_TRIGGER_RELEASE

        # Sticky double-tap modifier lock stays active after emit_key
        self.window.set_sticky_modifier_lock(True, save=False)
        self.window.toggle_modifier_key("Shift_L")  # 1st tap: one-shot
        self.assertTrue(self.window.modifiers["Shift_L"])
        self.assertFalse(self.window.locked_modifiers["Shift_L"])
        self.window.toggle_modifier_key("Shift_L")  # 2nd tap: locked
        self.assertTrue(self.window.locked_modifiers["Shift_L"])
        self.window.emit_key("A")
        self.assertTrue(self.window.modifiers["Shift_L"])  # remains locked!
        self.window.toggle_modifier_key("Shift_L")  # 3rd tap: unlock & off
        self.assertFalse(self.window.modifiers["Shift_L"])

        # Auto-capitalize after sentence + Current Text bar + Media row
        self.window.set_keyboard_layout("en", sync_system=False, save=False)
        self.window.set_show_current_text_bar(True, save=False)
        self.window.set_show_media_row(True, save=False)
        self.window.set_auto_capitalize(True, save=False)
        self.window.clear_current_text_buffer()
        self.window.emit_key("H")
        self.window.emit_key("I")
        self.window.emit_key(".")
        self.window.emit_key("Space")
        self.assertTrue(self.window.modifiers["Shift_L"])
        self.assertEqual(self.window.current_text_buffer, "hi. ")
        self.assertTrue(self.window.media_bar.get_visible())
        self.assertTrue(self.window.current_text_bar.get_visible())

        # Input trigger mode on release + inactivity fade + dwell trigger
        self.window.set_input_trigger_mode(INPUT_TRIGGER_RELEASE, save=False)
        self.window.set_fade_on_inactivity(True, save=False)
        self.window.set_inactivity_fade_opacity(0.30, save=False)
        self.window.set_faded_state(True)
        self.assertTrue(self.window._is_faded)
        self.window.reset_inactivity_timer()
        self.assertFalse(self.window._is_faded)

        emitted = []
        self.window.backend.emit_key = lambda key, mods: emitted.append(key)
        self.window.set_dwell_enabled(True, save=False)
        btn_a = self.window.key_buttons["A"]
        self.window.start_dwell_timer(btn_a, "A")
        self.window._on_dwell_timeout(btn_a, "A")
        self.assertIn("A", emitted)

        # Open & close 4-tab Customize Vboard dialog + settings round-trip
        self.window.set_key_corner_radius(12, save=False)
        self.window.set_key_spacing(5, save=False)
        self.window.set_accent_color("#FF9F0A", save=False)
        self.window.open_settings_dialog()
        self.assertIsNotNone(self.window.settings_dialog)
        self.window.settings_dialog.destroy()
        self.assertIsNone(self.window.settings_dialog)

        self.window.save_settings()
        self.window.key_corner_radius = 1
        self.window.accent_color = "#000000"
        self.window.read_settings()
        self.assertEqual(self.window.key_corner_radius, 12)
        self.assertEqual(self.window.key_spacing, 5)
        self.assertEqual(self.window.accent_color, "#FF9F0A")
        self.assertEqual(self.window.input_trigger_mode, INPUT_TRIGGER_RELEASE)
        self.assertTrue(self.window.show_media_row)
        self.assertTrue(self.window.show_current_text_bar)


if __name__ == "__main__":
    unittest.main()
