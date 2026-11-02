import unittest

from PyQt5.QtWidgets import QApplication

from controllers.throttle_controller import ThrottleController
from logic.startup_sequence import StartupSequence
from tests.mockScripts.mock_hardware import MockHardware


class StartupSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.hardware = MockHardware()
        self.throttle = ThrottleController(
            self.hardware,
            can_operate=lambda: False,
        )
        self.startup = StartupSequence(
            hardware=self.hardware,
            initialize_analog=False,
        )
        self.startup.set_throttle_controller(self.throttle)

    def _pulse_throttle(self, count):
        for _ in range(count):
            if self.throttle._timer.isActive():
                self.throttle._pulse()

    def _advance_preheat(self):
        for _ in range(
            self.startup.STARTUP_DURATION_MS // self.startup.TIMER_INTERVAL_MS
        ):
            if self.startup.is_running:
                self.startup._update_progress()

    def test_startup_activates_power_and_filament_and_waits_for_homing(self):
        self.hardware.set_input_state("THROTTLE_OPEN", False)
        self.hardware.set_input_state("THROTTLE_CLOSED", False)
        completed = []
        self.startup.startup_completed.connect(lambda: completed.append(True))

        self.startup.start()
        self.assertTrue(self.hardware.digital_read("POWER_ON"))
        self.assertTrue(self.hardware.digital_read("FILAMENT_ENABLE"))

        self._pulse_throttle(self.throttle.LIMIT_DEBOUNCE_READS)
        self.assertTrue(self.hardware.digital_read("DRIVER_ENABLE"))
        self._advance_preheat()
        self.assertTrue(self.startup.is_running)
        self.assertEqual(completed, [])

        self.hardware.set_input_state("THROTTLE_OPEN", True)
        self._pulse_throttle(self.throttle.LIMIT_DEBOUNCE_READS)

        self.assertEqual(completed, [True])
        self.assertFalse(self.startup.is_running)
        self.assertFalse(self.hardware.digital_read("POWER_ON"))
        self.assertTrue(self.hardware.digital_read("FILAMENT_ENABLE"))
        self.assertFalse(self.hardware.digital_read("DRIVER_ENABLE"))
        self.assertEqual(self.throttle.position_steps, 0.0)

    def test_already_open_throttle_completes_without_enabling_driver(self):
        completed = []
        self.startup.startup_completed.connect(lambda: completed.append(True))

        self.startup.start()
        self._pulse_throttle(self.throttle.LIMIT_DEBOUNCE_READS)
        self.assertFalse(self.hardware.digital_read("DRIVER_ENABLE"))

        self._advance_preheat()

        self.assertEqual(completed, [True])
        self.assertEqual(self.throttle.position_steps, 0.0)

    def test_opening_door_during_homing_fails_and_cleans_up_outputs(self):
        errors = []
        self.startup.startup_error.connect(errors.append)
        self.startup.start()
        self.hardware.set_input_state("DOOR_CLOSE", False)

        self._pulse_throttle(1)

        self.assertEqual(len(errors), 1)
        self.assertFalse(self.startup.is_running)
        self.assertFalse(self.hardware.digital_read("POWER_ON"))
        self.assertFalse(self.hardware.digital_read("FILAMENT_ENABLE"))
        self.assertFalse(self.hardware.digital_read("DRIVER_ENABLE"))

    def test_homing_timeout_fails_startup_and_disables_driver(self):
        self.hardware.set_input_state("THROTTLE_OPEN", False)
        self.hardware.set_input_state("THROTTLE_CLOSED", False)
        errors = []
        self.startup.startup_error.connect(errors.append)

        self.startup.start()
        self._pulse_throttle(self.throttle.LIMIT_DEBOUNCE_READS)
        self.assertTrue(self.hardware.digital_read("DRIVER_ENABLE"))
        self.throttle._homing_timed_out()

        self.assertEqual(len(errors), 1)
        self.assertFalse(self.startup.is_running)
        self.assertFalse(self.hardware.digital_read("POWER_ON"))
        self.assertFalse(self.hardware.digital_read("FILAMENT_ENABLE"))
        self.assertFalse(self.hardware.digital_read("DRIVER_ENABLE"))


if __name__ == "__main__":
    unittest.main()
