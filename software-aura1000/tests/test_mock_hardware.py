import unittest
from contextlib import redirect_stdout
from io import StringIO

from tests.mockScripts.mock_hardware import MockHardware


class MockHardwareTests(unittest.TestCase):
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
        self.hardware.analog_write("MFC1_SETPOINT", voltage)

    def test_eop_starts_at_ten_volts(self):
        self.assertEqual(self.hardware.analog_read("EOP"), 10.0)

    def test_digital_write_updates_state_and_reads_are_passive(self):
        output = StringIO()

        with redirect_stdout(output):
            self.hardware.digital_set("DRIVER_ENABLE", True)
            first_read = self.hardware.digital_read("DRIVER_ENABLE")
            second_read = self.hardware.digital_read("DRIVER_ENABLE")

        self.assertTrue(first_read)
        self.assertTrue(second_read)
        self.assertEqual(output.getvalue(), "")

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
