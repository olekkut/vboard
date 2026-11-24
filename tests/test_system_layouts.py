import unittest
from types import SimpleNamespace
from unittest import mock

from vboard.constants import MODIFIER_KEYS
from vboard.layouts import load_keyboard_layouts
from vboard.system_layouts import (
    PlasmaLayoutBackend,
    SystemLayoutController,
    SystemLayoutEntry,
    parse_xkb_spec,
    resolve_system_entry_to_vboard_layout,
)
from vboard.window import VirtualKeyboard
from vboard.xkb_layouts import build_layout_from_xkb


class FakeSystemBackend:
    name = "fake-plasma"

    def __init__(self, entries, current_index=0):
        self.entries = list(entries)
        self.current_index = current_index
        self.on_changed = None
        self.set_calls = []

    def refresh(self):
        return list(self.entries)

    def get_layouts(self):
        return tuple(self.entries)

    def get_current_index(self):
        return self.current_index

    def set_layout_index(self, index):
        if index < 0 or index >= len(self.entries):
            return False
        self.current_index = index
        self.set_calls.append(index)
        return True

    def trigger_external_change(self, index):
        self.current_index = index
        if self.on_changed is not None:
            self.on_changed(self.entries[index])

    def close(self):
        return


class XkbDynamicLayoutTest(unittest.TestCase):
    def test_parse_xkb_spec(self):
        self.assertEqual(parse_xkb_spec("us(dvorak)"), ("us", "dvorak"))
        self.assertEqual(parse_xkb_spec("us+dvorak"), ("us", "dvorak"))
        self.assertEqual(parse_xkb_spec("ua", "legacy"), ("ua", "legacy"))

    def test_builds_dynamic_layout_for_variant_and_unbundled_language(self):
        dvorak = build_layout_from_xkb("us", "dvorak", display_name="English (Dvorak)")
        self.assertIsNotNone(dvorak)
        self.assertEqual(dvorak["id"], "xkb:us:dvorak")
        self.assertEqual(dvorak["labels"]["A"], "a")
        self.assertEqual(dvorak["labels"]["S"], "o")
        self.assertEqual(dvorak["labels"]["E"], ".")

        czech = build_layout_from_xkb("cz", "", display_name="Czech")
        self.assertIsNotNone(czech)
        self.assertEqual(czech["id"], "xkb:cz")
        self.assertEqual(czech["labels"]["Z"], "y")
        self.assertEqual(czech["labels"]["["], "ú")


class SystemLayoutSyncTest(unittest.TestCase):
    def setUp(self):
        self.layouts = load_keyboard_layouts(user_layout_dir="/nonexistent")
        self.entries = [
            SystemLayoutEntry(0, "us", "", "English (US)"),
            SystemLayoutEntry(1, "pl", "", "Polish"),
            SystemLayoutEntry(2, "ua", "", "Ukrainian"),
            SystemLayoutEntry(3, "ru", "", "Russian"),
            SystemLayoutEntry(4, "cz", "", "Czech"),
        ]

    def test_system_change_from_russian_to_polish_and_ukrainian_and_czech(self):
        backend = FakeSystemBackend(self.entries, current_index=3)
        received = []
        controller = SystemLayoutController(
            backend,
            self.layouts,
            on_layout_changed=lambda layout_id, entry: received.append(layout_id),
        )

        self.assertEqual(controller.get_current_vboard_layout(), "ru")

        backend.trigger_external_change(1)  # Polish
        backend.trigger_external_change(2)  # Ukrainian
        backend.trigger_external_change(4)  # Czech (dynamic XKB)
        backend.trigger_external_change(0)  # English

        self.assertEqual(received, ["pl", "uk", "xkb:cz", "en"])
        self.assertIn("xkb:cz", self.layouts)

    def test_cycle_next_layout_cycles_all_system_layouts(self):
        backend = FakeSystemBackend(self.entries[:4], current_index=0)
        controller = SystemLayoutController(backend, self.layouts)

        visited = []
        for _ in range(4):
            _entry, layout_id = controller.cycle_next_layout()
            visited.append(layout_id)

        self.assertEqual(visited, ["pl", "uk", "ru", "en"])
        self.assertEqual(backend.set_calls, [1, 2, 3, 0])

    def test_set_vboard_layout_switches_system_layout(self):
        backend = FakeSystemBackend(self.entries[:4], current_index=0)
        controller = SystemLayoutController(backend, self.layouts)

        self.assertTrue(controller.set_vboard_layout("uk"))
        self.assertEqual(backend.current_index, 2)
        self.assertTrue(controller.set_vboard_layout("pl"))
        self.assertEqual(backend.current_index, 1)
        self.assertFalse(controller.set_vboard_layout("fr"))

    def test_switching_to_layout_missing_from_system_still_updates_vboard(self):
        backend = FakeSystemBackend(self.entries[:2], current_index=0)
        controller = SystemLayoutController(backend, self.layouts)
        keyboard = SimpleNamespace(
            keyboard_layout="en",
            keyboard_layouts=self.layouts,
            sync_system_layout=True,
            system_layout_controller=controller,
            suggestion_engine=mock.Mock(),
            gesture_controller=None,
            text_prediction_enabled=False,
            current_word="old",
            normalize_keyboard_layout=lambda key: key,
            refresh_layout_character_lookup=mock.Mock(),
            rebuild_keyboard_grid=mock.Mock(),
            clear_suggestion_override=mock.Mock(),
            update_suggestions=mock.Mock(),
            update_layout_button=mock.Mock(),
            sync_tray_items=mock.Mock(),
            sync_settings_dialog_controls=mock.Mock(),
            save_settings=mock.Mock(),
        )

        with mock.patch("builtins.print") as print_mock:
            VirtualKeyboard.set_keyboard_layout(keyboard, "uk")

        self.assertEqual(keyboard.keyboard_layout, "uk")
        keyboard.suggestion_engine.set_layout.assert_called_once_with("uk")
        keyboard.rebuild_keyboard_grid.assert_called_once_with()
        keyboard.save_settings.assert_called_once_with()
        self.assertTrue(print_mock.called)

    def test_plasma_backend_dbus_signals_and_methods(self):
        class FakeVariant:
            def __init__(self, value):
                self._value = value

            def unpack(self):
                return self._value

        class FakeProxy:
            def __init__(self):
                self.callbacks = {}
                self.calls = []
                self.active_index = 2

            def call_sync(self, method, params, _flags, _timeout, _cancellable):
                self.calls.append((method, params))
                if method == "getLayoutsList":
                    return FakeVariant(
                        (
                            [
                                ("us", "", "English (US)"),
                                ("pl", "", "Polish"),
                                ("ua", "", "Ukrainian"),
                            ],
                        )
                    )
                if method == "getLayout":
                    return FakeVariant((self.active_index,))
                if method == "setLayout":
                    self.active_index = int(params.unpack()[0])
                    return FakeVariant((True,))
                raise AssertionError(f"Unexpected D-Bus method: {method}")

            def connect(self, signal, callback):
                self.callbacks[signal] = callback
                return 42

            def disconnect(self, handler_id):
                self.callbacks.clear()

        fake_proxy = FakeProxy()
        observed = []

        with mock.patch(
            "vboard.system_layouts.Gio.DBusProxy.new_for_bus_sync",
            return_value=fake_proxy,
        ):
            backend = PlasmaLayoutBackend(on_changed=lambda entry: observed.append(entry))
            self.assertEqual(backend.get_current_index(), 2)
            self.assertTrue(backend.set_layout_index(1))
            self.assertEqual(backend.get_current_index(), 1)

            fake_proxy.callbacks["g-signal"](
                fake_proxy, None, "layoutChanged", FakeVariant((2,))
            )
            self.assertEqual(len(observed), 1)
            self.assertEqual(observed[0].xkb_layout, "ua")
            backend.close()

    def test_polish_altgr_labels_and_character_lookup(self):
        keyboard = SimpleNamespace(
            keyboard_layout="pl",
            keyboard_layouts=self.layouts,
            keyboard_mode="standard",
            modifiers={mod: False for mod in MODIFIER_KEYS},
            caps_lock_active=False,
            layout_character_lookup={},
        )
        keyboard.get_layout_config = lambda: self.layouts["pl"]
        keyboard.get_active_key_rows = lambda: self.layouts["pl"]["rows"]
        keyboard.get_active_key_labels = lambda: self.layouts["pl"]["labels"]
        keyboard.get_active_shifted_map = lambda: self.layouts["pl"]["shifted"]
        keyboard.get_active_altgr_map = lambda: self.layouts["pl"]["altgr"]
        keyboard.get_active_altgr_shifted_map = lambda: self.layouts["pl"]["altgr_shifted"]

        VirtualKeyboard.refresh_layout_character_lookup(keyboard)

        # Normal label
        self.assertEqual(VirtualKeyboard.get_button_label(keyboard, "A"), "a")
        # AltGr label
        keyboard.modifiers["Alt_R"] = True
        self.assertEqual(VirtualKeyboard.get_button_label(keyboard, "A"), "ą")
        self.assertEqual(VirtualKeyboard.get_button_label(keyboard, "L"), "ł")
        self.assertEqual(VirtualKeyboard.get_button_label(keyboard, "Z"), "ż")
        # Shift + AltGr label
        keyboard.modifiers["Shift_L"] = True
        self.assertEqual(VirtualKeyboard.get_button_label(keyboard, "L"), "Ł")

        # Lookup for word completion / emit_text
        key_event, mods = VirtualKeyboard.character_to_key_event(keyboard, "ę")
        self.assertEqual(key_event, "E")
        self.assertTrue(mods["Alt_R"])
        self.assertFalse(mods["Shift_L"])

        key_event_upper, mods_upper = VirtualKeyboard.character_to_key_event(keyboard, "Ł")
        self.assertEqual(key_event_upper, "L")
        self.assertTrue(mods_upper["Alt_R"])
        self.assertTrue(mods_upper["Shift_L"])

    def test_resolve_variant_does_not_falsely_map_dvorak_to_qwerty_en(self):
        entry = SystemLayoutEntry(0, "us", "dvorak", "English (Dvorak)")
        resolved = resolve_system_entry_to_vboard_layout(entry, self.layouts)
        self.assertEqual(resolved, "xkb:us:dvorak")
        self.assertEqual(self.layouts[resolved]["labels"]["S"], "o")


if __name__ == "__main__":
    unittest.main()
