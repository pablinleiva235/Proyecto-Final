import unittest

from PyQt5.QtWidgets import QApplication

import config_gui.strings as strings
from gui.startup_mode_dialog import StartupModeDialog


class StartupModeDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_default_mode_is_real_and_popup_uses_active_language(self):
        original_language = strings.get_language()
        dialog = None
        try:
            strings.set_language("en")
            dialog = StartupModeDialog()

            self.assertTrue(dialog.real_mode_radio.isChecked())
            self.assertFalse(dialog.simulation_selected)
            self.assertEqual(dialog.windowTitle(), "Plasma Asher AURA 1000")
            self.assertEqual(dialog.mode_title_label.text(), "Select startup mode")
            self.assertEqual(dialog.real_mode_radio.text(), "Real mode")
            self.assertEqual(dialog.simulation_mode_radio.text(), "Simulation mode")
            self.assertEqual(dialog.continue_button.text(), "Continue")
            self.assertEqual(dialog.cancel_button.text(), "Cancel")
        finally:
            if dialog is not None:
                dialog.close()
            strings.set_language(original_language)


if __name__ == "__main__":
    unittest.main()
