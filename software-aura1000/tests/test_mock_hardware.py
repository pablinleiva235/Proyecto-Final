import unittest
from contextlib import redirect_stdout
from io import StringIO

from tests.mockScripts.mock_hardware import MockHardware


class MockHardwareTests(unittest.TestCase):
    def setUp(self):
        self.hardware = MockHardware()

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
        self.hardware.digital_set("SOFT_START_CONTROL", True)

        self.assertEqual(self.hardware.analog_read("BARATRON"), 0.1)
        self.assertFalse(self.hardware.digital_read("ATM_SWITCH"))

    def test_main_vacuum_sets_pressure_and_deactivates_atm_switch(self):
        self.hardware.set_input_state("ATM_SWITCH", True)
        self.hardware.digital_set("MAIN_VACUUM_CONTROL", True)

        self.assertEqual(self.hardware.analog_read("BARATRON"), 0.06)
        self.assertFalse(self.hardware.digital_read("ATM_SWITCH"))

    def test_input_setter_rejects_outputs(self):
        with self.assertRaises(ValueError):
            self.hardware.set_input_state("DRIVER_ENABLE", True)

    def test_analog_write_is_returned_by_analog_output_readback(self):
        self.hardware.analog_write("MFC1_SETPOINT", 2.5)

        self.assertEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 2.5)
        self.assertEqual(self.hardware.get_analog_output("MFC1_SETPOINT"), 2.5)


if __name__ == "__main__":
    unittest.main()
