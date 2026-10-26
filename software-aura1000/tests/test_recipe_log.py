import re
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from gui.main_window import MainWindow
from services.recipe_log import ANALOG_UNITS, RecipeDataLog, RecipeLog


class RecipeLogTests(unittest.TestCase):
    def test_records_iso_timestamp_snapshot_and_overwrites_previous_run(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "recipe.log"
            first = RecipeLog(path)
            readings = {
                "EOP": (1.95, "2026-10-26T14:25:31.125-03:00"),
                "BARATRON": (0.8, "2026-10-26T14:25:30.875-03:00"),
            }
            self.assertTrue(first.record("FIN DE PLASMA", readings))
            first.close()
            first_run = path.read_text(encoding="utf-8")
            self.assertRegex(first_run, r"^\d{4}-\d\d-\d\dT.*\| FIN DE PLASMA \|")
            self.assertIn("EOP=1.95 V (lectura 2026-10-26T14:25:31.125-03:00)", first_run)
            self.assertIn("BARATRON=0.8 Torr", first_run)
            for name in ANALOG_UNITS:
                if name not in readings:
                    self.assertIn(f"{name}=NO DISPONIBLE", first_run)

            second = RecipeLog(path)
            self.assertTrue(second.record("SEGUNDA EJECUCION", {}))
            second.close()
            latest_run = path.read_text(encoding="utf-8")
            self.assertIn("SEGUNDA EJECUCION", latest_run)
            self.assertNotIn("FIN DE PLASMA", latest_run)

    def test_records_logical_outputs_and_setpoints(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "recipe.log"
            log = RecipeLog(path)
            self.assertTrue(log.record(
                "ACCION: Abrir puerta", {},
                outputs={"DOOR_CLOSE_CMD": False, "DOOR_OPEN_CMD": True,
                         "MFC1_SETPOINT": "2.5 V"},
            ))
            log.close()
            line = path.read_text(encoding="utf-8")
            self.assertIn("Salidas: DOOR_CLOSE_CMD=INACTIVO, DOOR_OPEN_CMD=ACTIVO, MFC1_SETPOINT=2.5 V", line)
            self.assertIn("EOP=NO DISPONIBLE", line)

    def test_recipe_data_csv_records_each_signal_and_overwrites(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "recipe_data.csv"
            first = RecipeDataLog(path)
            self.assertTrue(first.record("BARATRON", 0.82, "2026-10-26T14:25:30.875-03:00"))
            self.assertTrue(first.record("CHAMBER_TEMP", 154.5, "2026-10-26T14:25:30.975-03:00"))
            first.close()
            rows = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(rows[0], "timestamp,señal,valor,unidad")
            self.assertIn("2026-10-26T14:25:30.875-03:00,BARATRON,0.82,Torr", rows)
            self.assertIn("2026-10-26T14:25:30.975-03:00,CHAMBER_TEMP,154.5,°C", rows)

            second = RecipeDataLog(path)
            self.assertTrue(second.record("BARATRON", 0.4, "2026-10-26T14:26:00.000-03:00"))
            second.close()
            content = path.read_text(encoding="utf-8")
            self.assertIn("0.4,Torr", content)
            self.assertNotIn("0.82,Torr", content)

    def test_completion_popup_includes_saved_log_path(self):
        class DummyScreen:
            def set_recipe_status(self, _status):
                pass

            def set_recipe_running(self, _running):
                pass

        class DummyMaintainer:
            def set_manual_controls_locked(self, _locked):
                pass

        class DummySequence:
            log_saved = True
            log_path = Path("logs/recipe.log")
            data_log_saved = True
            data_log_path = Path("logs/recipe_data.csv")

        class DummyWindow:
            normal_operation_screen = DummyScreen()
            maintainer_screen = DummyMaintainer()
            recipe_sequence = DummySequence()

            def _sync_module_permissions(self):
                pass

        with patch("gui.main_window.QMessageBox.information") as popup:
            MainWindow._handle_recipe_finished(DummyWindow(), True, "Receta completada.")
        self.assertIn("logs\\recipe.log", popup.call_args.args[2])
        self.assertIn("logs\\recipe_data.csv", popup.call_args.args[2])

    def test_completion_popup_reports_attempted_path_when_log_failed(self):
        class DummyScreen:
            def set_recipe_status(self, _status):
                pass

            def set_recipe_running(self, _running):
                pass

        class DummyMaintainer:
            def set_manual_controls_locked(self, _locked):
                pass

        class DummySequence:
            log_saved = False
            log_path = Path("logs/recipe.log")
            data_log_saved = False
            data_log_path = Path("logs/recipe_data.csv")

        class DummyWindow:
            normal_operation_screen = DummyScreen()
            maintainer_screen = DummyMaintainer()
            recipe_sequence = DummySequence()

            def _sync_module_permissions(self):
                pass

        with patch("gui.main_window.QMessageBox.warning") as popup:
            MainWindow._handle_recipe_finished(DummyWindow(), False, "No se pudo escribir.")
        self.assertIn("Ruta intentada", popup.call_args.args[2])
        self.assertIn("logs\\recipe.log", popup.call_args.args[2])
        self.assertIn("Ruta intentada", popup.call_args.args[2])
        self.assertIn("logs\\recipe_data.csv", popup.call_args.args[2])


if __name__ == "__main__":
    unittest.main()
