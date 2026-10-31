import unittest
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow


class _Interlocks:
    def __init__(self, permissions):
        self.permissions = permissions

    def get_permissions(self):
        return self.permissions.copy()


class _MaintainerScreen:
    def __init__(self):
        self.sequence_permissions = {}
        self.signal_errors = {}

    def set_sequence_enabled(self, name, enabled):
        self.sequence_permissions[name] = enabled

    def set_signal_error(self, name, message):
        self.signal_errors[name] = message

    def clear_operation_message(self, name):
        pass


class _WindowHarness:
    def __init__(self):
        self.maintainer_screen = _MaintainerScreen()
        self.interlock_controller = _Interlocks({
            "door": False,
            "soft_vacuum": False,
            "main_vacuum": False,
            "vent": False,
        })
        self.sync_count = 0
        self._driver_read_error = False

    def _sync_module_permissions(self):
        self.sync_count += 1

    def _update_sequence_permissions(self):
        MainWindow._update_sequence_permissions(self)


class _PressureController:
    def __init__(self, active):
        self.is_active = active
        self.aborted_with = []

    def abort(self, message):
        self.aborted_with.append(message)
        self.is_active = False


class _ThrottleController:
    def __init__(self, reserved=False):
        self.is_reserved_for_pressure = reserved
        self.stop_count = 0
        self.return_count = 0

    def stop(self):
        self.stop_count += 1

    def return_to_rest_for_safety(self):
        self.return_count += 1
        self.stop_count += 1
        return True


class _SafetyWindowHarness:
    def __init__(self, recipe_active=False):
        self.pressure_controller = _PressureController(active=True)
        self.throttle_controller = _ThrottleController(reserved=True)
        self.temperature_controller = _PressureController(active=False)
        self.maintainer_screen = _MaintainerScreen()
        self.maintainer_screen.set_operation_message = lambda *args, **kwargs: None
        self.mfc_controller = type("MFC", (), {"shutdown": lambda self: None})()
        self.process_controller = type("Process", (), {"stop_all": lambda self: None})()

        class RecipeSequence:
            is_active = recipe_active

            def interlock_lost(self, message):
                if self.is_active:
                    self.failed_with = message

        self.recipe_sequence = RecipeSequence()

    def _stop_pressure_and_throttle(self, message, return_to_rest=False):
        MainWindow._stop_pressure_and_throttle(self, message, return_to_rest)

    def _handle_pressure_error(self, message):
        self.pressure_error = message

    def _handle_throttle_error(self, message):
        self.throttle_error = message


class _StopTimer:
    def __init__(self):
        self.stop_count = 0

    def stop(self):
        self.stop_count += 1


class _EmergencyWindowHarness:
    def __init__(self):
        self.emergency_shutdown_requested = type(
            "Signal", (), {"emit": lambda self: setattr(self, "emitted", True)}
        )()
        self.module_monitor_timer = _StopTimer()
        self.analog_controller = type(
            "Analog", (), {"stop_monitoring": lambda self: setattr(self, "stopped", True)}
        )()
        self.maintainer_screen = _MaintainerScreen()
        self.pressure_controller = _PressureController(active=True)
        self.throttle_controller = _ThrottleController(reserved=True)
        self.temperature_controller = _PressureController(active=True)
        self.mfc_controller = type("MFC", (), {"shutdown": lambda self: None})()
        self.process_controller = type("Process", (), {"stop_all": lambda self: None})()
        self.recipe_sequence = type(
            "Recipe", (), {"abort_for_hardware_failure": lambda self, message: setattr(self, "aborted", message)}
        )()
        self.hardware = type(
            "Hardware", (), {"shutdown_state": lambda self: ["salida sin verificar"]}
        )()

    def _stop_pressure_and_throttle(self, message, return_to_rest=False):
        MainWindow._stop_pressure_and_throttle(self, message, return_to_rest)

    def _handle_pressure_error(self, message):
        self.pressure_error = message

    def _handle_throttle_error(self, message):
        self.throttle_error = message


def _make_active_pressure_safety_window(recipe_active=False):
    from controllers.pressure_controller import PressureController
    from controllers.throttle_controller import ThrottleController
    from tests.mockScripts.mock_hardware import MockHardware

    hardware = MockHardware()
    hardware.digital_set("DRIVER_ENABLE", True)
    hardware.set_input_state("THROTTLE_OPEN", False)
    hardware.set_input_state("THROTTLE_CLOSED", False)
    throttle = ThrottleController(hardware, can_operate=lambda: True)
    throttle._position_steps = 398.0
    pressure = PressureController(throttle, can_operate=lambda: True)
    pressure.set_pressure_reading(0.5)
    pressure.start(1.0)
    return hardware, throttle, pressure, _SafetyWindowHarness(recipe_active)


class MainWindowPermissionRefreshTests(unittest.TestCase):
    def setUp(self):
        self.window = _WindowHarness()

    def test_driver_change_refreshes_process_and_sequence_permissions(self):
        self.window.interlock_controller.permissions = {
            "door": True,
            "soft_vacuum": True,
            "main_vacuum": False,
            "vent": False,
        }

        MainWindow._handle_digital_signal_changed(
            self.window, "DRIVER_ENABLE", True
        )

        self.assertEqual(self.window.sync_count, 1)
        self.assertEqual(
            self.window.maintainer_screen.sequence_permissions,
            self.window.interlock_controller.permissions,
        )

    def test_driver_read_error_refreshes_sequence_permissions(self):
        MainWindow._handle_signal_error(
            self.window, "DRIVER_ENABLE", "lectura fallida"
        )

        self.assertTrue(self.window._driver_read_error)
        self.assertEqual(
            self.window.maintainer_screen.sequence_permissions,
            self.window.interlock_controller.permissions,
        )

    def test_successful_driver_sample_clears_read_error_and_refreshes(self):
        self.window._driver_read_error = True

        MainWindow._handle_digital_signal_sampled(
            self.window, "DRIVER_ENABLE", True
        )

        self.assertFalse(self.window._driver_read_error)
        self.assertEqual(self.window.sync_count, 1)
        self.assertEqual(
            self.window.maintainer_screen.sequence_permissions,
            self.window.interlock_controller.permissions,
        )

    def test_door_input_change_keeps_existing_module_permission_refresh(self):
        MainWindow._handle_digital_signal_changed(
            self.window, "DOOR_CLOSE", True
        )

        self.assertEqual(self.window.sync_count, 1)
        self.assertEqual(self.window.maintainer_screen.sequence_permissions, {})

    def test_process_alarm_stops_pressure_and_returns_throttle_without_recipe(self):
        window = _SafetyWindowHarness(recipe_active=False)
        with patch("gui.main_window.QMessageBox.warning"):
            MainWindow._handle_process_alarm(window, "falla simulada")

        self.assertEqual(len(window.pressure_controller.aborted_with), 1)
        self.assertEqual(window.throttle_controller.return_count, 1)

    def test_mfc_flow_fault_stops_pressure_and_throttle_with_or_without_recipe(self):
        for recipe_active in (False, True):
            with self.subTest(recipe_active=recipe_active):
                window = _SafetyWindowHarness(recipe_active=recipe_active)
                with patch("gui.main_window.QMessageBox.warning"):
                    MainWindow._handle_mfc_flow_fault(window, "desvío simulado")

                self.assertEqual(len(window.pressure_controller.aborted_with), 1)
                self.assertEqual(window.throttle_controller.stop_count, 1)
                self.assertEqual(
                    hasattr(window.recipe_sequence, "failed_with"),
                    recipe_active,
                )

    def test_process_alarm_aborts_active_pressure_motion_without_recipe(self):
        hardware, throttle, pressure, window = _make_active_pressure_safety_window()
        self.assertTrue(pressure.is_active)
        self.assertTrue(throttle._timer.isActive())

        with patch("gui.main_window.QMessageBox.warning"):
            window.pressure_controller = pressure
            window.throttle_controller = throttle
            MainWindow._handle_process_alarm(window, "falla simulada")

        self.assertFalse(pressure.is_active)
        self.assertTrue(throttle._timer.isActive())
        for _ in range(8):
            if not throttle._timer.isActive():
                break
            throttle._pulse()
        self.assertEqual(throttle.position_steps, 400.0)
        self.assertFalse(throttle._timer.isActive())
        self.assertFalse(throttle.is_reserved_for_pressure)
        self.assertFalse(hardware.digital_read("STEPPER_OUTPUT_ENABLE"))

    def test_mfc_flow_fault_aborts_active_pressure_motion_without_recipe(self):
        hardware, throttle, pressure, window = _make_active_pressure_safety_window()
        self.assertTrue(pressure.is_active)
        self.assertTrue(throttle._timer.isActive())
        window.pressure_controller = pressure
        window.throttle_controller = throttle

        with patch("gui.main_window.QMessageBox.warning"):
            MainWindow._handle_mfc_flow_fault(window, "desvío simulado")

        self.assertFalse(pressure.is_active)
        self.assertFalse(throttle._timer.isActive())
        self.assertFalse(throttle.is_reserved_for_pressure)
        self.assertFalse(hardware.digital_read("STEPPER_OUTPUT_ENABLE"))

    def test_fault_monitor_read_error_runs_global_shutdown_and_exits(self):
        window = _EmergencyWindowHarness()
        with (
            patch("gui.main_window.QMessageBox.critical") as critical,
            patch("gui.main_window.QApplication.exit") as app_exit,
        ):
            MainWindow._handle_fault_monitoring_failure(
                window, "Entradas de falla", "LAMP1_FAIL: entrada desconectada"
            )

        self.assertEqual(window.module_monitor_timer.stop_count, 1)
        self.assertTrue(window.emergency_shutdown_requested.emitted)
        self.assertTrue(window.analog_controller.stopped)
        self.assertIn("entrada desconectada", window.recipe_sequence.aborted)
        self.assertEqual(window.pressure_controller.aborted_with.__len__(), 1)
        self.assertEqual(window.throttle_controller.stop_count, 1)
        self.assertEqual(window.throttle_controller.return_count, 0)
        critical.assert_called_once()
        self.assertIn("salida sin verificar", critical.call_args.args[2])
        app_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
