import unittest
from unittest.mock import Mock, call

from PyQt5.QtCore import QRectF
from PyQt5.QtWidgets import QApplication

from gui.normal_operation_screen import NormalOperationScreen
from gui.widgets.schematic_diagram import SchematicDiagramWidget


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


class SchematicDiagramTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_assets_load_for_both_themes_and_theme_change_preserves_state(self):
        diagram = SchematicDiagramWidget()
        self.assertTrue(diagram.assets_available)

        diagram.set_pump_state("alert")
        self.assertTrue(diagram.assets_available)
        diagram.set_valve_state("left_valve_1", "half")
        diagram.set_theme("light")

        self.assertTrue(diagram.assets_available)
        self.assertEqual(diagram.theme, "light")
        self.assertEqual(diagram._states["left_valve_1"], "half")
        self.assertEqual(diagram._states["left_valve_2"], "close")

    def test_component_state_updates_only_selected_component(self):
        diagram = SchematicDiagramWidget()

        diagram.set_pump_state("open")
        diagram.set_mfc_state("mfc_o2", "alert")
        diagram.set_chamber_state("plasma")

        self.assertEqual(diagram._states["pump"], "open")
        self.assertEqual(diagram._states["mfc_o2"], "alert")
        self.assertEqual(diagram._states["chamber"], "plasma")
        self.assertEqual(diagram._states["mfc_n2"], "idle")
        self.assertEqual(diagram._states["right_valve_1"], "close")

    def test_unavailable_component_state_is_rejected(self):
        diagram = SchematicDiagramWidget()

        with self.assertRaises(ValueError):
            diagram.set_component_state("arm", "open")

    def test_valve_rendering_applies_orientation_by_position(self):
        rect = QRectF(10, 20, 100, 80)
        center = rect.center()

        for name in (
            "left_valve_1",
            "right_valve_1",
            "vent_valve",
        ):
            with self.subTest(name=name):
                painter = Mock()
                renderer = Mock()

                SchematicDiagramWidget._render_valve(painter, renderer, name, rect)

                renderer.render.assert_called_once_with(painter, rect)
                painter.save.assert_called_once_with()
                painter.restore.assert_called_once_with()
                if name == "left_valve_1":
                    painter.translate.assert_not_called()
                    painter.scale.assert_not_called()
                    painter.rotate.assert_not_called()
                elif name == "right_valve_1":
                    painter.translate.assert_has_calls([call(center), call(-center)])
                    painter.scale.assert_called_once_with(-1, 1)
                    painter.rotate.assert_not_called()
                else:
                    painter.translate.assert_has_calls([call(center), call(-center)])
                    painter.rotate.assert_called_once_with(-90)
                    painter.scale.assert_not_called()

    def test_requested_component_and_label_offsets(self):
        components = SchematicDiagramWidget.COMPONENTS
        for name in (
            "left_valve_1", "left_valve_2", "left_valve_3",
            "right_valve_1", "right_valve_2", "right_valve_3",
        ):
            with self.subTest(component=name):
                self.assertEqual(components[name][2].y(),
                                 {"left_valve_1": 67, "left_valve_2": 191,
                                  "left_valve_3": 315, "right_valve_1": 67,
                                  "right_valve_2": 191, "right_valve_3": 315}[name])

        self.assertEqual(components["vent_valve"][2].x(), 430)
        self.assertEqual(components["chamber"][2].y(), 317)
        self.assertEqual(components["magnetron"][2].y(), 370)
        self.assertEqual(
            [components[name][2].y() for name in ("mfc_o2", "mfc_n2", "mfc_aux")],
            [79, 203, 327],
        )
        self.assertEqual(
            [label[2] for label in SchematicDiagramWidget.LABELS if label[0].startswith("MFC")],
            [185, 309, 433],
        )
        chamber_open_rect = SchematicDiagramWidget._component_render_rect(
            "chamber", components["chamber"][2], "open"
        )
        self.assertEqual(chamber_open_rect.y(), 267)


if __name__ == "__main__":
    unittest.main()
