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

    def test_registers_media_keys_and_releases_stuck_keys_via_watchdog(self):
        from vboard.constants import MEDIA_KEYS

        backend = input_backends.UInputBackend()
        for key in MEDIA_KEYS:
            self.assertIn(key, backend.key_map)

        # Simulate a stuck key pressed 10 seconds ago
        backend.pressed_keys["KEY_LEFTSHIFT"] = 0.0
        released = backend.check_stuck_keys(max_hold_seconds=1.0)
        self.assertEqual(released, ["KEY_LEFTSHIFT"])
        self.assertNotIn("KEY_LEFTSHIFT", backend.pressed_keys)
        self.assertIn(("KEY_LEFTSHIFT", 0), self.fake_uinput.device.events)

        # Simulate release_all_keys clearing all held keys
        backend.pressed_keys["KEY_A"] = 999999999.0
        backend.release_all_keys()
        self.assertEqual(backend.pressed_keys, {})
        self.assertIn(("KEY_A", 0), self.fake_uinput.device.events)

    def test_evdev_fallback_backend_when_uinput_unavailable(self):
        class FakeEcodes:
            EV_KEY = 1

            def __getattr__(self, name):
                if name.startswith("KEY_"):
                    return name
                raise AttributeError(name)

        class FakeEvdevDevice:
            def __init__(self, caps, name="vboard"):
                self.caps = caps
                self.name = name
                self.events = []
                self.closed = False

            def write(self, ev_type, code, value):
                self.events.append((ev_type, code, value))

            def syn(self):
                self.events.append(("SYN",))

            def close(self):
                self.closed = True

        class FakeEvdevModule:
            ecodes = FakeEcodes()

            def __init__(self):
                self.device = None

            def UInput(self, caps, name="vboard"):
                self.device = FakeEvdevDevice(caps, name=name)
                return self.device

        fake_evdev = FakeEvdevModule()
        with mock.patch.object(input_backends, "uinput", None), mock.patch.object(
            input_backends, "evdev", fake_evdev
        ):
            backend = input_backends.create_uinput_backend()
            self.assertEqual(backend.name, "evdev-uinput")
            modifiers = {modifier: False for modifier in MODIFIER_KEYS}
            backend.emit_key("VolumeUp", modifiers)
            self.assertIn((1, "KEY_VOLUMEUP", 1), fake_evdev.device.events)
            self.assertIn((1, "KEY_VOLUMEUP", 0), fake_evdev.device.events)
            backend.destroy()
            self.assertTrue(fake_evdev.device.closed)


if __name__ == "__main__":
    unittest.main()
