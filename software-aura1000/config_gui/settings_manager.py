"""Preferencias persistentes de idioma y tema de la interfaz."""

from PyQt5.QtCore import QObject, QSettings, pyqtSignal

import config_gui.strings as strings
from config_gui.theme import build_app_style


class SettingsManager(QObject):
    language_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str)

    def __init__(self, application, parent=None):
        super().__init__(parent)
        self._application = application
        self._settings = QSettings("UTN", "Plasma Asher AURA 1000")
        self._language = self._settings.value("language", "es", type=str)
        self._theme = self._settings.value("theme", "dark", type=str)

        if self._language not in ("es", "en"):
            self._language = "es"
        if self._theme not in ("light", "dark"):
            self._theme = "dark"

        strings.set_language(self._language)
        self._application.setStyleSheet(build_app_style(self._theme))

    @property
    def language(self):
        return self._language

    @property
    def theme(self):
        return self._theme

    def set_language(self, language):
        if language not in ("es", "en"):
            raise ValueError("El idioma debe ser 'es' o 'en'.")
        if language == self._language:
            return
        self._language = language
        strings.set_language(language)
        self._settings.setValue("language", language)
        self._settings.sync()
        self.language_changed.emit(language)

    def set_theme(self, theme):
        if theme not in ("light", "dark"):
            raise ValueError("El tema debe ser 'light' o 'dark'.")
        if theme == self._theme:
            return
        self._theme = theme
        self._settings.setValue("theme", theme)
        self._settings.sync()
        self._application.setStyleSheet(build_app_style(theme))
        self.theme_changed.emit(theme)
