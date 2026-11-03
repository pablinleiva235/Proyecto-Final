import unittest

from PyQt5.QtWidgets import QApplication

from gui.normal_operation_screen import NormalOperationScreen


class NormalOperationEquipmentStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_mock_mode_keeps_simulation_badge(self):
        screen = NormalOperationScreen(use_mock_hardware=True)

        screen.set_equipment_status("running")

        self.assertEqual(screen.simulation_badge.text(), "MODO SIMULADO")

    def test_real_hardware_displays_equipment_states(self):
        screen = NormalOperationScreen(use_mock_hardware=False)
        self.assertEqual(screen.simulation_badge.text(), "REPOSO")

        for state, expected in (
            ("running", "EN PROCESO"),
            ("finished", "TERMINADO"),
            ("idle", "REPOSO"),
        ):
            screen.set_equipment_status(state)
            self.assertEqual(screen.simulation_badge.text(), expected)


if __name__ == "__main__":
    unittest.main()
