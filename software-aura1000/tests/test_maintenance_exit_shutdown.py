import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PyQt5.QtWidgets import QMessageBox

from gui.main_window import MainWindow


class MaintenanceExitShutdownTests(unittest.TestCase):
    def _window(self):
        return SimpleNamespace(
            _maintenance_shutdown_pending=False,
            _maintenance_shutdown_error=None,
            shutdown_sequence=Mock(),
            maintainer_screen=SimpleNamespace(back_button=Mock()),
            _show_welcome_screen=Mock(),
        )

    def test_declining_confirmation_keeps_maintenance_open(self):
        window = self._window()
        with patch("gui.main_window.QMessageBox.question", return_value=QMessageBox.No):
            MainWindow._request_maintenance_exit(window)

        window.shutdown_sequence.start.assert_not_called()
        window._show_welcome_screen.assert_not_called()

    def test_confirming_starts_shutdown_and_completion_returns_to_welcome(self):
        window = self._window()
        with patch("gui.main_window.QMessageBox.question", return_value=QMessageBox.Yes):
            MainWindow._request_maintenance_exit(window)

        window.shutdown_sequence.start.assert_called_once_with()
        window.maintainer_screen.back_button.setEnabled.assert_called_once_with(False)
        MainWindow._handle_maintenance_shutdown_completed(window)
        window._show_welcome_screen.assert_called_once_with()
        window.maintainer_screen.back_button.setEnabled.assert_called_with(True)

    def test_shutdown_error_is_shown_before_returning_to_welcome(self):
        window = self._window()
        window._maintenance_shutdown_pending = True
        MainWindow._handle_maintenance_shutdown_error(window, "Falla de hardware")

        with patch("gui.main_window.QMessageBox.warning") as warning:
            MainWindow._handle_maintenance_shutdown_completed(window)

        self.assertIn("Falla de hardware", warning.call_args.args[2])
        window._show_welcome_screen.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
