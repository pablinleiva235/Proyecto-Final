import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.maintainer_screen import MaintainerScreen
from config_gui import strings


class MaintenanceRecordUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_save_button_fits_both_labels_without_changing_its_height_or_back_button(self):
        screen = MaintainerScreen()
        back_size = screen.back_button.size()
        record_height = screen.maintenance_record_button.height()
        for active, text in (
            (False, strings.MAINTENANCE_RECORD_START),
            (True, strings.MAINTENANCE_RECORD_STOP),
        ):
            screen.set_maintenance_recording(active)
            self.assertEqual(screen.maintenance_record_button.text(), text)
            self.assertEqual(screen.back_button.size(), back_size)
            self.assertEqual(screen.maintenance_record_button.height(), record_height)
            self.assertGreaterEqual(
                screen.maintenance_record_button.width(),
                screen.maintenance_record_button.fontMetrics().horizontalAdvance(text) + 48,
            )

    def test_stopping_recording_shows_saved_path_in_popup_and_clears_screen_message(self):
        path = "logs/mantenimiento_data/mantenimiento_test.csv"
        log = Mock(error=None, path=path)
        screen = Mock()
        fake = SimpleNamespace(
            _maintenance_data_log=log,
            _maintenance_sample_timer=Mock(),
            _maintenance_timeout_timer=Mock(),
            maintainer_screen=screen,
        )
        fake._finish_maintenance_recording = lambda message, error=False: (
            MainWindow._finish_maintenance_recording(fake, message, error)
        )
        with patch("gui.main_window.QMessageBox.information") as popup:
            MainWindow._stop_maintenance_recording(fake)

        log.close.assert_called_once()
        screen.set_maintenance_recording.assert_called_once_with(False)
        screen.set_operation_message.assert_called_once_with("")
        self.assertIn(path, popup.call_args.args[2])

    def test_write_error_is_shown_in_warning_popup(self):
        screen = Mock()
        fake = SimpleNamespace(
            _maintenance_data_log=None,
            _maintenance_sample_timer=Mock(),
            _maintenance_timeout_timer=Mock(),
            maintainer_screen=screen,
        )
        with patch("gui.main_window.QMessageBox.warning") as popup:
            MainWindow._finish_maintenance_recording(
                fake, "No se pudo guardar el registro: disco lleno", error=True
            )

        screen.set_operation_message.assert_called_once_with("")
        self.assertIn("disco lleno", popup.call_args.args[2])


if __name__ == "__main__":
    unittest.main()
