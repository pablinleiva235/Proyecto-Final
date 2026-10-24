"""Regresiones para el cierre de ventanas y tareas Qt."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QEvent, QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication

from controllers.application_controller import ApplicationController
from controllers.power_controller import PowerController
from controllers.shutdown_controller import ShutdownController
from controllers.startup_controller import StartupController
from gui.main_window import MainWindow
from gui.recipe_dialogs import RecipeEditorDialog, RecipeViewerDialog
from gui.startup_screen import StartupScreen
from services.recipe_service import Recipe
from logic.door_sequence import DoorSequence
from logic.main_vacuum_sequence import MainVacuumSequence
from logic.shutdown_sequence import ShutdownSequence
from logic.soft_vacuum_sequence import SoftVacuumSequence
from logic.startup_sequence import StartupSequence
from logic.vent_sequence import VentSequence
from tests.mockScripts.mock_hardware import MockHardware


class _MainWindowStub(QObject):
    exit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.closed = False
        self.prepared = False

    def hide(self):
        pass

    def start_module_monitoring(self):
        pass

    def showFullScreen(self):
        pass

    def isVisible(self):
        return False

    def prepare_for_shutdown(self):
        self.prepared = True
        return []

    def allow_close(self):
        pass

    def close(self):
        self.closed = True


class _SettingsStub(QObject):
    language_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str)
    language = "es"
    theme = "dark"


class ApplicationLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def test_startup_screen_close_requests_shutdown_and_waits(self):
        screen = StartupScreen()
        close_requests = []
        screen.close_requested.connect(lambda: close_requests.append(True))
        screen.show()
        self.app.processEvents()

        screen.close()

        self.assertEqual(len(close_requests), 1)
        self.assertTrue(screen.isVisible())
        screen.allow_close()
        screen.close()
        self.assertFalse(screen.isVisible())
        screen.deleteLater()
        self.app.processEvents()

    def test_startup_close_stops_startup_and_runs_safe_shutdown(self):
        hardware = MockHardware()
        power_controller = PowerController(hardware)
        startup_sequence = StartupSequence(hardware, initialize_analog=False)
        startup_controller = StartupController(startup_sequence)
        door_sequence = DoorSequence(hardware)
        soft_vacuum_sequence = SoftVacuumSequence(hardware)
        main_vacuum_sequence = MainVacuumSequence(hardware)
        vent_sequence = VentSequence(hardware)
        shutdown_sequence = ShutdownSequence(
            hardware,
            soft_vacuum_sequence,
            main_vacuum_sequence,
            vent_sequence,
        )
        shutdown_controller = ShutdownController(shutdown_sequence)
        startup_screen = StartupScreen()
        main_window = _MainWindowStub()
        lifecycle = ApplicationController(
            startup_controller,
            power_controller,
            shutdown_controller,
            startup_screen,
            main_window,
        )

        lifecycle.start()
        startup_controller.start()
        self.assertTrue(startup_sequence.is_running)
        self.assertTrue(power_controller._timer.isActive())

        with patch.object(QApplication, "quit", lambda *_args: None):
            startup_screen.close()

        self.assertFalse(startup_sequence.is_running)
        self.assertFalse(startup_sequence._timer.isActive())
        self.assertFalse(power_controller._timer.isActive())
        self.assertTrue(main_window.prepared)
        self.assertTrue(main_window.closed)
        self.assertTrue(shutdown_controller.is_shutting_down)
        self.assertFalse(hardware.digital_read("POWER_ON"))

        startup_screen.deleteLater()
        main_window.deleteLater()
        self.app.processEvents()

    def test_main_window_shutdown_stops_all_monitor_and_pulse_timers(self):
        hardware = MockHardware()
        door_sequence = DoorSequence(hardware)
        soft_vacuum_sequence = SoftVacuumSequence(hardware)
        main_vacuum_sequence = MainVacuumSequence(hardware)
        vent_sequence = VentSequence(hardware)
        window = MainWindow(
            hardware,
            door_sequence,
            soft_vacuum_sequence,
            main_vacuum_sequence,
            vent_sequence,
        )
        window.signal_controller.start_monitoring()
        window.analog_controller.start_monitoring()
        window.module_monitor_timer.start()
        window.process_controller._pulse_timer.start(1000)
        window.throttle_controller._timer.start(1000)
        purge_before_shutdown = hardware.digital_read("PURGE_VALVE_CONTROL")
        window.signal_controller.request_toggle("PURGE_VALVE_CONTROL")
        self.assertTrue(window.signal_controller.is_processing("PURGE_VALVE_CONTROL"))

        self.assertTrue(window.top_bar._clock_timer.isActive())
        self.assertTrue(window.module_monitor_timer.isActive())

        errors = window.prepare_for_shutdown()

        self.assertEqual(errors, [])
        self.assertFalse(window.signal_controller.is_monitoring)
        self.assertFalse(window.analog_controller._timer.isActive())
        self.assertFalse(window.module_monitor_timer.isActive())
        self.assertFalse(window.process_controller._pulse_timer.isActive())
        self.assertFalse(window.throttle_controller._timer.isActive())
        self.assertFalse(window.top_bar._clock_timer.isActive())
        self.app.processEvents()
        self.assertFalse(window.signal_controller.is_processing("PURGE_VALVE_CONTROL"))
        self.assertEqual(
            hardware.digital_read("PURGE_VALVE_CONTROL"),
            purge_before_shutdown,
        )

        window.allow_close()
        window.close()
        window.deleteLater()
        self.app.processEvents()

    def test_transient_dialogs_are_deleted_after_each_open(self):
        hardware = MockHardware()
        door_sequence = DoorSequence(hardware)
        soft_vacuum_sequence = SoftVacuumSequence(hardware)
        main_vacuum_sequence = MainVacuumSequence(hardware)
        vent_sequence = VentSequence(hardware)
        window = MainWindow(
            hardware,
            door_sequence,
            soft_vacuum_sequence,
            main_vacuum_sequence,
            vent_sequence,
            settings_manager=_SettingsStub(),
        )

        def open_and_reject(dialog_type, opener, parent):
            for _ in range(3):
                QTimer.singleShot(
                    0,
                    lambda: parent.findChild(dialog_type).reject(),
                )
                opener()
                self.app.sendPostedEvents(None, QEvent.DeferredDelete)
                self.assertEqual(parent.findChildren(dialog_type), [])

        open_and_reject(
            RecipeEditorDialog,
            window.normal_operation_screen._new_recipe,
            window.normal_operation_screen,
        )
        window.normal_operation_screen._active_recipe = Recipe(
            name="prueba",
            description="prueba",
            o2_flow=1.0,
            n2_flow=0.1,
            base_pressure=1.0,
            process_pressure=0.5,
            process_temperature=150.0,
        )
        open_and_reject(
            RecipeViewerDialog,
            window.normal_operation_screen._view_recipe,
            window.normal_operation_screen,
        )

        from gui.login_dialog import LoginDialog
        from gui.settings_dialog import SettingsDialog

        open_and_reject(
            LoginDialog,
            window._request_maintainer_access,
            window,
        )
        open_and_reject(
            SettingsDialog,
            window._open_settings_dialog,
            window,
        )
        window.allow_close()
        window.close()
        window.deleteLater()
        self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
