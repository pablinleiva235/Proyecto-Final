import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QPixmap, QTextCursor

from gui import statistics_screen as statistics_module
from gui.statistics_screen import CombinedProcessPlot, StatisticsScreen
from config_gui.theme import THEMES


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
            with patch.object(statistics_module, "RECIPE_LOG_DIRECTORY", directory), \
                    patch.object(statistics_module, "MAINTENANCE_DATA_DIRECTORY", directory):
                screen = StatisticsScreen()

            self.assertEqual(screen.data_path, newest)
            self.assertEqual(screen.pressure_temperature_plot.points_for("BARATRON"), [(0.0, 0.8)])
            self.assertIn(newest.name, screen.subtitle_label.text())
            self.assertIn("1 lecturas", screen.subtitle_label.text())
            self.assertEqual(screen.refresh_button.text(), "Cargar archivo")

    def test_selecting_csv_loads_its_data_and_cancel_keeps_current_data(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            first = directory / "recipe_data_1.csv"
            second = directory / "recipe_data_2.csv"
            self._write_csv(first, 0.5)
            self._write_csv(second, 0.9)
            with patch.object(statistics_module, "RECIPE_LOG_DIRECTORY", directory), \
                    patch.object(statistics_module, "MAINTENANCE_DATA_DIRECTORY", directory):
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
                self.assertEqual(screen.pressure_temperature_plot.points_for("BARATRON"), [(0.0, 0.9)])

                previous_points = list(screen.pressure_temperature_plot.points_for("BARATRON"))
                with patch.object(
                    statistics_module.QFileDialog,
                    "getOpenFileName",
                    return_value=("", ""),
                ):
                    screen.choose_data_file()
                self.assertEqual(screen.pressure_temperature_plot.points_for("BARATRON"), previous_points)
                self.assertEqual(screen.data_path, second)

    def test_empty_directory_does_not_open_dialog_or_load_data(self):
        with TemporaryDirectory() as temp_dir:
            with patch.object(
                statistics_module, "RECIPE_LOG_DIRECTORY", Path(temp_dir)
            ), patch.object(
                statistics_module, "MAINTENANCE_DATA_DIRECTORY", Path(temp_dir)
            ):
                screen = StatisticsScreen()
                self.assertIsNone(screen.data_path)
                self.assertEqual(screen.pressure_temperature_plot.points_for("BARATRON"), [])
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
                previous_points = list(screen.pressure_temperature_plot.points_for("BARATRON"))
                with patch.object(
                    statistics_module.QFileDialog,
                    "getOpenFileName",
                    return_value=(str(bad), "CSV (*.csv)"),
                ):
                    screen.choose_data_file()

            self.assertEqual(screen.pressure_temperature_plot.points_for("BARATRON"), previous_points)
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

            self.assertEqual(screen.pressure_temperature_plot.points_for("BARATRON"), [(0.0, 0.2), (1.0, 0.3)])
            self.assertEqual(screen.pressure_temperature_plot.points_for("CHAMBER_TEMP"), [(0.0, 30.0), (1.0, 31.0)])
            self.assertEqual(screen.mfc_plot.points_for("MFC1_FLOW"), [(0.0, 1.1), (1.0, 1.2)])
            self.assertEqual(screen.mfc_plot.points_for("MFC2_FLOW"), [(0.0, 0.3), (1.0, 0.4)])
            self.assertEqual(screen.throttle_plot.points, [(0.0, 20.0), (1.0, 21.0)])
            self.assertEqual(screen.plasma_plot.points, [(0.0, 0.0), (1.0, 1.0)])

            self.assertTrue(screen.pressure_temperature_plot.dual_axis)
            self.assertEqual(screen.pressure_temperature_plot.series["BARATRON"]["unit"], "Torr")
            self.assertEqual(screen.pressure_temperature_plot.series["CHAMBER_TEMP"]["unit"], "°C")
            self.assertFalse(screen.mfc_plot.dual_axis)
            self.assertEqual(screen.mfc_plot.series["MFC1_FLOW"]["unit"], "SLPM")
            self.assertEqual(screen.mfc_plot.series["MFC1_FLOW"]["label"], "MFC1 · O₂")
            self.assertEqual(screen.mfc_plot.series["MFC2_FLOW"]["label"], "MFC2 · N₂")

    def test_combined_plots_ignore_invalid_values_and_missing_signals(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mantenimiento_1.csv"
            path.write_text(
                "timestamp,pressure_Torr,temperature_C,MFC1_flow_SLPM,MFC2_flow_SLPM\n"
                "2026-11-03T12:00:00-03:00,0.2,bad,1.1,\n"
                "2026-11-03T12:00:01-03:00,,31,NaN,0.4\n",
                encoding="utf-8",
            )
            screen = StatisticsScreen(data_path=path)

        self.assertEqual(screen.pressure_temperature_plot.points_for("BARATRON"), [(0.0, 0.2)])
        self.assertEqual(screen.pressure_temperature_plot.points_for("CHAMBER_TEMP"), [(1.0, 31.0)])
        self.assertEqual(screen.mfc_plot.points_for("MFC1_FLOW"), [(0.0, 1.1)])
        self.assertEqual(screen.mfc_plot.points_for("MFC2_FLOW"), [(1.0, 0.4)])

    def test_combined_plots_render_without_qpainter_errors(self):
        plots = (
            CombinedProcessPlot(
                "Presión y temperatura",
                (("BARATRON", "Presión", "Torr", "#38BDF8"),
                 ("CHAMBER_TEMP", "Temperatura", "°C", "#FACC15")),
                dual_axis=True,
            ),
            CombinedProcessPlot(
                "Caudales MFC",
                (("MFC1_FLOW", "MFC1", "SLPM", "#34D399"),
                 ("MFC2_FLOW", "MFC2", "SLPM", "#A78BFA")),
            ),
        )
        for plot in plots:
            plot.resize(800, 220)
            for signal in plot.series:
                plot.set_points(signal, [(0.0, 1.0), (10.0, 2.0)])
            pixmap = QPixmap(plot.size())
            plot.render(pixmap)

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
            self.assertEqual(screen.pressure_temperature_plot.points_for("BARATRON"), [(0.0, 0.8)])

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

        self.assertEqual(screen.pressure_temperature_plot.points_for("BARATRON"), [(0.0, 0.4)])
        self.assertEqual(screen.pressure_temperature_plot.points_for("CHAMBER_TEMP"), [(0.0, 80.0)])
        self.assertEqual(screen.mfc_plot.points_for("MFC1_FLOW"), [(0.0, 1.5)])
        self.assertEqual(screen.mfc_plot.points_for("MFC2_FLOW"), [(0.0, 0.2)])
        self.assertEqual(screen.throttle_plot.points, [(0.0, 120.0)])
        self.assertEqual(screen.plasma_plot.points, [(0.0, 1.0)])

    def test_loads_most_recent_recipe_or_shutdown_log(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            recipes = root / "recetas"
            shutdowns = root / "shutdown"
            recipes.mkdir()
            shutdowns.mkdir()
            recipe = recipes / "recipe_1.log"
            shutdown = shutdowns / "shutdown_1.log"
            recipe.write_text("evento receta\n", encoding="utf-8")
            shutdown.write_text("evento apagado\n", encoding="utf-8")
            os.utime(recipe, (1000, 1000))
            os.utime(shutdown, (2000, 2000))
            with patch.object(statistics_module, "RECIPE_LOG_DIRECTORY", recipes), \
                    patch.object(statistics_module, "SHUTDOWN_LOG_DIRECTORY", shutdowns):
                screen = StatisticsScreen()

            self.assertEqual(screen.log_path, shutdown)
            self.assertEqual(screen.logs_view.toPlainText(), "evento apagado\n")
            self.assertEqual(screen.logs_title_label.text(), shutdown.name)
            self.assertEqual(screen.tabs.tabText(0), "Datos")
            self.assertEqual(screen.tabs.tabText(1), "Logs")

    def test_selecting_log_and_canceling_preserves_current_view(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            first = directory / "recipe_1.log"
            second = directory / "shutdown_1.log"
            first.write_text("primero", encoding="utf-8")
            second.write_text("segundo", encoding="utf-8")
            with patch.object(statistics_module, "RECIPE_LOG_DIRECTORY", directory), \
                    patch.object(statistics_module, "SHUTDOWN_LOG_DIRECTORY", directory):
                screen = StatisticsScreen()
                with patch.object(
                    statistics_module.QFileDialog,
                    "getOpenFileName",
                    return_value=(str(second), "Logs (*.log)"),
                ) as dialog:
                    screen.choose_log_file()
                self.assertEqual(dialog.call_args.args[3], "Logs (*.log)")
                self.assertEqual(screen.log_path, second)
                self.assertEqual(screen.logs_view.toPlainText(), "segundo")
                with patch.object(
                    statistics_module.QFileDialog,
                    "getOpenFileName",
                    return_value=("", ""),
                ):
                    screen.choose_log_file()
                self.assertEqual(screen.log_path, second)
                self.assertEqual(screen.logs_view.toPlainText(), "segundo")

    def test_empty_and_unreadable_logs_are_reported(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            with patch.object(statistics_module, "RECIPE_LOG_DIRECTORY", directory), \
                    patch.object(statistics_module, "SHUTDOWN_LOG_DIRECTORY", directory):
                screen = StatisticsScreen()
                self.assertIsNone(screen.log_path)
                self.assertIn("No hay registros", screen.logs_title_label.text())
                bad = directory / "recipe_1.log"
                bad.write_bytes(b"\xff\xfe\xfa")
                self.assertFalse(screen._load_log_file(bad))
                self.assertIn("No se pudo cargar", screen.logs_title_label.text())
                self.assertIn(bad.name, screen.logs_title_label.text())

    def test_shared_load_button_uses_active_tab_and_footer_has_two_columns(self):
        screen = StatisticsScreen(data_path=Path("missing.csv"))
        screen.data_path = None
        with patch.object(screen, "choose_data_file") as choose_data, \
                patch.object(screen, "choose_log_file") as choose_log:
            screen.tabs.setCurrentIndex(0)
            screen.load_file_button.click()
            choose_data.assert_called_once_with()
            choose_log.assert_not_called()

            choose_data.reset_mock()
            screen.tabs.setCurrentIndex(1)
            screen.load_file_button.click()
            choose_log.assert_called_once_with()
            choose_data.assert_not_called()

        self.assertEqual(screen.footer_buttons.count(), 2)
        self.assertIs(screen.footer_buttons.itemAt(0).widget(), screen.load_file_button)
        self.assertIs(screen.footer_buttons.itemAt(1).widget(), screen.back_button)
        self.assertEqual(screen.tabs.objectName(), "StatisticsTabs")

    def test_back_button_still_emits_navigation_signal(self):
        screen = StatisticsScreen(data_path=Path("missing.csv"))
        emitted = []
        screen.back_requested.connect(lambda: emitted.append(True))
        screen.back_button.click()
        self.assertEqual(emitted, [True])

    def test_log_view_formats_timestamp_title_and_alternating_theme_colors(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "recipe_1.log"
            content = (
                "2026-11-04T14:20:39.164-03:00 | evento receta\n"
                "\n"
                "línea sin fecha"
            )
            path.write_text(content, encoding="utf-8")
            screen = StatisticsScreen(data_path=Path("missing.csv"))
            self.assertTrue(screen._load_log_file(path))

            self.assertEqual(screen.logs_title_label.alignment(), Qt.AlignCenter)
            self.assertTrue(screen.logs_title_label.font().bold())
            self.assertEqual(screen.logs_view.toPlainText(), content)

            cursor = QTextCursor(screen.logs_view.document())
            cursor.setPosition(0)
            cursor.setPosition(len("2026-11-04T14:20:39.164-03:00"), QTextCursor.KeepAnchor)
            self.assertEqual(cursor.selectedText(), "2026-11-04T14:20:39.164-03:00")
            self.assertEqual(
                cursor.charFormat().foreground().color().name(),
                THEMES["dark"]["primary"].lower(),
            )
            self.assertEqual(cursor.charFormat().fontWeight(), QFont.Bold)

            def block_backgrounds():
                block = screen.logs_view.document().begin()
                result = []
                while block.isValid():
                    result.append(block.blockFormat().background().color().name())
                    block = block.next()
                return result

            self.assertEqual(
                block_backgrounds(),
                [color.lower() for color in (
                    THEMES["dark"]["background"],
                    THEMES["dark"]["surface"],
                    THEMES["dark"]["background"],
                )],
            )

            screen.set_theme("light")
            self.assertEqual(
                block_backgrounds(),
                [color.lower() for color in (
                    THEMES["light"]["background"],
                    THEMES["light"]["surface"],
                    THEMES["light"]["background"],
                )],
            )
            cursor = QTextCursor(screen.logs_view.document())
            cursor.setPosition(0)
            cursor.setPosition(len("2026-11-04T14:20:39.164-03:00"), QTextCursor.KeepAnchor)
            self.assertEqual(
                cursor.charFormat().foreground().color().name(),
                THEMES["light"]["primary"].lower(),
            )


if __name__ == "__main__":
    unittest.main()
