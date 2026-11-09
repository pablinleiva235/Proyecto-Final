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

    def test_simulated_startup_completes_after_three_seconds(self):
        simulated_startup = StartupSequence(
            hardware=self.hardware,
            initialize_analog=False,
            duration_ms=StartupSequence.SIMULATED_STARTUP_DURATION_MS,
        )
        completed = []
        progress = []
        simulated_startup.startup_completed.connect(lambda: completed.append(True))
        simulated_startup.progress_changed.connect(progress.append)

        simulated_startup.start()
        for _ in range(
            StartupSequence.SIMULATED_STARTUP_DURATION_MS
            // simulated_startup.TIMER_INTERVAL_MS
        ):
            simulated_startup._update_progress()

        self.assertEqual(completed, [True])
        self.assertEqual(progress[-1], 100)
        self.assertEqual(
            simulated_startup.SIMULATED_STARTUP_DURATION_MS,
            3_000,
        )

    def test_real_startup_keeps_thirty_second_default(self):
        self.assertEqual(self.startup.STARTUP_DURATION_MS, 30_000)
        self.assertEqual(self.startup._duration_ms, 30_000)


if __name__ == "__main__":
    unittest.main()
