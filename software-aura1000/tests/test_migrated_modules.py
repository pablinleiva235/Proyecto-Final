"""Regresiones de los módulos migrados usando MockHardware."""

import sys
import unittest

from PyQt5.QtWidgets import QApplication

from controllers.analog_signal_controller import AnalogSignalController
from controllers.mfc_controller import MFCController
from controllers.process_controller import ProcessController
from controllers.pressure_controller import PressureController
from controllers.throttle_controller import ThrottleController
from controllers.temperature_controller import TemperatureController
from gui.maintainer_screen import MaintainerScreen
from services.recipe_service import Recipe, RecipeError, RecipeService
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

    def test_pressure_control_homes_and_reaches_legacy_start_position(self):
        self.hardware.set_input_state("THROTTLE_OPEN", False)
        throttle = ThrottleController(self.hardware, can_operate=lambda: True)
        pressure = PressureController(throttle, can_operate=lambda: True)
        reached = []
        pressure.setpoint_reached.connect(reached.append)
        pressure.set_pressure_reading(0.5)
        pressure.start(1.0)

        self.assertEqual(pressure.state, "posicionando")
        self.assertFalse(pressure.state == "regulando")
        throttle._pulse()
        self.hardware.set_input_state("THROTTLE_OPEN", True)
        throttle._pulse()
        self.assertEqual(throttle._position_steps, 0)
        self.assertEqual(pressure.state, "posicionando")

        pulse_count = 0
        while (
            pressure.state == "posicionando"
            and throttle._timer.isActive()
            and pulse_count < throttle.REST_POSITION_STEPS * 2 + 2
        ):
            throttle._pulse()
            pulse_count += 1

        self.assertEqual(throttle._position_steps, 400)
        self.assertEqual(pressure.state, "regulando")
        self.assertTrue(self.hardware.digital_read("STEPPER_DIR"))
        self.assertTrue(throttle._timer.isActive())
        pressure.set_pressure_reading(1.0)
        self.assertFalse(throttle._timer.isActive())
        self.assertEqual(reached, [1.0])
        self.assertTrue(throttle._automatic_mode)
        pressure.stop()
        self.assertFalse(throttle._automatic_mode)

    def test_pressure_control_rejects_invalid_and_unreachable_setpoints(self):
        throttle = ThrottleController(self.hardware, can_operate=lambda: True)
        pressure = PressureController(throttle, can_operate=lambda: True)
        errors = []
        pressure.operation_error.connect(errors.append)
        pressure.set_pressure_reading(1.0)

        pressure.start(3.01)
        pressure.start(float("nan"))
        pressure.start(0.9)

        self.assertEqual(len(errors), 3)
        self.assertEqual(pressure.state, "detenido")
        self.assertFalse(throttle._timer.isActive())

    def test_pressure_control_stops_when_an_interlock_is_lost(self):
        allowed = [True]
        throttle = ThrottleController(self.hardware, can_operate=lambda: allowed[0])
        pressure = PressureController(throttle, can_operate=lambda: allowed[0])
        pressure.set_pressure_reading(0.5)
        pressure.start(1.0)
        self.assertTrue(throttle._timer.isActive())

        allowed[0] = False
        pressure._check_runtime_conditions()

        self.assertEqual(pressure.state, "detenido")
        self.assertFalse(throttle._timer.isActive())
        self.assertFalse(throttle._automatic_mode)

    def test_pressure_control_does_not_take_over_manual_throttle_motion(self):
        throttle = ThrottleController(self.hardware, can_operate=lambda: True)
        pressure = PressureController(throttle, can_operate=lambda: True)
        pressure.set_pressure_reading(0.5)
        throttle.start(closing=True)
        self.assertTrue(throttle._timer.isActive())

        pressure.start(1.0)

        self.assertEqual(pressure.state, "detenido")
        self.assertTrue(throttle._timer.isActive())
        throttle.stop()

    def test_maintainer_pressure_controls_are_limited_to_three_torr(self):
        screen = MaintainerScreen()
        screen.set_module_controls_enabled(True)
        self.assertEqual(screen.pressure_setpoint.minimum(), 0.0)
        self.assertEqual(screen.pressure_setpoint.maximum(), 3.0)
        self.assertTrue(screen.pressure_start_button.isEnabled())
        self.assertFalse(screen.pressure_stop_button.isEnabled())
        self.assertEqual(screen.temperature_setpoint.minimum(), 130.0)
        self.assertEqual(screen.temperature_setpoint.maximum(), 200.0)

    def test_temperature_ramp_and_hysteresis_use_managed_lamp_outputs(self):
        process = ProcessController(self.hardware, can_operate=lambda: True)
        temperature = TemperatureController(process, can_operate=lambda: True)
        temperature.set_temperature_reading(100.0)
        reached = []
        temperature.setpoint_reached.connect(reached.append)

        temperature.start(180.0)
        self.assertTrue(self.hardware.digital_read("LAMP1_ON_CMD"))
        self.assertTrue(self.hardware.digital_read("LAMP2_ON_CMD"))
        self.assertTrue(self.hardware.digital_read("LAMP3_ON_CMD"))
        self.assertEqual(temperature.state, "precalentando")

        for _ in range(11):
            temperature.set_temperature_reading(172.0)
        self.assertEqual(temperature.state, "manteniendo")
        self.assertFalse(self.hardware.digital_read("LAMP1_ON_CMD"))
        self.assertTrue(self.hardware.digital_read("LAMP2_ON_CMD"))
        self.assertFalse(self.hardware.digital_read("LAMP3_ON_CMD"))

        for _ in range(11):
            temperature.set_temperature_reading(183.0)
        self.assertFalse(self.hardware.digital_read("LAMP2_ON_CMD"))
        for _ in range(11):
            temperature.set_temperature_reading(177.0)
        self.assertTrue(self.hardware.digital_read("LAMP2_ON_CMD"))
        self.assertEqual(reached, [180.0])

        temperature.stop()
        for signal in ("LAMP1_ON_CMD", "LAMP2_ON_CMD", "LAMP3_ON_CMD"):
            self.assertFalse(self.hardware.digital_read(signal))

    def test_temperature_control_aborts_on_lost_interlock_or_reading(self):
        allowed = [True]
        process = ProcessController(self.hardware, can_operate=lambda: allowed[0])
        temperature = TemperatureController(process, can_operate=lambda: allowed[0])
        errors = []
        temperature.operation_error.connect(errors.append)
        temperature.set_temperature_reading(100.0)
        temperature.start(180.0)
        self.assertTrue(temperature.is_active)

        allowed[0] = False
        temperature._check_runtime_conditions()

        self.assertFalse(temperature.is_active)
        self.assertFalse(self.hardware.digital_read("LAMP1_ON_CMD"))
        self.assertFalse(self.hardware.digital_read("LAMP2_ON_CMD"))
        self.assertFalse(self.hardware.digital_read("LAMP3_ON_CMD"))
        self.assertTrue(errors)

    def test_recipe_process_pressure_is_limited_to_three_torr(self):
        service = RecipeService()
        recipe = Recipe(
            name="test",
            description="test recipe",
            o2_flow=1.0,
            n2_flow=0.1,
            base_pressure=0.5,
            process_pressure=3.01,
            process_temperature=150.0,
        )
        with self.assertRaises(RecipeError):
            service.validate(recipe)

        recipe.process_pressure = 2.0
        recipe.base_pressure = 3.01
        with self.assertRaises(RecipeError):
            service.validate(recipe)

        recipe.base_pressure = 0.5
        recipe.process_temperature = 200.0
        service.validate(recipe)
        recipe.process_temperature = 200.1
        with self.assertRaises(RecipeError):
            service.validate(recipe)

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
