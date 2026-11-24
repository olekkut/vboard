import unittest
from unittest import mock

from vboard import input_backends
from vboard.constants import FUNCTION_KEYS, MODIFIER_KEYS, NAVIGATION_KEYS, NUMPAD_KEYS


class FakeDevice:
    def __init__(self, supported_keys):
        self.supported_keys = supported_keys
        self.events = []

    def emit(self, key, value):
        self.events.append((key, value))


class FakeUInput:
    def __init__(self):
        self.device = None

    def __getattr__(self, name):
        if name.startswith("KEY_"):
            return name
        raise AttributeError(name)

    def Device(self, supported_keys):
        self.device = FakeDevice(supported_keys)
        return self.device


class UInputExtendedKeysTest(unittest.TestCase):
    def setUp(self):
        self.fake_uinput = FakeUInput()
        self.uinput_patch = mock.patch.object(
            input_backends,
            "uinput",
            self.fake_uinput,
        )
        self.uinput_patch.start()
        self.addCleanup(self.uinput_patch.stop)

    def test_registers_function_navigation_and_numpad_keys(self):
        backend = input_backends.UInputBackend()

        for key in FUNCTION_KEYS + NAVIGATION_KEYS + NUMPAD_KEYS:
            self.assertIn(key, backend.key_map)
            self.assertIn(backend.key_map[key], self.fake_uinput.device.supported_keys)

    def test_emits_altgr_chord_for_polish_diacritic(self):
        backend = input_backends.UInputBackend()
        modifiers = {modifier: False for modifier in MODIFIER_KEYS}
        modifiers["Alt_R"] = True

        backend.emit_key("A", modifiers)

        self.assertEqual(
            self.fake_uinput.device.events,
            [
                ("KEY_RIGHTALT", 1),
                ("KEY_A", 1),
                ("KEY_A", 0),
                ("KEY_RIGHTALT", 0),
            ],
        )


if __name__ == "__main__":
    unittest.main()
