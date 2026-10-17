"""Regresiones de los módulos migrados usando MockHardware."""

import sys
import unittest

from PyQt5.QtWidgets import QApplication

from controllers.analog_signal_controller import AnalogSignalController
from controllers.mfc_controller import MFCController
from controllers.process_controller import ProcessController
from controllers.throttle_controller import ThrottleController
from tests.mockScripts.mock_hardware import MockHardware


class MigratedModulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.hardware = MockHardware()

    def test_config_import_does_not_load_board_dll_drivers(self):
        self.assertNotIn("drivers.dio_driver", sys.modules)
        self.assertNotIn("drivers.analog_driver", sys.modules)

    def test_mfc_flow_scaling_validation_and_valve_close(self):
        self.assertEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 0.0)
        controller = MFCController(self.hardware, can_operate=lambda: True)
        errors = []
        controller.operation_error.connect(lambda name, message: errors.append((name, message)))

        controller.set_flow("MFC1", 3.25)
        controller.set_flow("MFC2", 0.45)
        self.assertAlmostEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 3.25)
        self.assertAlmostEqual(self.hardware.get_analog_output("MFC2_SETPOINT"), 0.45)

        controller.set_flow("MFC1", 10.01)
        self.assertTrue(errors)
        self.assertAlmostEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 3.25)

        controller.set_valve("MFC1", True)
        controller.set_valve("MFC1", False)
        self.assertFalse(self.hardware.digital_read("MFC1_OPEN"))
        self.assertEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 0.0)

    def test_analog_controller_reads_voltage_and_thermocouple(self):
        self.hardware.set_analog_value("BARATRON", 2.1)
        self.hardware.set_analog_value("CHAMBER_TEMP", 87.5)
        controller = AnalogSignalController(
            self.hardware,
            ("BARATRON", "CHAMBER_TEMP"),
        )
        values = {}
        controller.signal_value_changed.connect(lambda name, value: values.__setitem__(name, value))
        controller._poll_signals()
        self.assertAlmostEqual(values["BARATRON"], 2.1)
        self.assertAlmostEqual(values["CHAMBER_TEMP"], 87.5)

    def test_throttle_stops_at_directional_limit(self):
        controller = ThrottleController(self.hardware, can_operate=lambda: True)
        self.hardware.set_input_state("THROTTLE_OPEN", True)
        controller.start(closing=False)
        self.assertFalse(controller._timer.isActive())
        self.assertFalse(self.hardware.digital_read("STEPPER_OUTPUT_ENABLE"))

        self.hardware.set_input_state("THROTTLE_OPEN", False)
        controller.start(closing=False)
        self.assertTrue(controller._timer.isActive())
        controller.stop()
        self.assertFalse(self.hardware.digital_read("STEPPER_OUTPUT_ENABLE"))

    def test_process_fault_turns_off_lamps_and_plasma(self):
        controller = ProcessController(self.hardware, can_operate=lambda: True)
        alarms = []
        controller.alarm_raised.connect(alarms.append)
        controller.start_lamps13(10)
        controller.set_plasma(True)
        self.hardware.set_input_state("LAMP1_FAIL", True)
        controller.check_faults()
        self.assertTrue(alarms)
        for output_name in ("LAMP1_ON_CMD", "LAMP2_ON_CMD", "LAMP3_ON_CMD", "RF_ON_CMD"):
            self.assertFalse(self.hardware.digital_read(output_name))
        controller._pulse_timer.stop()


if __name__ == "__main__":
    unittest.main()
