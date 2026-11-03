import unittest

from PyQt5.QtWidgets import QApplication

from logic.startup_sequence import StartupSequence
from tests.mockScripts.mock_hardware import MockHardware


class StartupSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.hardware = MockHardware()
        self.startup = StartupSequence(
            hardware=self.hardware,
            initialize_analog=False,
        )

    def _advance_preheat(self):
        for _ in range(
            self.startup.STARTUP_DURATION_MS // self.startup.TIMER_INTERVAL_MS
        ):
            if self.startup.is_running:
                self.startup._update_progress()

    def test_startup_completes_after_preheat_without_throttle_controller(self):
        completed = []
        self.startup.startup_completed.connect(lambda: completed.append(True))

        self.startup.start()
        self.assertTrue(self.hardware.digital_read("POWER_ON"))
        self.assertTrue(self.hardware.digital_read("FILAMENT_ENABLE"))

        self._advance_preheat()

        self.assertEqual(completed, [True])
        self.assertFalse(self.startup.is_running)
        self.assertFalse(self.hardware.digital_read("POWER_ON"))
        self.assertTrue(self.hardware.digital_read("FILAMENT_ENABLE"))
        self.assertFalse(self.hardware.digital_read("DRIVER_ENABLE"))


if __name__ == "__main__":
    unittest.main()
