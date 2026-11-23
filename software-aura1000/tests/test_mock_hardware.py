import unittest
from contextlib import redirect_stdout
from io import StringIO
from PyQt5.QtCore import QCoreApplication, QEvent, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtTest import QTest

from tests.mockScripts.mock_hardware import MockHardware
from tests.mockScripts.controllers.simulation_controller import SimulationController


class MockHardwareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._qt_app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.hardware = MockHardware()

    def _set_throttle_steps(self, steps):
        current = self.hardware._throttle_position_steps
        direction = steps >= current
        self.hardware.digital_set("STEPPER_DIR", direction)
        for _ in range(abs(steps - current)):
            self.hardware.digital_set("STEPPER_STEP", True)
            self.hardware.digital_set("STEPPER_STEP", False)

    def _set_o2_flow(self, flow):
        voltage = flow / (10.0 * 0.981) * 5.0
        self.hardware.digital_set("MFC1_OPEN", True)
        self.hardware.analog_write("MFC1_SETPOINT", voltage)

    def test_eop_starts_at_zero_volts(self):
        self.assertEqual(self.hardware.analog_read("EOP"), 0.0)

    def test_eop_adjustment_changes_one_volt_and_stays_within_limits(self):
        self.hardware.adjust_eop(1)
        self.assertEqual(self.hardware.analog_read("EOP"), 1.0)
        self.hardware.adjust_eop(-1)
        self.assertEqual(self.hardware.analog_read("EOP"), 0.0)
        self.hardware.adjust_eop(-1)
        self.assertEqual(self.hardware.analog_read("EOP"), 0.0)

        for _ in range(11):
            self.hardware.adjust_eop(1)
        self.assertEqual(self.hardware.analog_read("EOP"), 10.0)

    def test_simulation_controller_maps_up_and_down_to_eop(self):
        controller = SimulationController(self.hardware)
        up = QKeyEvent(QEvent.KeyPress, Qt.Key_Up, Qt.NoModifier)
        down = QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.NoModifier)

        self.assertTrue(controller.eventFilter(None, up))
        self.assertEqual(self.hardware.analog_read("EOP"), 1.0)
        self.assertTrue(controller.eventFilter(None, down))
        self.assertEqual(self.hardware.analog_read("EOP"), 0.0)

    def test_digital_write_updates_state_and_reads_are_passive(self):
        output = StringIO()

        with redirect_stdout(output):
            self.hardware.digital_set("DRIVER_ENABLE", True)
            first_read = self.hardware.digital_read("DRIVER_ENABLE")
            second_read = self.hardware.digital_read("DRIVER_ENABLE")

        self.assertTrue(first_read)
        self.assertTrue(second_read)
        self.assertEqual(output.getvalue(), "")

    def test_device_commands_toggle_only_their_simulated_failure_inputs(self):
        command_failure_pairs = (
            ("LAMP1_ON_CMD", "LAMP1_FAIL"),
            ("LAMP2_ON_CMD", "LAMP2_FAIL"),
            ("LAMP3_ON_CMD", "LAMP3_FAIL"),
            ("RF_ON_CMD", "PLASMA_FAIL"),
        )
        initial_temperature = self.hardware.analog_read_temperature("CHAMBER_TEMP")

        for command, failure in command_failure_pairs:
            with self.subTest(command=command):
                self.assertTrue(self.hardware.digital_read(failure))
                for _other_command, other_failure in command_failure_pairs:
                    if other_failure != failure:
                        self.assertTrue(self.hardware.digital_read(other_failure))

                self.hardware.digital_set(command, True)
                self.assertFalse(self.hardware.digital_read(failure))
                self.hardware.digital_set(command, False)
                self.assertTrue(self.hardware.digital_read(failure))

        self.assertEqual(
            self.hardware.analog_read_temperature("CHAMBER_TEMP"),
            initial_temperature,
        )

    def test_temperature_heats_by_one_degree_per_second_with_only_lamp2(self):
        self.hardware.digital_set("LAMP2_ON_CMD", True)

        QTest.qWait(1050)

        self.assertEqual(self.hardware.analog_read_temperature("CHAMBER_TEMP"), 26.0)

    def test_temperature_heats_by_five_degrees_per_second_with_lamp1_or_lamp3(self):
        for lamp in ("LAMP1_ON_CMD", "LAMP3_ON_CMD"):
            with self.subTest(lamp=lamp):
                self.hardware = MockHardware()
                self.hardware.digital_set(lamp, True)

                QTest.qWait(1050)

                self.assertEqual(
                    self.hardware.analog_read_temperature("CHAMBER_TEMP"), 30.0
                )

    def test_all_lamps_heat_by_five_degrees_each_quarter_second_without_upper_limit(self):
        self.hardware.set_analog_value("CHAMBER_TEMP", 200.0)
        for lamp in ("LAMP1_ON_CMD", "LAMP2_ON_CMD", "LAMP3_ON_CMD"):
            self.hardware.digital_set(lamp, True)

        QTest.qWait(400)

        self.assertEqual(self.hardware.analog_read_temperature("CHAMBER_TEMP"), 205.0)

    def test_temperature_cools_slowly_with_rf_and_quickly_to_twenty_five_without_devices(self):
        self.hardware.set_analog_value("CHAMBER_TEMP", 26.0)
        self.hardware.digital_set("RF_ON_CMD", True)

        QTest.qWait(1050)

        self.assertEqual(self.hardware.analog_read_temperature("CHAMBER_TEMP"), 25.5)

        self.hardware.digital_set("RF_ON_CMD", False)
        self.hardware.set_analog_value("CHAMBER_TEMP", 37.0)
        self.hardware._configure_temperature_simulation()
        QTest.qWait(550)
        self.assertEqual(self.hardware.analog_read_temperature("CHAMBER_TEMP"), 27.0)

        self.hardware.set_analog_value("CHAMBER_TEMP", 27.0)
        self.hardware._configure_temperature_simulation()
        QTest.qWait(550)
        self.assertEqual(self.hardware.analog_read_temperature("CHAMBER_TEMP"), 25.0)

    def test_temperature_shortcuts_are_removed(self):
        controller = SimulationController(self.hardware)
        initial_temperature = self.hardware.analog_read_temperature("CHAMBER_TEMP")

        for key in (Qt.Key_4, Qt.Key_6):
            event = QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)
            self.assertFalse(controller.eventFilter(None, event))

        self.assertFalse(hasattr(self.hardware, "adjust_temperature"))
        self.assertEqual(
            self.hardware.analog_read_temperature("CHAMBER_TEMP"),
            initial_temperature,
        )

    def test_input_changes_only_when_explicitly_set(self):
        initial_state = self.hardware.digital_read("ATM_SWITCH")

        self.assertEqual(self.hardware.digital_read("ATM_SWITCH"), initial_state)
        self.hardware.set_input_state("ATM_SWITCH", not initial_state)
        self.assertEqual(self.hardware.digital_read("ATM_SWITCH"), not initial_state)

    def test_atm_switch_sets_baratron_pressure_and_pressure_is_retained(self):
        self.hardware.set_input_state("ATM_SWITCH", True)

        self.assertEqual(self.hardware.analog_read("BARATRON"), 10.0)
        self.hardware.set_input_state("ATM_SWITCH", False)
        self.assertEqual(self.hardware.analog_read("BARATRON"), 10.0)

    def test_vent_automatically_activates_atm_switch_after_delay(self):
        self.hardware.set_input_state("ATM_SWITCH", False)
        self.hardware.digital_set("VENT_VALVE_CONTROL", True)

        QTest.qWait(100)
        self.assertFalse(self.hardware.digital_read("ATM_SWITCH"))

        QTest.qWait(self.hardware._VENT_TO_ATM_DELAY_MS)
        self.assertTrue(self.hardware.digital_read("ATM_SWITCH"))
        self.assertEqual(self.hardware.analog_read("BARATRON"), 10.0)

    def test_closing_vent_valve_cancels_pending_atm_activation(self):
        self.hardware.set_input_state("ATM_SWITCH", False)
        self.hardware.digital_set("VENT_VALVE_CONTROL", True)
        QTest.qWait(100)
        self.hardware.digital_set("VENT_VALVE_CONTROL", False)

        QTest.qWait(self.hardware._VENT_TO_ATM_DELAY_MS)
        self.assertFalse(self.hardware.digital_read("ATM_SWITCH"))

    def test_soft_vacuum_sets_pressure_and_deactivates_atm_switch(self):
        self.hardware.set_input_state("ATM_SWITCH", True)
        self._set_throttle_steps(400)
        self.hardware.digital_set("SOFT_START_CONTROL", True)

        self.assertAlmostEqual(self.hardware.analog_read("BARATRON"), 0.83)
        self.assertFalse(self.hardware.digital_read("ATM_SWITCH"))

    def test_main_vacuum_sets_pressure_and_deactivates_atm_switch(self):
        self.hardware.set_input_state("ATM_SWITCH", True)
        self._set_throttle_steps(400)
        self.hardware.digital_set("MAIN_VACUUM_CONTROL", True)

        self.assertAlmostEqual(self.hardware.analog_read("BARATRON"), 0.83)
        self.assertFalse(self.hardware.digital_read("ATM_SWITCH"))

    def test_baratron_matches_reference_table_at_400_throttle_steps(self):
        expected = (0.83, 1.14, 1.51, 1.86, 2.23, 2.63, 3.0)
        self._set_throttle_steps(400)
        self.hardware.digital_set("MAIN_VACUUM_CONTROL", True)

        for flow, pressure in enumerate(expected):
            with self.subTest(o2_flow=flow):
                self._set_o2_flow(float(flow))
                self.assertAlmostEqual(
                    self.hardware.analog_read("MFC1_FLOW"),
                    flow / (10.0 * 0.981) * 5.0,
                )
                self.assertAlmostEqual(self.hardware.analog_read("BARATRON"), pressure)

    def test_baratron_interpolates_and_extrapolates_from_o2_flow(self):
        self._set_throttle_steps(400)
        self.hardware.digital_set("MAIN_VACUUM_CONTROL", True)

        self._set_o2_flow(2.5)
        self.assertAlmostEqual(self.hardware.analog_read("BARATRON"), 1.685)

        self._set_o2_flow(7.0)
        self.assertAlmostEqual(self.hardware.analog_read("BARATRON"), 3.37)

    def test_throttle_scales_pressure_and_pressure_is_clamped_to_ten_torr(self):
        self.hardware.digital_set("MAIN_VACUUM_CONTROL", True)
        self._set_o2_flow(6.0)
        self._set_throttle_steps(200)
        self.assertAlmostEqual(self.hardware.analog_read("BARATRON"), 1.5)
        self._set_throttle_steps(1200)
        self.assertEqual(self.hardware.analog_read("BARATRON"), 9.0)
        self._set_throttle_steps(1400)
        self.assertEqual(self.hardware.analog_read("BARATRON"), 10.0)

    def test_mfc_readings_follow_setpoints_and_are_independent_of_pressure(self):
        self.hardware.digital_set("MAIN_VACUUM_CONTROL", True)
        self.hardware.digital_set("MFC1_OPEN", True)
        self.hardware.digital_set("MFC2_OPEN", True)
        self._set_o2_flow(2.0)
        self.hardware.analog_write("MFC2_SETPOINT", 1.0)
        measured = (
            self.hardware.analog_read("MFC1_FLOW"),
            self.hardware.analog_read("MFC2_FLOW"),
        )

        self.assertAlmostEqual(measured[0], 2.0 / (10.0 * 0.981) * 5.0)
        self.assertAlmostEqual(measured[1], 1.0)

        self.hardware.set_input_state("ATM_SWITCH", True)
        self._set_throttle_steps(20)
        self.assertEqual(self.hardware.analog_read("BARATRON"), 10.0)
        self.assertEqual(
            (
                self.hardware.analog_read("MFC1_FLOW"),
                self.hardware.analog_read("MFC2_FLOW"),
            ),
            measured,
        )

    def test_mfc_setpoint_requires_open_valve_and_is_applied_when_opened(self):
        self.hardware.analog_write("MFC1_SETPOINT", 2.5)

        self.assertEqual(self.hardware.analog_read("MFC1_FLOW"), 0.0)
        self.assertEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 2.5)

        self.hardware.digital_set("MFC1_OPEN", True)
        self.assertEqual(self.hardware.analog_read("MFC1_FLOW"), 2.5)

        self.hardware.digital_set("MFC1_OPEN", False)
        self.assertEqual(self.hardware.analog_read("MFC1_FLOW"), 0.0)

    def test_mfc_valves_gate_their_flows_independently(self):
        self.hardware.analog_write("MFC1_SETPOINT", 2.0)
        self.hardware.analog_write("MFC2_SETPOINT", 1.0)

        self.hardware.digital_set("MFC1_OPEN", True)
        self.assertEqual(self.hardware.analog_read("MFC1_FLOW"), 2.0)
        self.assertEqual(self.hardware.analog_read("MFC2_FLOW"), 0.0)

        self.hardware.digital_set("MFC2_OPEN", True)
        self.assertEqual(self.hardware.analog_read("MFC2_FLOW"), 1.0)
        self.hardware.digital_set("MFC1_OPEN", False)
        self.assertEqual(self.hardware.analog_read("MFC1_FLOW"), 0.0)
        self.assertEqual(self.hardware.analog_read("MFC2_FLOW"), 1.0)

    def test_atm_switch_overrides_pressure_and_vacuum_restores_model(self):
        self._set_throttle_steps(400)
        self._set_o2_flow(3.0)
        self.hardware.digital_set("MAIN_VACUUM_CONTROL", True)
        self.hardware.set_input_state("ATM_SWITCH", True)
        self.assertEqual(self.hardware.analog_read("BARATRON"), 10.0)

        self.hardware.set_input_state("ATM_SWITCH", False)
        self.assertAlmostEqual(self.hardware.analog_read("BARATRON"), 1.86)

    def test_input_setter_rejects_outputs(self):
        with self.assertRaises(ValueError):
            self.hardware.set_input_state("DRIVER_ENABLE", True)

    def test_analog_write_is_returned_by_analog_output_readback(self):
        self.hardware.analog_write("MFC1_SETPOINT", 2.5)

        self.assertEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 2.5)
        self.assertEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 2.5)


if __name__ == "__main__":
    unittest.main()
