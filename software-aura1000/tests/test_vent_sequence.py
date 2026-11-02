import unittest

from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal
from PyQt5.QtTest import QTest

from config.digital_signals import INACTIVE
from controllers.throttle_controller import ThrottleController
from controllers.signal_controller import SignalController
from logic.vent_sequence import (
    VENT_STABILIZATION_TIME_MS,
    VentSequence,
    VentState,
)
from tests.mockScripts.mock_hardware import MockHardware


class Hardware:
    def __init__(self):
        self.readings = {
            "ATM_SWITCH": False,
            "VENT_VALVE_CONTROL": False,
            "DRIVER_ENABLE": True,
        }
        self.outputs = []

    def digital_read(self, signal_name):
        return self.readings[signal_name]

    def digital_set(self, signal_name, active):
        self.outputs.append((signal_name, active))
        self.readings[signal_name] = active


class ThrottleHomeStub(QObject):
    startup_homing_completed = pyqtSignal()
    startup_homing_failed = pyqtSignal(str)

    def __init__(self, at_initial_position=False):
        super().__init__()
        self._at_initial_position = at_initial_position
        self.home_calls = 0
        self.is_moving = False

    @property
    def is_at_initial_position(self):
        return self._at_initial_position

    def home_on_startup(self):
        self.home_calls += 1
        self._at_initial_position = False

    def stop(self):
        self.is_moving = False

    def stop_startup_homing(self):
        self.is_moving = False
        return None

    def complete_homing(self):
        self._at_initial_position = True
        self.startup_homing_completed.emit()


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

    def test_vent_waits_for_throttle_homing_before_opening_vent_valve(self):
        self.vent.stop()
        throttle = ThrottleHomeStub(at_initial_position=False)
        self.vent.set_throttle_controller(throttle)

        self.vent.start()

        self.assertEqual(self.vent.state, VentState.STARTING)
        self.assertEqual(throttle.home_calls, 1)
        self.assertFalse(self.hardware.digital_read("VENT_VALVE_CONTROL"))

        throttle.complete_homing()

        self.assertEqual(self.vent.state, VentState.RUNNING)
        self.assertTrue(self.hardware.digital_read("VENT_VALVE_CONTROL"))

    def test_vent_skips_homing_when_throttle_is_already_at_initial_position(self):
        self.vent.stop()
        throttle = ThrottleHomeStub(at_initial_position=True)
        self.vent.set_throttle_controller(throttle)

        self.vent.start()

        self.assertEqual(throttle.home_calls, 0)
        self.assertEqual(self.vent.state, VentState.RUNNING)
        self.assertTrue(self.hardware.digital_read("VENT_VALVE_CONTROL"))

    def test_vent_stays_closed_when_throttle_homing_fails(self):
        self.vent.stop()
        throttle = ThrottleHomeStub(at_initial_position=False)
        self.vent.set_throttle_controller(throttle)
        errors = []
        self.vent.sequence_error.connect(errors.append)

        self.vent.start()
        throttle.startup_homing_failed.emit("No se confirmó THROTTLE_OPEN dentro del tiempo límite.")

        self.assertEqual(self.vent.state, VentState.ERROR)
        self.assertFalse(self.hardware.digital_read("VENT_VALVE_CONTROL"))
        self.assertIn("falló el homing", errors[-1])

    def test_shutdown_cancels_pending_throttle_homing(self):
        self.vent.stop()
        throttle = ThrottleHomeStub(at_initial_position=False)
        self.vent.set_throttle_controller(throttle)
        self.vent.start()

        self.vent.shutdown()
        throttle.complete_homing()

        self.assertEqual(self.vent.state, VentState.IDLE)
        self.assertFalse(self.hardware.digital_read("VENT_VALVE_CONTROL"))

    def test_vent_homes_real_throttle_before_opening_vent_valve(self):
        hardware = MockHardware()
        hardware.digital_set("DRIVER_ENABLE", True)
        hardware.set_input_state("THROTTLE_OPEN", False)
        hardware.set_input_state("THROTTLE_CLOSED", False)
        throttle = ThrottleController(hardware, can_operate=lambda: False)
        vent = VentSequence(hardware)
        vent.set_throttle_controller(throttle)

        vent.start()

        self.assertEqual(vent.state, VentState.STARTING)
        self.assertFalse(hardware.digital_read("VENT_VALVE_CONTROL"))
        for _ in range(throttle.LIMIT_DEBOUNCE_READS):
            throttle._pulse()
        hardware.set_input_state("THROTTLE_OPEN", True)
        for _ in range(throttle.LIMIT_DEBOUNCE_READS):
            throttle._pulse()

        self.assertEqual(throttle.position_steps, 0.0)
        self.assertTrue(throttle.is_at_initial_position)
        self.assertEqual(vent.state, VentState.RUNNING)
        self.assertTrue(hardware.digital_read("VENT_VALVE_CONTROL"))


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
