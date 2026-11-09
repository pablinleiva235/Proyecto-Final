import unittest

from PyQt5.QtWidgets import QApplication

from gui.normal_operation_screen import NormalOperationScreen


class NormalOperationEquipmentStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_both_modes_display_the_same_equipment_states(self):
        for use_mock_hardware in (True, False):
            with self.subTest(use_mock_hardware=use_mock_hardware):
                screen = NormalOperationScreen(
                    use_mock_hardware=use_mock_hardware
                )
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
