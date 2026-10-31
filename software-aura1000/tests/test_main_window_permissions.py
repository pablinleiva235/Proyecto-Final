import unittest

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


if __name__ == "__main__":
    unittest.main()
