import unittest

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtTest import QTest

from config.digital_signals import INACTIVE
from controllers.signal_controller import SignalController
from logic.vent_sequence import (
    VENT_STABILIZATION_TIME_MS,
    VentSequence,
    VentState,
)


class Hardware:
    def __init__(self):
        self.readings = {
            "ATM_SWITCH": False,
            "VENT_VALVE_CONTROL": False,
        }
        self.outputs = []

    def digital_read(self, signal_name):
        return self.readings[signal_name]

    def digital_set(self, signal_name, active):
        self.outputs.append((signal_name, active))


class VentSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.hardware = Hardware()
        self.vent = VentSequence(self.hardware)
        self.completed = []
        self.vent.vent_completed.connect(lambda: self.completed.append(True))
        self.vent.start()

    def test_five_consecutive_atm_readings_start_four_second_timer(self):
        for _ in range(4):
            self.vent.update_atmospheric_state(True)

        self.assertFalse(self.vent._stabilization_timer.isActive())

        self.vent.update_atmospheric_state(True)

        self.assertTrue(self.vent._stabilization_timer.isActive())
        self.assertEqual(
            self.vent._stabilization_timer.interval(),
            VENT_STABILIZATION_TIME_MS,
        )

    def test_inactive_reading_resets_consecutive_count(self):
        for _ in range(4):
            self.vent.update_atmospheric_state(True)
        self.vent.update_atmospheric_state(False)
        for _ in range(4):
            self.vent.update_atmospheric_state(True)

        self.assertFalse(self.vent._stabilization_timer.isActive())
        self.vent.update_atmospheric_state(True)
        self.assertTrue(self.vent._stabilization_timer.isActive())

        self.vent.update_atmospheric_state(False)
        self.assertFalse(self.vent._stabilization_timer.isActive())
        for _ in range(4):
            self.vent.update_atmospheric_state(True)
        self.assertFalse(self.vent._stabilization_timer.isActive())
        self.vent.update_atmospheric_state(True)
        self.assertTrue(self.vent._stabilization_timer.isActive())

    def test_stop_and_shutdown_cancel_count_and_timer(self):
        for _ in range(4):
            self.vent.update_atmospheric_state(True)
        self.vent.stop()
        self.assertFalse(self.vent._stabilization_timer.isActive())
        self.assertEqual(self.vent._consecutive_atm_readings, 0)

        self.vent.start()
        for _ in range(5):
            self.vent.update_atmospheric_state(True)
        self.assertTrue(self.vent._stabilization_timer.isActive())
        self.vent.shutdown()
        self.assertFalse(self.vent._stabilization_timer.isActive())
        self.assertEqual(self.vent._consecutive_atm_readings, 0)

    def test_timer_finishes_vent_after_four_seconds(self):
        for _ in range(5):
            self.vent.update_atmospheric_state(True)

        QTest.qWait(VENT_STABILIZATION_TIME_MS + 100)

        self.assertEqual(self.vent.state, VentState.IDLE)
        self.assertEqual(self.completed, [True])
        self.assertEqual(
            self.hardware.outputs[-1],
            ("VENT_VALVE_CONTROL", INACTIVE),
        )


class SignalSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_poll_emits_each_valid_sample_even_when_state_is_unchanged(self):
        hardware = Hardware()
        controller = SignalController(
            hardware=hardware,
            monitored_signals=("ATM_SWITCH", "VENT_VALVE_CONTROL"),
            output_signals=("VENT_VALVE_CONTROL",),
        )
        samples = []
        controller.signal_sampled.connect(
            lambda name, active: samples.append((name, active))
            if name == "ATM_SWITCH" else None
        )

        controller._poll_signals()
        controller._poll_signals()

        self.assertEqual(
            samples,
            [("ATM_SWITCH", False), ("ATM_SWITCH", False)],
        )


if __name__ == "__main__":
    unittest.main()
