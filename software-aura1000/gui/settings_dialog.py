"""Diálogo de preferencias y créditos académicos."""

from math import cos, radians, sin

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QPalette
from PyQt5.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

import config_gui.strings as strings


class ThemeSymbol(QWidget):
    """Icono vectorial sencillo de sol o luna para el selector de tema."""

    def __init__(self, kind, accessible_name, parent=None):
        super().__init__(parent)
        self._kind = kind
        self.setObjectName(
            "SettingsSunIcon" if kind == "sun" else "SettingsMoonIcon"
        )
        self.setFixedSize(24, 24)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAccessibleName(accessible_name)
        self.setToolTip(accessible_name)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = self.palette().color(QPalette.WindowText)
        painter.setPen(QPen(color, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        if self._kind == "sun":
            center = QPointF(12, 12)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, 4, 4)
            for angle in range(0, 360, 45):
                direction = radians(angle)
                inner = QPointF(
                    center.x() + cos(direction) * 7,
                    center.y() + sin(direction) * 7,
                )
                outer = QPointF(
                    center.x() + cos(direction) * 10,
                    center.y() + sin(direction) * 10,
                )
                painter.drawLine(inner, outer)
        else:
            crescent = QPainterPath()
            crescent.addEllipse(QRectF(4, 3, 16, 18))
            cutout = QPainterPath()
            cutout.addEllipse(QRectF(11, 1, 15, 18))
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawPath(crescent.subtracted(cutout))

        painter.end()


class SettingsDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self._settings_manager = settings_manager
        self.setObjectName("SettingsDialog")

        self.language_label = QLabel()
        self.theme_label = QLabel()
        self.language_es_radio = QRadioButton("ES")
        self.language_en_radio = QRadioButton("EN")
        self.theme_light_radio = QRadioButton()
        self.theme_dark_radio = QRadioButton()
        for radio in (
            self.language_es_radio,
            self.language_en_radio,
            self.theme_light_radio,
            self.theme_dark_radio,
        ):
            radio.setObjectName("SettingsRadio")
            radio.setCursor(Qt.PointingHandCursor)

        self.language_group = QButtonGroup(self)
        self.language_group.setExclusive(True)
        self.language_group.addButton(self.language_es_radio)
        self.language_group.addButton(self.language_en_radio)
        self.theme_group = QButtonGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_group.addButton(self.theme_light_radio)
        self.theme_group.addButton(self.theme_dark_radio)

        self.sun_icon = ThemeSymbol("sun", "Sol")
        self.moon_icon = ThemeSymbol("moon", "Luna")

        self.developers_group = QGroupBox()
        self.tutors_group = QGroupBox()
        self.developer_labels = [QLabel(name) for name in strings.DEVELOPER_NAMES]
        self.tutor_labels = [QLabel(name) for name in strings.TUTOR_NAMES]
        self.close_button = QPushButton()
        self.close_button.setObjectName("SettingsCloseButton")

        language_control = QWidget()
        language_layout = QHBoxLayout(language_control)
        language_layout.setContentsMargins(0, 0, 0, 0)
        language_layout.setSpacing(16)
        language_layout.addWidget(self.language_es_radio)
        language_layout.addWidget(self.language_en_radio)

        theme_control = QWidget()
        theme_layout = QHBoxLayout(theme_control)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(6)
        theme_layout.addWidget(self.sun_icon)
        theme_layout.addWidget(self.theme_light_radio)
        theme_layout.addSpacing(10)
        theme_layout.addWidget(self.moon_icon)
        theme_layout.addWidget(self.theme_dark_radio)

        preferences_layout = QFormLayout()
        preferences_layout.setHorizontalSpacing(18)
        preferences_layout.setVerticalSpacing(14)
        preferences_layout.addRow(self.language_label, language_control)
        preferences_layout.addRow(self.theme_label, theme_control)

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

        self.language_es_radio.setChecked(settings_manager.language == "es")
        self.language_en_radio.setChecked(settings_manager.language == "en")
        self.theme_light_radio.setChecked(settings_manager.theme == "light")
        self.theme_dark_radio.setChecked(settings_manager.theme == "dark")
        self.language_es_radio.toggled.connect(
            lambda selected: self._change_language("es", selected)
        )
        self.language_en_radio.toggled.connect(
            lambda selected: self._change_language("en", selected)
        )
        self.theme_light_radio.toggled.connect(
            lambda selected: self._change_theme("light", selected)
        )
        self.theme_dark_radio.toggled.connect(
            lambda selected: self._change_theme("dark", selected)
        )
        self.close_button.clicked.connect(self.accept)
        settings_manager.language_changed.connect(self.update_texts)
        settings_manager.theme_changed.connect(self.update_texts)
        self.update_texts()
        self.setMinimumWidth(440)
        self.setModal(True)

    def update_texts(self, *_):
        self.setWindowTitle(strings.tr(strings.SETTINGS_TITLE))
        self.language_label.setText(strings.tr(strings.SETTINGS_LANGUAGE_LABEL))
        self.theme_label.setText(strings.tr(strings.SETTINGS_THEME_LABEL))
        self.theme_light_radio.setText(strings.tr(strings.SETTINGS_THEME_LIGHT))
        self.theme_dark_radio.setText(strings.tr(strings.SETTINGS_THEME_DARK))
        self.language_es_radio.setAccessibleName(
            f"{strings.tr(strings.SETTINGS_LANGUAGE_LABEL)}: ES"
        )
        self.language_en_radio.setAccessibleName(
            f"{strings.tr(strings.SETTINGS_LANGUAGE_LABEL)}: EN"
        )
        self.theme_light_radio.setAccessibleName(
            f"{strings.tr(strings.SETTINGS_THEME_LABEL)}: "
            f"{strings.tr(strings.SETTINGS_THEME_LIGHT)}"
        )
        self.theme_dark_radio.setAccessibleName(
            f"{strings.tr(strings.SETTINGS_THEME_LABEL)}: "
            f"{strings.tr(strings.SETTINGS_THEME_DARK)}"
        )
        self.sun_icon.setAccessibleName(strings.tr(strings.SETTINGS_THEME_LIGHT))
        self.sun_icon.setToolTip(strings.tr(strings.SETTINGS_THEME_LIGHT))
        self.moon_icon.setAccessibleName(strings.tr(strings.SETTINGS_THEME_DARK))
        self.moon_icon.setToolTip(strings.tr(strings.SETTINGS_THEME_DARK))
        self.developers_group.setTitle(
            strings.tr(strings.SETTINGS_DEVELOPERS_TITLE)
        )
        self.tutors_group.setTitle(strings.tr(strings.SETTINGS_TUTORS_TITLE))
        self.close_button.setText(strings.tr(strings.SETTINGS_CLOSE_BUTTON))

        for radio in (self.language_es_radio, self.language_en_radio):
            radio.blockSignals(True)
        self.language_es_radio.setChecked(self._settings_manager.language == "es")
        self.language_en_radio.setChecked(self._settings_manager.language == "en")
        for radio in (self.language_es_radio, self.language_en_radio):
            radio.blockSignals(False)

        for radio in (self.theme_light_radio, self.theme_dark_radio):
            radio.blockSignals(True)
        self.theme_light_radio.setChecked(self._settings_manager.theme == "light")
        self.theme_dark_radio.setChecked(self._settings_manager.theme == "dark")
        for radio in (self.theme_light_radio, self.theme_dark_radio):
            radio.blockSignals(False)

    def _change_language(self, language, selected):
        if selected:
            self._settings_manager.set_language(language)

    def _change_theme(self, theme, selected):
        if selected:
            self._settings_manager.set_theme(theme)
