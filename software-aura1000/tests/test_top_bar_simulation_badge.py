import unittest

from PyQt5.QtWidgets import QApplication

import config_gui.strings as strings
from config_gui.theme import build_app_style
from gui.widgets.top_bar_widget import TopBarWidget


class TopBarSimulationBadgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_badge_visibility_tracks_simulation_mode(self):
        real_top_bar = TopBarWidget(simulation_mode=False)
        simulated_top_bar = TopBarWidget(simulation_mode=True)
        try:
            self.assertTrue(real_top_bar.simulation_badge.isHidden())
            self.assertFalse(simulated_top_bar.simulation_badge.isHidden())
            self.assertEqual(simulated_top_bar.simulation_badge.text(), "MODO SIMULADO")
        finally:
            real_top_bar.close()
            simulated_top_bar.close()

    def test_badge_is_centered_in_the_top_bar(self):
        top_bar = TopBarWidget(simulation_mode=True)
        try:
            top_bar.resize(900, 60)
            top_bar.show()
            self.app.processEvents()

            badge_center = top_bar.simulation_badge.geometry().center().x()
            self.assertAlmostEqual(badge_center, top_bar.width() / 2, delta=1)
        finally:
            top_bar.close()

    def test_badge_text_follows_active_language(self):
        original_language = strings.get_language()
        top_bar = None
        try:
            strings.set_language("en")
            top_bar = TopBarWidget(simulation_mode=True)
            top_bar.update_texts()
            self.assertEqual(top_bar.simulation_badge.text(), "SIMULATION MODE")
        finally:
            if top_bar is not None:
                top_bar.close()
            strings.set_language(original_language)

    def test_badge_uses_warning_palette_for_both_themes(self):
        self.assertIn("color: #FACC15;", build_app_style("dark"))
        self.assertIn("color: #92400E;", build_app_style("light"))


if __name__ == "__main__":
    unittest.main()
