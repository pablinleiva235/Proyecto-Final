"""Diálogo de preferencias y créditos académicos."""

from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

import config_gui.strings as strings


class SettingsDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self._settings_manager = settings_manager
        self.setObjectName("SettingsDialog")

        self.language_combo = QComboBox()
        self.language_combo.setObjectName("SettingsCombo")
        self.language_combo.addItem("Español", "es")
        self.language_combo.addItem("English", "en")
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("SettingsCombo")
        self.theme_combo.addItem("Oscuro", "dark")
        self.theme_combo.addItem("Claro", "light")

        self.language_label = QLabel()
        self.theme_label = QLabel()
        self.developers_group = QGroupBox()
        self.tutors_group = QGroupBox()
        self.developer_labels = [QLabel(name) for name in strings.DEVELOPER_NAMES]
        self.tutor_labels = [QLabel(name) for name in strings.TUTOR_NAMES]
        self.close_button = QPushButton()
        self.close_button.setObjectName("SettingsCloseButton")

        preferences_layout = QFormLayout()
        preferences_layout.addRow(self.language_label, self.language_combo)
        preferences_layout.addRow(self.theme_label, self.theme_combo)

        developers_layout = QVBoxLayout(self.developers_group)
        for label in self.developer_labels:
            developers_layout.addWidget(label)
        tutors_layout = QVBoxLayout(self.tutors_group)
        for label in self.tutor_labels:
            tutors_layout.addWidget(label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        layout.addLayout(preferences_layout)
        layout.addWidget(self.developers_group)
        layout.addWidget(self.tutors_group)
        layout.addWidget(self.close_button)

        self.language_combo.setCurrentIndex(
            self.language_combo.findData(settings_manager.language)
        )
        self.theme_combo.setCurrentIndex(
            self.theme_combo.findData(settings_manager.theme)
        )

        self.language_combo.currentIndexChanged.connect(self._change_language)
        self.theme_combo.currentIndexChanged.connect(self._change_theme)
        self.close_button.clicked.connect(self.accept)
        settings_manager.language_changed.connect(self.update_texts)
        self.update_texts()
        self.setMinimumWidth(440)
        self.setModal(True)

    def update_texts(self, *_):
        self.setWindowTitle(strings.tr(strings.SETTINGS_TITLE))
        self.language_label.setText(strings.tr(strings.SETTINGS_LANGUAGE_LABEL))
        self.theme_label.setText(strings.tr(strings.SETTINGS_THEME_LABEL))
        self.developers_group.setTitle(
            strings.tr(strings.SETTINGS_DEVELOPERS_TITLE)
        )
        self.tutors_group.setTitle(strings.tr(strings.SETTINGS_TUTORS_TITLE))
        self.close_button.setText(strings.tr(strings.SETTINGS_CLOSE_BUTTON))

        language = self.language_combo.currentData()
        theme = self.theme_combo.currentData()
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        self.language_combo.addItem(
            strings.tr(strings.SETTINGS_LANGUAGE_SPANISH), "es"
        )
        self.language_combo.addItem(
            strings.tr(strings.SETTINGS_LANGUAGE_ENGLISH), "en"
        )
        self.language_combo.setCurrentIndex(self.language_combo.findData(language))
        self.language_combo.blockSignals(False)

        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        self.theme_combo.addItem(strings.tr(strings.SETTINGS_THEME_DARK), "dark")
        self.theme_combo.addItem(strings.tr(strings.SETTINGS_THEME_LIGHT), "light")
        self.theme_combo.setCurrentIndex(self.theme_combo.findData(theme))
        self.theme_combo.blockSignals(False)

    def _change_language(self, index):
        language = self.language_combo.itemData(index)
        if language:
            self._settings_manager.set_language(language)

    def _change_theme(self, index):
        theme = self.theme_combo.itemData(index)
        if theme:
            self._settings_manager.set_theme(theme)
