import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication

from gui import statistics_screen as statistics_module
from gui.statistics_screen import StatisticsScreen


class StatisticsScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _write_csv(self, path, value):
        path.write_text(
            "timestamp,signal,value,unit\n"
            f"2026-10-26T14:25:30-03:00,BARATRON,{value},Torr\n",
            encoding="utf-8",
        )

    def test_loads_most_recent_recipe_csv_and_shows_filename(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            older = directory / "recipe_data_1.csv"
            newest = directory / "recipe_data_2.csv"
            self._write_csv(older, 0.5)
            self._write_csv(newest, 0.8)
            os.utime(older, (1000, 1000))
            os.utime(newest, (2000, 2000))
            with patch.object(statistics_module, "RECIPE_LOG_DIRECTORY", directory):
                screen = StatisticsScreen()

            self.assertEqual(screen.data_path, newest)
            self.assertEqual(screen.pressure_plot.points, [(0.0, 0.8)])
            self.assertIn(newest.name, screen.subtitle_label.text())
            self.assertIn("1 lecturas", screen.subtitle_label.text())
            self.assertEqual(screen.refresh_button.text(), "Cargar datos")

    def test_selecting_csv_loads_its_data_and_cancel_keeps_current_data(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            first = directory / "recipe_data_1.csv"
            second = directory / "recipe_data_2.csv"
            self._write_csv(first, 0.5)
            self._write_csv(second, 0.9)
            with patch.object(statistics_module, "RECIPE_LOG_DIRECTORY", directory):
                screen = StatisticsScreen(data_path=first)
                with patch.object(
                    statistics_module.QFileDialog,
                    "getOpenFileName",
                    return_value=(str(second), "CSV (*.csv)"),
                ) as dialog:
                    screen.choose_data_file()
                    self.assertEqual(dialog.call_args.args[2], str(directory))
                    self.assertEqual(dialog.call_args.args[3], "CSV (*.csv)")
                self.assertEqual(screen.data_path, second)
                self.assertEqual(screen.pressure_plot.points, [(0.0, 0.9)])

                previous_points = list(screen.pressure_plot.points)
                with patch.object(
                    statistics_module.QFileDialog,
                    "getOpenFileName",
                    return_value=("", ""),
                ):
                    screen.choose_data_file()
                self.assertEqual(screen.pressure_plot.points, previous_points)
                self.assertEqual(screen.data_path, second)

    def test_empty_directory_does_not_open_dialog_or_load_data(self):
        with TemporaryDirectory() as temp_dir:
            with patch.object(
                statistics_module, "RECIPE_LOG_DIRECTORY", Path(temp_dir)
            ):
                screen = StatisticsScreen()
                self.assertIsNone(screen.data_path)
                self.assertEqual(screen.pressure_plot.points, [])
                with patch.object(statistics_module.QFileDialog, "getOpenFileName") as dialog:
                    screen.choose_data_file()
                dialog.assert_not_called()

    def test_unreadable_selected_file_reports_error_and_keeps_existing_plot(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            good = directory / "recipe_data_1.csv"
            bad = directory / "recipe_data_2.csv"
            self._write_csv(good, 0.5)
            bad.write_bytes(b"\xff\xfe\xfa")
            with patch.object(statistics_module, "RECIPE_LOG_DIRECTORY", directory):
                screen = StatisticsScreen(data_path=good)
                previous_points = list(screen.pressure_plot.points)
                with patch.object(
                    statistics_module.QFileDialog,
                    "getOpenFileName",
                    return_value=(str(bad), "CSV (*.csv)"),
                ):
                    screen.choose_data_file()

            self.assertEqual(screen.pressure_plot.points, previous_points)
            self.assertEqual(screen.data_path, good)
            self.assertIn("No se pudo cargar", screen.subtitle_label.text())
            self.assertIn(bad.name, screen.subtitle_label.text())

    def test_loads_maintenance_csv_and_plots_all_recorded_signals(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            path = directory / "mantenimiento_1.csv"
            path.write_text(
                "timestamp,pressure_Torr,temperature_C,MFC1_flow_SLPM,MFC2_flow_SLPM,"
                "throttle_position_steps,plasma_state\n"
                "2026-11-03T12:00:00-03:00,0.2,30,1.1,0.3,20,OFF\n"
                "2026-11-03T12:00:01-03:00,0.3,31,1.2,0.4,21,ON\n",
                encoding="utf-8",
            )
            with patch.object(statistics_module, "MAINTENANCE_DATA_DIRECTORY", directory):
                screen = StatisticsScreen(data_path=path)

            self.assertEqual(screen.pressure_plot.points, [(0.0, 0.2), (1.0, 0.3)])
            self.assertEqual(screen.temperature_plot.points, [(0.0, 30.0), (1.0, 31.0)])
            self.assertEqual(screen.mfc1_plot.points, [(0.0, 1.1), (1.0, 1.2)])
            self.assertEqual(screen.mfc2_plot.points, [(0.0, 0.3), (1.0, 0.4)])
            self.assertEqual(screen.throttle_plot.points, [(0.0, 20.0), (1.0, 21.0)])
            self.assertEqual(screen.plasma_plot.points, [(0.0, 0.0), (1.0, 1.0)])

    def test_latest_data_includes_maintenance_logs(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            recipe = directory / "recipe_data_1.csv"
            maintenance = directory / "mantenimiento_1.csv"
            self._write_csv(recipe, 0.5)
            maintenance.write_text(
                "timestamp,pressure_Torr\n2026-11-03T12:00:00-03:00,0.8\n",
                encoding="utf-8",
            )
            os.utime(recipe, (1000, 1000))
            os.utime(maintenance, (2000, 2000))
            with patch.object(statistics_module, "RECIPE_LOG_DIRECTORY", directory), \
                    patch.object(statistics_module, "RECIPE_DATA_PATH", directory / "recipe_data.csv"), \
                    patch.object(statistics_module, "MAINTENANCE_DATA_DIRECTORY", directory):
                screen = StatisticsScreen()

            self.assertEqual(screen.data_path, maintenance)
            self.assertEqual(screen.pressure_plot.points, [(0.0, 0.8)])

    def test_loads_wide_recipe_csv_with_all_maintenance_signals(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "recipe_data_1.csv"
            path.write_text(
                "timestamp,pressure_Torr,temperature_C,MFC1_flow_SLPM,MFC2_flow_SLPM,"
                "throttle_position_steps,plasma_state\n"
                "2026-11-03T12:00:00-03:00,0.4,80,1.5,0.2,120,ON\n",
                encoding="utf-8",
            )
            screen = StatisticsScreen(data_path=path)

        self.assertEqual(screen.pressure_plot.points, [(0.0, 0.4)])
        self.assertEqual(screen.temperature_plot.points, [(0.0, 80.0)])
        self.assertEqual(screen.mfc1_plot.points, [(0.0, 1.5)])
        self.assertEqual(screen.mfc2_plot.points, [(0.0, 0.2)])
        self.assertEqual(screen.throttle_plot.points, [(0.0, 120.0)])
        self.assertEqual(screen.plasma_plot.points, [(0.0, 1.0)])


if __name__ == "__main__":
    unittest.main()
