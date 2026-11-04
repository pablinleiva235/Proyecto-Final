"""Regresiones de los módulos migrados usando MockHardware."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication

from controllers.analog_signal_controller import AnalogSignalController
from controllers.mfc_controller import MFCController
from controllers.process_controller import ProcessController
from controllers.pressure_controller import PressureController
from controllers.throttle_controller import ThrottleController
from controllers.temperature_controller import TemperatureController
from config.pressure_limits import minimum_process_pressure
from gui.maintainer_screen import MaintainerScreen
from gui.recipe_dialogs import RecipeEditorDialog
from gui.widgets.localization import translate_widget_tree
import config_gui.strings as strings
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
        self.hardware.digital_set("DRIVER_ENABLE", True)
        controller = MFCController(self.hardware, can_operate=lambda: True)
        errors = []
        controller.operation_error.connect(lambda name, message: errors.append((name, message)))

        controller.set_flow("MFC1", 3.25)
        controller.set_flow("MFC2", 0.45)
        self.assertAlmostEqual(
            self.hardware.get_analog_output("MFC1_SETPOINT"),
            max(0.0, 3.25 - 0.16) / 0.981 / 10.0 * 5.0,
        )
        self.assertAlmostEqual(self.hardware.get_analog_output("MFC2_SETPOINT"), 2.25)

        controller.set_flow("MFC1", 6.51)
        self.assertTrue(errors)
        self.assertAlmostEqual(
            self.hardware.get_analog_output("MFC1_SETPOINT"),
            max(0.0, 3.25 - 0.16) / 0.981 / 10.0 * 5.0,
        )

        controller.set_flow("MFC2", 0.09)
        self.assertEqual(len(errors), 2)

        controller.set_valve("MFC1", True)
        controller.set_valve("MFC1", False)
        self.assertFalse(self.hardware.digital_read("MFC1_OPEN"))
        self.assertEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 0.0)

    def test_mfc_calibration_boundaries_and_measurement_conversion(self):
        self.assertEqual(MFCController.flow_to_voltage("MFC1", 0), 0.0)
        self.assertEqual(MFCController.flow_to_voltage("MFC1", 0.16), 0.0)
        self.assertAlmostEqual(MFCController.flow_to_voltage("MFC1", 6.5), 3.2313965341)
        self.assertAlmostEqual(MFCController.flow_to_voltage("MFC2", 0.1), 0.5)
        self.assertAlmostEqual(MFCController.flow_to_voltage("MFC2", 0.65), 3.25)
        self.assertAlmostEqual(MFCController.voltage_to_flow("MFC1", 2.5), 4.905)
        self.assertAlmostEqual(MFCController.voltage_to_flow("MFC2", 2.5), 0.5)

    def test_mfc_output_offset_calibration_is_persisted_and_keeps_read_conversion(self):
        class MemorySettings:
            NoError = 0
            values = {}

            def __init__(self, *args):
                pass

            def value(self, key, default=None, type=None):
                value = self.values.get(key, default)
                return type(value) if type is not None else value

            def setValue(self, key, value):
                self.values[key] = value

            def sync(self):
                pass

            def status(self):
                return self.NoError

        MemorySettings.values = {}
        self.hardware.digital_set("DRIVER_ENABLE", True)
        with patch("controllers.mfc_controller.QSettings", MemorySettings):
            controller = MFCController(self.hardware, can_operate=lambda: True)
            results = []
            controller.calibration_finished.connect(lambda *args: results.append(args))
            controller.calibrate_output_offset("MFC1", 2.0)
            measured_voltage = 2.4 / (10.0 * 0.981) * 5.0
            for _ in range(4):
                controller.update_flow_measurement("MFC1", measured_voltage)
            controller._finish_calibration("MFC1")

            self.assertEqual(len(results), 1)
            self.assertTrue(results[0][1])
            self.assertAlmostEqual(results[0][2], 0.4)
            self.assertTrue(results[0][4])
            self.assertFalse(controller._valves["MFC1"])
            self.assertEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 0.0)
            self.assertAlmostEqual(MFCController.voltage_to_flow("MFC1", measured_voltage), 2.4)

            reloaded = MFCController(self.hardware, can_operate=lambda: True)
            self.assertAlmostEqual(reloaded.output_offset("MFC1"), 0.4)
            reloaded.set_flow("MFC1", 3.0)
            self.assertAlmostEqual(
                self.hardware.get_analog_output("MFC1_SETPOINT"),
                (3.0 - 0.4) / 0.981 / 10.0 * 5.0,
            )

    def test_flow_monitor_waits_for_three_seconds_and_trips_over_tolerance(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        controller = MFCController(self.hardware, can_operate=lambda: True)
        faults = []
        controller.flow_fault.connect(faults.append)
        controller.set_flow("MFC1", 2.0)
        controller.set_valve("MFC1", True)
        # Una desviación del 26% supera la tolerancia de 25%.
        voltage = (2.0 * 1.26) / (10.0 * 0.981) * 5.0
        with patch("controllers.mfc_controller.time.monotonic", side_effect=(0.0, 1.0, 2.0, 2.99, 3.0)):
            for _ in range(4):
                controller.update_flow_measurement("MFC1", voltage)
            self.assertFalse(faults)
            controller.update_flow_measurement("MFC1", voltage)
        self.assertEqual(len(faults), 1)

    def test_mfc1_flow_monitor_accepts_deviation_up_to_25_percent(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        controller = MFCController(self.hardware, can_operate=lambda: True)
        faults = []
        controller.flow_fault.connect(faults.append)
        controller.set_flow("MFC1", 2.0)
        controller.set_valve("MFC1", True)
        voltage = (2.0 * 1.25) / (10.0 * 0.981) * 5.0
        with patch("controllers.mfc_controller.time.monotonic", side_effect=(0.0, 1.0, 2.0, 3.0)):
            for _ in range(4):
                controller.update_flow_measurement("MFC1", voltage)
        self.assertEqual(faults, [])

    def test_flow_monitor_uses_mfc2_tolerance(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        controller = MFCController(self.hardware, can_operate=lambda: True)
        faults = []
        controller.flow_fault.connect(faults.append)
        controller.set_flow("MFC2", 0.4)
        controller.set_valve("MFC2", True)
        # 30% below the target exceeds MFC2's 25% tolerance.
        with patch("controllers.mfc_controller.time.monotonic", side_effect=(0.0, 1.0, 2.0, 3.0)):
            for _ in range(4):
                controller.update_flow_measurement("MFC2", 0.4 * 0.7 / 1.0 * 5.0)
        self.assertEqual(len(faults), 1)

    def test_plasma_requires_mfc1_valve_and_positive_o2_setpoint(self):
        allowed = {"value": False}
        controller = ProcessController(
            self.hardware,
            can_operate=lambda: True,
            can_enable_plasma=lambda: allowed["value"],
        )
        controller.set_plasma(True)
        self.assertFalse(controller.plasma_active)
        self.assertFalse(self.hardware.digital_read("RF_ON_CMD"))
        allowed["value"] = True
        controller.set_plasma(True)
        self.assertTrue(controller.plasma_active)
        controller.set_plasma(False)

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

    def test_throttle_emits_only_changed_non_step_output_signals(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        throttle = ThrottleController(self.hardware, can_operate=lambda: True)
        changes = []
        throttle.output_signal_changed.connect(
            lambda name, active: changes.append((name, active))
        )

        throttle._write("STEPPER_DIR", True)
        throttle._write("STEPPER_DIR", True)
        throttle._write("STEPPER_HALF_STEP", True)
        throttle._write("STEPPER_OUTPUT_ENABLE", True)
        throttle._write("STEPPER_STEP", True)
        throttle._write("STEPPER_STEP", False)

        self.assertEqual(
            changes,
            [
                ("STEPPER_DIR", True),
                ("STEPPER_HALF_STEP", True),
                ("STEPPER_OUTPUT_ENABLE", True),
            ],
        )

    def test_throttle_reports_nominal_step_frequency_changes_and_stop(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        self.hardware.set_input_state("THROTTLE_CLOSED", False)
        throttle = ThrottleController(self.hardware, can_operate=lambda: True)
        throttle._automatic_mode = True
        frequencies = []
        throttle.pulse_frequency_changed.connect(frequencies.append)

        throttle.start_pressure_motion(closing=True, pulse_interval_ms=10, half_step=True)
        throttle.start_pressure_motion(closing=True, pulse_interval_ms=2, half_step=False)
        throttle.stop_pressure_motion()

        self.assertEqual(frequencies, [50.0, 250.0, 0.0])

    def test_throttle_moves_fixed_full_and_half_step_bursts(self):
        controller = ThrottleController(self.hardware, can_operate=lambda: True)
        self.hardware.set_input_state("THROTTLE_OPEN", False)
        self.hardware.set_input_state("THROTTLE_CLOSED", False)
        controller._position_steps = 10.0
        positions = []
        controller.position_changed.connect(positions.append)
        controller.move_steps(closing=True, steps=3, half_step=False)
        self.assertFalse(self.hardware.digital_read("STEPPER_HALF_STEP"))
        for _ in range(6):
            controller._pulse()
        self.assertFalse(controller._timer.isActive())
        self.assertEqual(controller.position_steps, 13.0)

        controller.move_steps(closing=False, steps=4, half_step=True)
        self.assertTrue(self.hardware.digital_read("STEPPER_HALF_STEP"))
        for _ in range(8):
            controller._pulse()
        self.assertFalse(controller._timer.isActive())
        self.assertEqual(controller.position_steps, 11.0)
        self.assertEqual(positions, [11.0, 12.0, 13.0, 12.5, 12.0, 11.5, 11.0])

    def test_manual_throttle_motion_does_not_require_process_vacuum(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        self.hardware.set_input_state("THROTTLE_OPEN", False)
        self.hardware.set_input_state("THROTTLE_CLOSED", False)
        throttle = ThrottleController(
            self.hardware,
            can_operate=lambda: True,
            can_operate_process=lambda: False,
        )
        throttle._position_steps = 0.0

        throttle.start(closing=True)

        self.assertTrue(throttle.is_moving)
        throttle._pulse()
        self.assertEqual(throttle.position_steps, 1.0)
        throttle.stop()

    def test_safety_repositioning_does_not_require_process_vacuum(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        self.hardware.set_input_state("THROTTLE_OPEN", False)
        self.hardware.set_input_state("THROTTLE_CLOSED", False)
        throttle = ThrottleController(
            self.hardware,
            can_operate=lambda: True,
            can_operate_process=lambda: False,
        )
        throttle._position_steps = 398.0
        results = []
        throttle.safety_return_finished.connect(
            lambda success, message: results.append((success, message))
        )

        self.assertTrue(throttle.return_to_rest_for_safety())
        while throttle.is_moving:
            throttle._pulse()

        self.assertTrue(throttle.is_at_rest_position)
        self.assertTrue(results[0][0])

    def test_throttle_position_never_goes_negative_when_opening(self):
        controller = ThrottleController(self.hardware, can_operate=lambda: True)
        self.hardware.digital_set("DRIVER_ENABLE", True)
        self.hardware.set_input_state("THROTTLE_OPEN", False)
        self.hardware.set_input_state("THROTTLE_CLOSED", False)
        controller._position_steps = 0.5
        positions = []
        controller.position_changed.connect(positions.append)

        controller.move_steps(closing=False, steps=1, half_step=True)
        for _ in range(2):
            controller._pulse()
        self.assertEqual(controller.position_steps, 0.0)
        self.assertEqual(positions, [0.0])

        controller.move_steps(closing=False, steps=2, half_step=True)
        for _ in range(4):
            controller._pulse()
        self.assertEqual(controller.position_steps, 0.0)
        self.assertEqual(positions, [0.0])

        controller.move_steps(closing=True, steps=1, half_step=True)
        for _ in range(2):
            controller._pulse()
        self.assertEqual(controller.position_steps, 0.5)
        self.assertEqual(positions, [0.0, 0.5])

    def test_maintainer_displays_estimated_throttle_position_and_unknown_reference(self):
        screen = MaintainerScreen()
        self.assertEqual(screen.throttle_limits_group.title(), "Estado de throttle")
        self.assertIs(screen.throttle_position_card.parent(), screen.throttle_limits_group)
        self.assertIs(screen.baratron_readout_card.parent(), screen.throttle_limits_group)
        self.assertIs(screen._analog_values["BARATRON"], screen.baratron_readout_card)
        self.assertNotIn(
            screen.baratron_readout_card,
            screen.analog_readouts_group.findChildren(type(screen.baratron_readout_card)),
        )
        for name in ("CHAMBER_TEMP", "EOP"):
            self.assertIn(
                screen._analog_values[name],
                screen.analog_readouts_group.findChildren(
                    type(screen._analog_values[name])
                ),
            )
        self.assertTrue(
            all(
                widget.parent() is screen.throttle_limits_group
                for widget in screen._throttle_limit_widgets.values()
            )
        )

        screen.set_throttle_position(None)
        self.assertEqual(screen.throttle_position_card.value_label.text(), "---")
        self.assertEqual(screen.throttle_position_card.type_label.text(), "Sin referencia")
        screen.set_throttle_position(12.5)
        self.assertEqual(screen.throttle_position_card.value_label.text(), "12.5")
        self.assertEqual(screen.throttle_position_card.unit_label.text(), "pasos")
        screen.set_analog_value("BARATRON", 1.234)
        self.assertEqual(screen.baratron_readout_card.value_label.text(), "1.234")
        self.assertEqual(screen.baratron_readout_card.unit_label.text(), "Torr")
        screen.set_pressure_reading_unavailable()
        self.assertEqual(screen.baratron_readout_card.value_label.text(), "ERR")
        self.assertTrue(screen.baratron_readout_card.value_label.property("error"))
        screen.set_throttle_position(None)

        previous_language = strings.get_language()
        try:
            strings.set_language("en")
            translate_widget_tree(screen)
            self.assertEqual(screen.throttle_limits_group.title(), "Throttle status")
            self.assertEqual(screen.throttle_position_card.title_label.text(), "Estimated position")
            self.assertEqual(screen.throttle_position_card.type_label.text(), "Unreferenced")
            self.assertEqual(screen.throttle_position_card.unit_label.text(), "steps")
            self.assertEqual(screen.throttle_position_card.footer_label.text(), "Full Step equivalents")
            self.assertEqual(screen.baratron_readout_card.title_label.text(), "Baratron · Pressure")
            self.assertEqual(screen.baratron_readout_card.footer_label.text(), "Analog reading")
        finally:
            strings.set_language(previous_language)
            translate_widget_tree(screen)

    def test_throttle_rejects_step_count_out_of_range(self):
        controller = ThrottleController(self.hardware, can_operate=lambda: True)
        errors = []
        controller.operation_error.connect(errors.append)
        controller.move_steps(True, 0)
        controller.move_steps(True, 1401)
        self.assertEqual(len(errors), 2)
        self.assertFalse(controller._timer.isActive())
        controller.move_steps(True, 1400)
        self.assertTrue(controller._timer.isActive())
        self.assertEqual(controller._remaining_steps, 1400)
        controller.stop()

    def test_throttle_limit_status_uses_gradual_three_sample_debounce(self):
        controller = ThrottleController(self.hardware, can_operate=lambda: True)
        changes = []
        controller.limit_state_changed.connect(lambda name, state: changes.append((name, state)))
        controller._record_limit_sample("THROTTLE_OPEN", True)
        controller._record_limit_sample("THROTTLE_OPEN", True)
        self.assertFalse(controller._limit_stable["THROTTLE_OPEN"])
        controller._record_limit_sample("THROTTLE_OPEN", False)
        controller._record_limit_sample("THROTTLE_OPEN", True)
        self.assertFalse(controller._limit_stable["THROTTLE_OPEN"])
        controller._record_limit_sample("THROTTLE_OPEN", True)
        self.assertTrue(controller._limit_stable["THROTTLE_OPEN"])
        self.assertEqual(changes, [("THROTTLE_OPEN", True)])
        controller._record_limit_sample("THROTTLE_OPEN", False)
        controller._record_limit_sample("THROTTLE_OPEN", False)
        self.assertTrue(controller._limit_stable["THROTTLE_OPEN"])
        controller._record_limit_sample("THROTTLE_OPEN", False)
        self.assertFalse(controller._limit_stable["THROTTLE_OPEN"])
        self.assertEqual(changes, [("THROTTLE_OPEN", True), ("THROTTLE_OPEN", False)])

        self.hardware.set_input_state("THROTTLE_OPEN", True)
        controller.start(closing=False)
        self.assertTrue(controller._timer.isActive())
        controller._pulse()
        self.assertFalse(controller._timer.isActive())

    def test_throttle_ignores_one_simultaneous_limit_sample(self):
        controller = ThrottleController(self.hardware, can_operate=lambda: True)
        self.hardware.set_input_state("THROTTLE_OPEN", True)
        self.hardware.set_input_state("THROTTLE_CLOSED", True)
        self.assertFalse(controller._limit_reached())
        self.assertFalse(controller._limit_stable["THROTTLE_OPEN"])
        self.assertFalse(controller._limit_stable["THROTTLE_CLOSED"])

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
        self.assertIsNone(throttle._position_steps)
        throttle.stop_if_limit_reached()
        throttle.stop_if_limit_reached()
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
        pressure.set_pressure_reading(1.0)
        self.assertFalse(throttle._timer.isActive())
        self.assertEqual(reached, [1.0])
        self.assertTrue(throttle._automatic_mode)
        pressure.stop()
        self.assertFalse(throttle._automatic_mode)

    def test_pressure_control_uses_median_and_adapts_step_mode(self):
        throttle = ThrottleController(self.hardware, can_operate=lambda: True)
        pressure = PressureController(throttle, can_operate=lambda: True)
        pressure._state = "regulando"
        pressure._target = 1.0
        throttle._automatic_mode = True
        for reading in (0.5, 0.5, 0.5, 8.0, 0.5, 0.5, 0.5):
            pressure.set_pressure_reading(reading)
        self.assertTrue(throttle._timer.isActive())
        self.assertTrue(self.hardware.digital_read("STEPPER_DIR"))
        self.assertFalse(self.hardware.digital_read("STEPPER_HALF_STEP"))
        self.assertEqual(throttle._timer.interval(), 2)

        pressure._apply_pressure_correction(0.8)
        self.assertTrue(self.hardware.digital_read("STEPPER_HALF_STEP"))
        self.assertEqual(throttle._timer.interval(), 4)
        pressure._apply_pressure_correction(0.97)
        self.assertEqual(throttle._timer.interval(), 10)
        pressure.stop(return_to_rest=False)

    def test_pressure_stop_returns_fully_open_but_abort_does_not(self):
        throttle = ThrottleController(self.hardware, can_operate=lambda: True)
        pressure = PressureController(throttle, can_operate=lambda: True)
        self.hardware.digital_set("DRIVER_ENABLE", True)
        self.hardware.set_input_state("THROTTLE_OPEN", False)
        self.hardware.set_input_state("THROTTLE_CLOSED", False)
        throttle._position_steps = 390.0
        throttle._automatic_mode = True
        pressure._target = 1.0
        pressure._state = "regulando"
        pressure.stop()
        self.assertEqual(pressure.state, "reposicionando")
        self.assertTrue(throttle._homing_active)
        self.assertFalse(self.hardware.digital_read("STEPPER_DIR"))
        self.hardware.set_input_state("THROTTLE_OPEN", True)
        for _ in range(20):
            throttle._pulse()
        self.assertEqual(throttle.position_steps, 0.0)
        self.assertTrue(throttle._limit_stable["THROTTLE_OPEN"])
        self.assertEqual(pressure.state, "detenido")
        self.assertFalse(throttle._automatic_mode)
        self.assertFalse(self.hardware.digital_read("STEPPER_OUTPUT_ENABLE"))

        throttle._position_steps = 390.0
        throttle._automatic_mode = True
        pressure._target = 1.0
        pressure._state = "regulando"
        pressure.abort("interlock perdido")
        self.assertEqual(throttle.position_steps, 390.0)
        self.assertEqual(pressure.state, "detenido")
        self.assertFalse(throttle._timer.isActive())

    def test_safety_open_return_skips_motor_when_open_limit_is_active(self):
        throttle = ThrottleController(self.hardware, can_operate=lambda: True)
        self.hardware.set_input_state("THROTTLE_OPEN", True)
        results = []
        throttle.safety_return_finished.connect(lambda *result: results.append(result))

        started = throttle.return_to_open_for_safety()

        self.assertFalse(started)
        self.assertEqual(throttle.position_steps, 0.0)
        self.assertFalse(throttle.is_moving)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0][0])

    def test_maintainer_exposes_step_controls(self):
        screen = MaintainerScreen()
        screen.set_module_controls_enabled(True)
        requests = []
        screen.throttle_steps_requested.connect(lambda *args: requests.append(args))
        screen.throttle_step_count.setValue(24)
        screen.throttle_step_mode.setCurrentIndex(1)
        screen.throttle_open_steps_button.click()
        self.assertEqual(requests, [(False, 24, True)])

    def test_maintainer_mirrors_debounced_throttle_limits(self):
        screen = MaintainerScreen()

        for name in ("THROTTLE_CLOSED", "THROTTLE_OPEN"):
            self.assertFalse(screen._throttle_limit_widgets[name].is_interactive)
            screen.set_signal_active(name, True)
            self.assertEqual(
                screen._throttle_limit_widgets[name].visual_state,
                screen._signal_widgets[name].visual_state,
            )
            screen.set_signal_active(name, False)
            self.assertEqual(
                screen._throttle_limit_widgets[name].visual_state,
                screen._signal_widgets[name].visual_state,
            )

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

    def test_pressure_control_rejects_start_without_main_vacuum_permission(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        throttle = ThrottleController(
            self.hardware,
            can_operate=lambda: True,
            can_operate_process=lambda: False,
        )
        pressure = PressureController(throttle, can_operate=lambda: False)
        errors = []
        pressure.operation_error.connect(errors.append)
        pressure.set_pressure_reading(0.5)

        pressure.start(1.0)

        self.assertEqual(pressure.state, "detenido")
        self.assertTrue(errors)
        self.assertFalse(throttle.is_moving)

    def test_maintainer_can_enable_throttle_without_process_modules(self):
        screen = MaintainerScreen()

        screen.set_module_controls_enabled(False, throttle_enabled=True)

        self.assertTrue(screen.throttle_open_button.isEnabled())
        self.assertTrue(screen.throttle_close_button.isEnabled())
        self.assertTrue(screen.throttle_open_steps_button.isEnabled())
        self.assertFalse(screen.pressure_start_button.isEnabled())
        self.assertFalse(screen.plasma_button.isEnabled())

    def test_pressure_control_stops_when_an_interlock_is_lost(self):
        allowed = [True]
        self.hardware.digital_set("DRIVER_ENABLE", True)
        throttle = ThrottleController(self.hardware, can_operate=lambda: allowed[0])
        pressure = PressureController(throttle, can_operate=lambda: allowed[0])
        self.hardware.set_input_state("THROTTLE_OPEN", False)
        pressure.set_pressure_reading(0.5)
        pressure.start(1.0)
        self.assertTrue(throttle._timer.isActive())

        allowed[0] = False
        pressure._check_runtime_conditions()

        self.assertEqual(pressure.state, "detenido")
        self.assertFalse(throttle._timer.isActive())
        self.assertFalse(throttle._automatic_mode)

    def test_pressure_minimum_curve_interpolates_table_and_caps_above_six(self):
        expected = (0.83, 1.14, 1.51, 1.86, 2.23, 2.63, 3.0)
        for flow, pressure in enumerate(expected):
            self.assertAlmostEqual(minimum_process_pressure(flow), pressure)
        self.assertAlmostEqual(minimum_process_pressure(0.5), 0.985)
        self.assertEqual(minimum_process_pressure(6.5), 3.0)

    def test_pressure_controller_enforces_flow_dependent_minimum(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        throttle = ThrottleController(self.hardware, can_operate=lambda: True)
        pressure = PressureController(throttle, can_operate=lambda: True)
        errors = []
        pressure.operation_error.connect(errors.append)
        pressure.set_pressure_reading(0.5)

        pressure.start(1.13, o2_flow=1.0)
        self.assertEqual(pressure.state, "detenido")
        self.assertTrue(errors)
        pressure.start(1.14, o2_flow=1.0)
        self.assertEqual(pressure.state, "posicionando")
        pressure.stop()

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
        self.assertEqual(screen.pressure_setpoint.minimum(), 0.83)
        self.assertEqual(screen.pressure_setpoint.maximum(), 3.0)
        self.assertTrue(screen.pressure_start_button.isEnabled())
        self.assertFalse(screen.pressure_stop_button.isEnabled())
        self.assertEqual(screen.temperature_setpoint.minimum(), 130.0)
        self.assertEqual(screen.temperature_setpoint.maximum(), 190.0)
        screen.mfc1_card.setpoint.setValue(2.0)
        self.assertAlmostEqual(screen.pressure_setpoint.minimum(), 1.51)

    def test_maintainer_allows_plasma_during_temperature_control(self):
        screen = MaintainerScreen()
        screen.set_module_controls_enabled(True)

        for state in ("precalentando", "manteniendo"):
            screen.set_temperature_control_state(state)
            self.assertTrue(screen.plasma_button.isEnabled())
            self.assertFalse(screen.lamps13_button.isEnabled())
            self.assertFalse(screen.lamp2_button.isEnabled())

            # Una actualización de habilitación general conserva la regla.
            screen.set_module_controls_enabled(True)
            self.assertTrue(screen.plasma_button.isEnabled())

        screen.set_module_controls_enabled(False)
        self.assertFalse(screen.plasma_button.isEnabled())

    def test_temperature_control_still_rejects_start_when_plasma_is_active(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        process = ProcessController(
            self.hardware,
            can_operate=lambda: True,
            can_enable_plasma=lambda: True,
        )
        process.set_plasma(True)
        temperature = TemperatureController(process, can_operate=lambda: True)
        temperature.set_temperature_reading(100.0)
        errors = []
        temperature.operation_error.connect(errors.append)

        temperature.start(180.0)

        self.assertFalse(temperature.is_active)
        self.assertTrue(process.plasma_active)
        self.assertTrue(any("Apague el plasma" in error for error in errors))

    def test_temperature_stop_still_turns_lamps_off_if_plasma_off_fails(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        process = ProcessController(self.hardware, can_operate=lambda: True)
        temperature = TemperatureController(process, can_operate=lambda: True)
        temperature.set_temperature_reading(100.0)
        temperature.start(180.0)
        errors = []
        temperature.operation_error.connect(errors.append)

        with patch.object(process, "set_plasma", side_effect=RuntimeError("RF write failed")):
            temperature.stop()

        self.assertFalse(temperature.is_active)
        self.assertTrue(all(
            not self.hardware.digital_read(signal)
            for signal in ("LAMP1_ON_CMD", "LAMP2_ON_CMD", "LAMP3_ON_CMD")
        ))
        self.assertTrue(any("No se pudo apagar el plasma" in error for error in errors))

    def test_temperature_ramp_and_hysteresis_use_managed_lamp_outputs(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
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

        # Para 180 °C y una lectura inicial de 100 °C, la rampa termina
        # a 180 - (8.0 + 9.75) = 162.25 °C.
        for _ in range(11):
            temperature.set_temperature_reading(162.0)
        self.assertEqual(temperature.state, "precalentando")
        for _ in range(11):
            temperature.set_temperature_reading(163.0)
        self.assertEqual(temperature.state, "manteniendo")
        # A baja temperatura, la asistencia heredada puede arrancar en la
        # primera evaluación posterior al fin de rampa.
        temperature._stop_assist_pulse()
        self.assertFalse(self.hardware.digital_read("LAMP1_ON_CMD"))
        self.assertTrue(self.hardware.digital_read("LAMP2_ON_CMD"))
        self.assertFalse(self.hardware.digital_read("LAMP3_ON_CMD"))

        # La histéresis queda bloqueada hasta la primera caída por debajo de
        # setpoint + 7 °C; luego L2 conmuta en los límites ±7 °C.
        for _ in range(11):
            temperature.set_temperature_reading(188.0)
        self.assertTrue(self.hardware.digital_read("LAMP2_ON_CMD"))
        for _ in range(11):
            temperature.set_temperature_reading(187.0)
        self.assertFalse(self.hardware.digital_read("LAMP2_ON_CMD"))
        for _ in range(11):
            temperature.set_temperature_reading(173.0)
        self.assertTrue(self.hardware.digital_read("LAMP2_ON_CMD"))
        for _ in range(11):
            temperature.set_temperature_reading(177.0)
        self.assertEqual(reached, [180.0])

        process.set_plasma(True)
        temperature.stop()
        self.assertFalse(process.plasma_active)
        self.assertFalse(self.hardware.digital_read("RF_ON_CMD"))
        for signal in ("LAMP1_ON_CMD", "LAMP2_ON_CMD", "LAMP3_ON_CMD"):
            self.assertFalse(self.hardware.digital_read(signal))

    def test_temperature_control_aborts_on_lost_interlock_or_reading(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        allowed = [True]
        process = ProcessController(self.hardware, can_operate=lambda: allowed[0])
        temperature = TemperatureController(process, can_operate=lambda: allowed[0])
        errors = []
        temperature.operation_error.connect(errors.append)
        temperature.set_temperature_reading(100.0)
        temperature.start(180.0)
        self.assertTrue(temperature.is_active)
        process.set_plasma(True)

        allowed[0] = False
        temperature._check_runtime_conditions()

        self.assertFalse(temperature.is_active)
        self.assertFalse(process.plasma_active)
        self.assertFalse(self.hardware.digital_read("RF_ON_CMD"))
        self.assertFalse(self.hardware.digital_read("LAMP1_ON_CMD"))
        self.assertFalse(self.hardware.digital_read("LAMP2_ON_CMD"))
        self.assertFalse(self.hardware.digital_read("LAMP3_ON_CMD"))
        self.assertTrue(errors)

    def test_temperature_assist_pulse_uses_managed_outputs_and_stops_safely(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        process = ProcessController(self.hardware, can_operate=lambda: True)
        temperature = TemperatureController(process, can_operate=lambda: True)
        temperature.set_temperature_reading(100.0)
        temperature.start(180.0)
        # Complete the ramp (threshold is 162.25 °C for this start temp).
        for _ in range(11):
            temperature.set_temperature_reading(163.0)
        # Pass the upper threshold, then fall through the assist threshold.
        for _ in range(11):
            temperature.set_temperature_reading(188.0)
        for _ in range(11):
            temperature.set_temperature_reading(170.0)
        self.assertTrue(self.hardware.digital_read("LAMP1_ON_CMD"))
        self.assertTrue(self.hardware.digital_read("LAMP3_ON_CMD"))

        temperature.stop()
        self.assertFalse(temperature._assist_timer.isActive())
        for signal in ("LAMP1_ON_CMD", "LAMP2_ON_CMD", "LAMP3_ON_CMD"):
            self.assertFalse(self.hardware.digital_read(signal))

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
        recipe.n2_flow = 0.0
        with self.assertRaises(RecipeError):
            service.validate(recipe)
        recipe.n2_flow = 0.1
        with self.assertRaises(RecipeError):
            service.validate(recipe)

        recipe.process_pressure = 2.0
        recipe.base_pressure = 3.01
        with self.assertRaises(RecipeError):
            service.validate(recipe)

        recipe.base_pressure = 0.5
        recipe.process_temperature = 190.0
        service.validate(recipe)
        recipe.process_temperature = 200.0
        with self.assertRaises(RecipeError):
            service.validate(recipe)

        recipe.process_temperature = 150.0
        recipe.process_pressure = 1.13
        with self.assertRaises(RecipeError):
            service.validate(recipe)
        recipe.process_pressure = 1.14
        service.validate(recipe)

    def test_recipe_editor_saves_without_baratron_reading(self):
        recipe = Recipe(
            name="",
            description="",
            o2_flow=1.0,
            n2_flow=0.1,
            base_pressure=2.0,
            process_pressure=2.0,
            process_temperature=150.0,
        )
        with TemporaryDirectory() as folder:
            service = RecipeService(folder)
            editor = RecipeEditorDialog(
                recipe,
                save_callback=lambda candidate: service.save(candidate),
            )
            editor.name_edit.setText("dos_torr")
            editor.description_edit.setText("sin lectura BARATRON")
            with patch("gui.recipe_dialogs.QMessageBox.warning") as warning:
                editor._accept_recipe()
            warning.assert_not_called()
            self.assertEqual(editor.result(), editor.Accepted)
            self.assertEqual(editor.recipe.base_pressure, 2.0)
            self.assertTrue(editor.recipe.source_path.is_file())
            editor.close()

    def test_recipe_rf_time_defaults_for_legacy_files_and_round_trips(self):
        with TemporaryDirectory() as folder:
            service = RecipeService(folder)
            legacy_path = Path(folder) / "legacy.txt"
            legacy_path.write_text(
                "[RECIPE]\nname = legacy\ndescription = receta antigua\n\n"
                "[PARAMETERS]\no2_flow = 1\nn2_flow = 0.1\n"
                "base_pressure = 0.5\nprocess_pressure = 2\nprocess_temperature = 150\n",
                encoding="utf-8",
            )
            legacy = service.load_file(legacy_path)
            self.assertEqual(legacy.rf_max_on_time, 90)

            saved = service.save(Recipe(
                "configured", "receta", 1, 0.1, 0.5, 2, 150,
                rf_max_on_time=120,
            ))
            self.assertEqual(service.load_file(saved.source_path).rf_max_on_time, 120)

    def test_recipe_rf_time_requires_integer_between_one_and_one_hundred_twenty(self):
        service = RecipeService()
        recipe = Recipe("test", "test", 1, 0.1, 0.5, 2, 150)
        for value in (0, 121, 1.5):
            recipe.rf_max_on_time = value
            with self.assertRaises(RecipeError):
                service.validate(recipe)
        recipe.rf_max_on_time = 120
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

    def test_process_controller_exposes_outer_lamp_activity(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        controller = ProcessController(self.hardware, can_operate=lambda: True)

        self.assertFalse(controller.lamps13_active)
        self.assertTrue(controller.set_lamps13(True))
        self.assertTrue(controller.lamps13_active)
        self.assertTrue(controller.set_lamps13(False))
        self.assertFalse(controller.lamps13_active)

    def test_fault_input_read_error_raises_dedicated_monitoring_failure(self):
        controller = ProcessController(self.hardware, can_operate=lambda: True)
        controller._lamps13 = True
        failures = []
        controller.fault_monitoring_failed.connect(
            lambda source, message: failures.append((source, message))
        )

        digital_read = self.hardware.digital_read

        def fail_lamp_fault_read(name):
            if name == "LAMP1_FAIL":
                raise OSError("entrada desconectada")
            return digital_read(name)

        with patch.object(self.hardware, "digital_read", side_effect=fail_lamp_fault_read):
            controller.check_faults()

        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0][0], "Entradas de falla de proceso")
        self.assertIn("LAMP1_FAIL", failures[0][1])
        self.assertIn("entrada desconectada", failures[0][1])

    def test_safety_throttle_return_reaches_rest_and_releases_motor(self):
        self.hardware.digital_set("DRIVER_ENABLE", True)
        self.hardware.set_input_state("THROTTLE_OPEN", False)
        self.hardware.set_input_state("THROTTLE_CLOSED", False)
        controller = ThrottleController(self.hardware, can_operate=lambda: True)
        controller._position_steps = 398.0
        results = []
        controller.safety_return_finished.connect(
            lambda success, message: results.append((success, message))
        )

        self.assertTrue(controller.return_to_rest_for_safety())
        for _ in range(8):
            if not controller._timer.isActive():
                break
            controller._pulse()

        self.assertEqual(controller.position_steps, 400.0)
        self.assertFalse(controller.is_reserved_for_pressure)
        self.assertFalse(self.hardware.digital_read("STEPPER_OUTPUT_ENABLE"))
        self.assertEqual(results, [(True, "La throttle llegó a la posición de reposo.")])

    def test_critical_process_fault_closes_mfc1_and_mfc2(self):
        mfc = MFCController(self.hardware, can_operate=lambda: True)
        process = ProcessController(
            self.hardware,
            can_operate=lambda: True,
            mfc_controller=mfc,
        )
        valve_states = []
        alarms = []
        mfc.valve_state_changed.connect(
            lambda name, opened: valve_states.append((name, opened))
        )
        process.alarm_raised.connect(alarms.append)

        for name, flow in (("MFC1", 2.0), ("MFC2", 0.4)):
            mfc.set_flow(name, flow)
            mfc.set_valve(name, True)
        process.start_lamps13(10)
        self.hardware.set_input_state("LAMP1_FAIL", True)

        process.check_faults()

        for name in ("MFC1", "MFC2"):
            self.assertFalse(self.hardware.digital_read(f"{name}_OPEN"))
            self.assertEqual(self.hardware.get_analog_output(f"{name}_SETPOINT"), 0.0)
            self.assertIn((name, False), valve_states)
        self.assertTrue(alarms)
        self.assertFalse(self.hardware.digital_read("LAMP1_ON_CMD"))
        self.assertFalse(self.hardware.digital_read("LAMP3_ON_CMD"))
        process._pulse_timer.stop()

    def test_mfc_close_error_does_not_prevent_other_close_or_alarm(self):
        mfc = MFCController(self.hardware, can_operate=lambda: True)
        process = ProcessController(
            self.hardware,
            can_operate=lambda: True,
            mfc_controller=mfc,
        )
        alarms = []
        process.alarm_raised.connect(alarms.append)
        mfc.set_flow("MFC1", 2.0)
        mfc.set_flow("MFC2", 0.4)
        mfc.set_valve("MFC1", True)
        mfc.set_valve("MFC2", True)
        process.set_lamps13(True)
        self.hardware.set_input_state("LAMP1_FAIL", True)

        digital_set = self.hardware.digital_set

        def fail_mfc1_close(signal_name, active):
            if signal_name == "MFC1_OPEN" and not active:
                raise RuntimeError("falló la salida MFC1")
            digital_set(signal_name, active)

        with patch.object(self.hardware, "digital_set", side_effect=fail_mfc1_close):
            process.check_faults()

        self.assertTrue(self.hardware.digital_read("MFC1_OPEN"))
        self.assertFalse(self.hardware.digital_read("MFC2_OPEN"))
        self.assertEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 0.0)
        self.assertEqual(self.hardware.get_analog_output("MFC2_SETPOINT"), 0.0)
        self.assertTrue(alarms)

    def test_process_fault_inputs_high_at_rest_do_not_raise_alarm(self):
        controller = ProcessController(self.hardware, can_operate=lambda: True)
        alarms = []
        controller.alarm_raised.connect(alarms.append)
        for signal in ("LAMP1_FAIL", "LAMP2_FAIL", "LAMP3_FAIL", "PLASMA_FAIL"):
            self.hardware.set_input_state(signal, True)

        controller.check_faults()

        self.assertEqual(alarms, [])
        self.assertEqual(
            controller.fault_monitoring_state(),
            {"LAMP1_FAIL": False, "LAMP2_FAIL": False, "LAMP3_FAIL": False, "PLASMA_FAIL": False},
        )

    def test_low_fail_inputs_during_operation_do_not_raise_alarm(self):
        controller = ProcessController(self.hardware, can_operate=lambda: True)
        alarms = []
        controller.alarm_raised.connect(alarms.append)
        for signal in ("LAMP1_FAIL", "LAMP2_FAIL", "LAMP3_FAIL", "PLASMA_FAIL"):
            self.hardware.set_input_state(signal, False)
        controller.set_lamps13(True)
        controller.set_lamp2(True)
        controller.set_plasma(True)
        controller._plasma_started_at -= controller.IGNITION_DELAY_S + 1

        controller.check_faults()

        self.assertEqual(alarms, [])
        controller.stop_all()

    def test_each_lamp_fail_input_is_checked_only_for_its_active_lamp(self):
        for signal, message, activate in (
            ("LAMP1_FAIL", "Falla en lámpara 1", lambda c: c.set_lamps13(True)),
            ("LAMP3_FAIL", "Falla en lámpara 3", lambda c: c.set_lamps13(True)),
            ("LAMP2_FAIL", "Falla en lámpara 2", lambda c: c.set_lamp2(True)),
        ):
            with self.subTest(signal=signal):
                controller = ProcessController(self.hardware, can_operate=lambda: True)
                alarms = []
                controller.alarm_raised.connect(alarms.append)
                for input_name in ("LAMP1_FAIL", "LAMP2_FAIL", "LAMP3_FAIL"):
                    self.hardware.set_input_state(input_name, False)
                self.hardware.set_input_state(signal, True)
                activate(controller)
                controller.check_faults()
                self.assertTrue(alarms)
                self.assertIn(message, alarms[0])

    def test_plasma_fail_input_waits_for_ignition_grace_period(self):
        from unittest.mock import patch

        controller = ProcessController(self.hardware, can_operate=lambda: True)
        alarms = []
        controller.alarm_raised.connect(alarms.append)
        self.hardware.set_input_state("PLASMA_FAIL", True)
        with patch("controllers.process_controller.time.monotonic", return_value=10.0):
            controller.set_plasma(True)
            controller.check_faults()
            self.assertEqual(alarms, [])
        with patch("controllers.process_controller.time.monotonic", return_value=12.1):
            controller.check_faults()
        self.assertTrue(alarms)
        self.assertIn("Falla en plasma", alarms[0])

    def test_fail_signal_widget_shows_high_as_normal_until_monitoring(self):
        from gui.widgets.signal_widget import SignalWidget

        widget = SignalWidget("LAMP1_FAIL", interactive=False)
        widget.set_active(True)
        self.assertEqual(widget.property("semanticState"), "on")
        widget.set_fault_monitoring_enabled(True)
        self.assertEqual(widget.property("semanticState"), "fault")
        widget.set_fault_monitoring_enabled(False)
        self.assertEqual(widget.property("semanticState"), "on")

    def test_legacy_fault_monitor_ignores_high_inputs_at_rest(self):
        from logic.process_faults import check_process_faults

        class LegacyWindow:
            alarm_active = False
            state_lamps13_pulsing = False
            lamp2_on = False
            rf_on = False
            warning_mag_shown = False

        for signal in ("LAMP1_FAIL", "LAMP2_FAIL", "LAMP3_FAIL", "PLASMA_FAIL"):
            self.hardware.set_input_state(signal, True)
        check_process_faults(LegacyWindow(), self.hardware)


if __name__ == "__main__":
    unittest.main()
