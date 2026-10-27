"""Pantalla de operación normal con lecturas y espacio para el esquema."""

from dataclasses import replace
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import config_gui.strings as text
from gui.widgets.localization import set_localized_text, translate_widget_tree
from gui.widgets.status_indicator import StatusIndicatorWidget
from gui.recipe_dialogs import RecipeEditorDialog, RecipeViewerDialog
from services.recipe_service import RecipeError, RecipeService


class _DiagramImageLabel(QLabel):
    """Display a diagram scaled to fit while preserving its aspect ratio."""

    def __init__(self, pixmap=None, fallback_text="", parent=None):
        super().__init__(parent)
        self._source_pixmap = (
            pixmap if pixmap is not None and not pixmap.isNull() else None
        )
        self.setAlignment(Qt.AlignCenter)
        if self._source_pixmap is None:
            self.setText(fallback_text)
            self.setWordWrap(True)
            self.setObjectName("OperationDiagramFallback")
        else:
            self.setObjectName("OperationDiagramImage")
            self._update_scaled_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self):
        if self._source_pixmap is None:
            return
        available_size = self.contentsRect().size()
        if available_size.width() <= 0 or available_size.height() <= 0:
            return
        self.setPixmap(
            self._source_pixmap.scaled(
                available_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )


class NormalOperationScreen(QWidget):
    """Lecturas analógicas activas, esquema reservado y acciones de receta."""

    back_requested = pyqtSignal()
    start_recipe_requested = pyqtSignal(object)
    stop_recipe_requested = pyqtSignal()

    ANALOG_READOUTS = {
        "CHAMBER_TEMP": (text.OPERATION_TEMPERATURE_LABEL, "°C", 1),
        "BARATRON": (text.OPERATION_PRESSURE_LABEL, "Torr", 3),
        "MFC1_FLOW": (text.OPERATION_MFC1_LABEL, "SLPM", 3),
        "MFC2_FLOW": (text.OPERATION_MFC2_LABEL, "SLPM", 3),
        "EOP": (text.OPERATION_EOP_LABEL, "V", 3),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._readouts = {}
        self._recipe_service = RecipeService()
        self._active_recipe = None
        self._chamber_pressure = None
        self._recipe_running = False
        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

    def create_widgets(self):
        self.title_label = QLabel(text.NORMAL_OPERATION_TITLE)
        self.title_label.setObjectName("NormalOperationTitle")

        self.simulation_badge = QLabel(text.SIMULATION_MODE_LABEL)
        self.simulation_badge.setObjectName("SimulationBadge")
        self.simulation_badge.setAlignment(Qt.AlignCenter)

        self.simulation_description = QLabel(text.SIMULATION_MODE_DESCRIPTION)
        self.simulation_description.setObjectName("SimulationDescription")
        self.simulation_description.setWordWrap(True)

        self.readings_panel = self._make_panel(text.OPERATION_READINGS_TITLE)
        readings_layout = self.readings_panel.layout()
        for signal_name, (label, unit, decimals) in self.ANALOG_READOUTS.items():
            readings_layout.addWidget(
                self._create_readout(signal_name, label, unit, decimals)
            )

        self.rf_readout = self._create_readout(
            "RF_LEVEL", text.OPERATION_RF_LABEL, "", 0, unavailable=True
        )
        readings_layout.addWidget(self.rf_readout["card"])
        readings_layout.addStretch(1)

        self.diagram_panel = self._make_panel(text.OPERATION_DIAGRAM_TITLE)
        diagram_path = Path(__file__).resolve().parents[1] / "assets" / "Frame 28.png"
        diagram_pixmap = QPixmap(str(diagram_path))
        fallback_text = text.OPERATION_DIAGRAM_LOAD_ERROR
        if diagram_pixmap.isNull():
            fallback_text = f"{fallback_text}\n{diagram_path.name}"
        self.diagram_image = _DiagramImageLabel(diagram_pixmap, fallback_text)
        if diagram_pixmap.isNull():
            set_localized_text(
                self.diagram_image,
                f"{text.OPERATION_DIAGRAM_LOAD_ERROR}\n{diagram_path.name}",
            )
        self.diagram_panel.layout().addWidget(self.diagram_image, 1)

        self.actions_panel = self._make_panel(text.OPERATION_RECIPE_ACTIONS_TITLE)
        self.active_recipe_label = QLabel(text.ACTIVE_RECIPE_LABEL)
        self.active_recipe_label.setObjectName("OperationReadoutLabel")
        self.active_recipe_name = QLabel(text.NO_ACTIVE_RECIPE)
        self.active_recipe_name.setObjectName("ActiveRecipeName")
        actions_layout = self.actions_panel.layout()
        actions_layout.addWidget(self.active_recipe_label)
        actions_layout.addWidget(self.active_recipe_name)
        self.new_recipe_button = self._recipe_button(text.NEW_RECIPE_BUTTON)
        self.load_recipe_button = self._recipe_button(text.LOAD_RECIPE_BUTTON)
        self.start_recipe_button = self._recipe_button(text.START_RECIPE_BUTTON)
        self.start_recipe_button.setEnabled(False)
        self.start_recipe_button.setToolTip(text.START_RECIPE_PENDING_TOOLTIP)
        self.start_recipe_button.setAccessibleDescription(
            text.tr(text.START_RECIPE_PENDING_TOOLTIP)
        )
        self.view_recipe_button = self._recipe_button(text.VIEW_RECIPE_BUTTON)
        self.view_recipe_button.setEnabled(False)
        self.recipe_status_label = QLabel(text.RECIPE_IDLE_STATUS)
        self.recipe_status_label.setObjectName("OperationReadoutLabel")
        self.recipe_status_label.setWordWrap(True)
        for button in (
            self.new_recipe_button,
            self.load_recipe_button,
            self.start_recipe_button,
            self.view_recipe_button,
        ):
            actions_layout.addWidget(button)
        actions_layout.addWidget(self.recipe_status_label)
        actions_layout.addStretch(1)

        self.back_button = QPushButton(text.BACK_BUTTON_TEXT)
        self.back_button.setObjectName("BackButton")

    def setup_layout(self):
        header = QHBoxLayout()
        header.addWidget(self.title_label)
        header.addStretch(1)
        header.addWidget(self.simulation_badge)

        columns = QHBoxLayout()
        columns.setSpacing(14)
        columns.addWidget(self.readings_panel, 1)
        columns.addWidget(self.diagram_panel, 3)
        columns.addWidget(self.actions_panel, 1)

        footer = QHBoxLayout()
        footer.addWidget(self.simulation_description, 1)
        footer.addWidget(self.back_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        layout.addLayout(header)
        layout.addLayout(columns, 1)
        layout.addLayout(footer)

    def connect_signals(self):
        self.back_button.clicked.connect(self.back_requested.emit)
        self.new_recipe_button.clicked.connect(self._new_recipe)
        self.load_recipe_button.clicked.connect(self._load_recipe)
        self.view_recipe_button.clicked.connect(self._view_recipe)
        self.start_recipe_button.clicked.connect(self._start_recipe_requested)

    @staticmethod
    def _make_panel(title):
        panel = QFrame()
        panel.setObjectName("OperationCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        heading = QLabel(title)
        heading.setObjectName("OperationCardTitle")
        layout.addWidget(heading)
        return panel

    def _create_readout(self, signal_name, label, unit, decimals, unavailable=False):
        card = QFrame()
        card.setObjectName("OperationReadoutCard")
        row = QHBoxLayout(card)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(8)
        indicator = StatusIndicatorWidget(
            "off" if unavailable else "running",
            text.tr(text.OPERATION_READING_UNAVAILABLE if unavailable else text.OPERATION_READING_WAITING),
            size=30,
        )
        details = QVBoxLayout()
        details.setSpacing(2)
        name_label = QLabel(label)
        name_label.setObjectName("OperationReadoutLabel")
        value_label = QLabel(text.OPERATION_READING_UNAVAILABLE if unavailable else text.OPERATION_READING_WAITING)
        value_label.setObjectName("OperationReadoutValue")
        unit_label = QLabel(unit)
        unit_label.setObjectName("OperationReadoutUnit")
        details.addWidget(name_label)
        value_row = QHBoxLayout()
        value_row.setSpacing(4)
        value_row.addWidget(value_label)
        value_row.addWidget(unit_label)
        value_row.addStretch(1)
        details.addLayout(value_row)
        row.addWidget(indicator)
        row.addLayout(details, 1)
        if not unavailable:
            self._readouts[signal_name] = {
                "card": card,
                "indicator": indicator,
                "value": value_label,
                "unit": unit_label,
                "decimals": decimals,
            }
        return {"card": card} if unavailable else card

    @staticmethod
    def _recipe_button(label):
        button = QPushButton(label)
        button.setObjectName("RecipeActionButton")
        button.setMinimumHeight(44)
        return button

    def set_analog_value(self, signal_name, value):
        readout = self._readouts.get(signal_name)
        if readout is None:
            return
        value = float(value)
        if signal_name == "BARATRON":
            self._chamber_pressure = value
        readout["value"].setProperty("i18nSourceText_text", None)
        readout["value"].setText(f"{value:.{readout['decimals']}f}")
        readout["value"].setToolTip("")
        readout["indicator"].set_state("on", text.tr(text.OPERATION_READING_OK))

    def set_analog_error(self, signal_name, message):
        readout = self._readouts.get(signal_name)
        if readout is None:
            return
        if signal_name == "BARATRON":
            self._chamber_pressure = None
        set_localized_text(readout["value"], text.OPERATION_READING_ERROR)
        readout["value"].setToolTip(str(message))
        readout["indicator"].set_state(
            "fault", f"{text.tr(text.OPERATION_READING_ERROR)}: {message}"
        )

    def _new_recipe(self):
        try:
            recipe = replace(
                self._recipe_service.load_template(),
                name="",
                source_path=None,
            )
        except RecipeError as error:
            self._show_recipe_error(error)
            return

        dialog = RecipeEditorDialog(
            recipe, self, pressure_min=self._chamber_pressure,
            save_callback=self._save_recipe_to_disk,
        )
        if dialog.exec_() == dialog.Accepted:
            self._set_active_recipe(dialog.recipe)

    def _load_recipe(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            text.tr(text.RECIPE_LOAD_DIALOG_TITLE),
            str(self._recipe_service.directory),
            text.tr(text.RECIPE_FILE_FILTER),
        )
        if not path:
            return
        try:
            recipe = self._recipe_service.load_file(path)
        except RecipeError as error:
            self._show_recipe_error(error)
            return
        self._set_active_recipe(recipe)

    def _save_recipe_to_disk(self, recipe):
        try:
            path = self._recipe_service.path_for_name(recipe.name)
            overwrite = path.exists()
            if overwrite:
                answer = QMessageBox.question(
                    self,
                    text.tr(text.RECIPE_OVERWRITE_TITLE),
                    text.tr(text.RECIPE_OVERWRITE_MESSAGE),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if answer != QMessageBox.Yes:
                    return None
            return self._recipe_service.save(recipe, overwrite=overwrite)
        except (RecipeError, OSError) as error:
            raise RecipeError(str(error)) from error

    def _view_recipe(self):
        if self._active_recipe is None:
            self._show_no_active_recipe()
            return
        viewer = RecipeViewerDialog(self._active_recipe, self)
        if viewer.exec_() == viewer.Accepted and viewer.edit_requested:
            recipe_to_edit = self._active_recipe
            is_template = (
                recipe_to_edit.source_path == self._recipe_service.template_path
            )
            if is_template:
                recipe_to_edit = replace(recipe_to_edit, name="", source_path=None)
            editor = RecipeEditorDialog(
                recipe_to_edit,
                self,
                allow_name_edit=is_template,
                pressure_min=self._chamber_pressure,
                save_callback=self._save_recipe_to_disk,
            )
            if editor.exec_() == editor.Accepted:
                self._set_active_recipe(editor.recipe)

    def _set_active_recipe(self, recipe):
        self._active_recipe = recipe
        self.active_recipe_name.setProperty("i18nSourceText_text", None)
        self.active_recipe_name.setText(recipe.name or text.tr(text.NO_ACTIVE_RECIPE))
        self.view_recipe_button.setEnabled(True)
        self.start_recipe_button.setEnabled(not self._recipe_running)
        self.start_recipe_button.setToolTip("")
        self.start_recipe_button.setAccessibleDescription("")

    def _start_recipe_requested(self):
        if self._recipe_running:
            self.stop_recipe_requested.emit()
            return
        if self._active_recipe is None:
            self._show_no_active_recipe()
            return
        try:
            self._recipe_service.validate(self._active_recipe, require_name=True)
        except RecipeError as error:
            self._show_recipe_error(error)
            return
        recipe = self._active_recipe
        details = (
            f"{text.tr(text.RECIPE_NAME_LABEL)}: {recipe.name}\n"
            f"{text.tr(text.RECIPE_DESCRIPTION_LABEL)}: {recipe.description}\n"
            f"{text.tr(text.RECIPE_O2_FLOW_LABEL)}: {recipe.o2_flow:g} SLPM\n"
            f"{text.tr(text.RECIPE_N2_FLOW_LABEL)}: {recipe.n2_flow:g} SLPM\n"
            f"{text.tr(text.RECIPE_BASE_PRESSURE_LABEL)}: {recipe.base_pressure:g} Torr\n"
            f"{text.tr(text.RECIPE_PROCESS_PRESSURE_LABEL)}: {recipe.process_pressure:g} Torr\n"
            f"{text.tr(text.RECIPE_PROCESS_TEMPERATURE_LABEL)}: {recipe.process_temperature:g} °C"
        )
        answer = QMessageBox.question(
            self, text.tr(text.START_RECIPE_CONFIRM_TITLE), details,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.start_recipe_requested.emit(recipe)

    def set_recipe_running(self, running, can_stop=True):
        self._recipe_running = bool(running)
        self.back_button.setEnabled(not self._recipe_running)
        self.new_recipe_button.setEnabled(not self._recipe_running)
        self.load_recipe_button.setEnabled(not self._recipe_running)
        self.view_recipe_button.setEnabled(
            not self._recipe_running and self._active_recipe is not None
        )
        set_localized_text(
            self.start_recipe_button,
            text.STOP_RECIPE_BUTTON if self._recipe_running else text.START_RECIPE_BUTTON,
        )
        self.start_recipe_button.setEnabled(
            (self._recipe_running and can_stop)
            or (not self._recipe_running and self._active_recipe is not None)
        )

    def set_recipe_status(self, status):
        set_localized_text(self.recipe_status_label, status)

    def confirm_wafer_loaded(self):
        answer = QMessageBox.question(
            self, text.tr(text.WAFER_CONFIRM_TITLE),
            text.tr(text.WAFER_CONFIRM_MESSAGE),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        return answer == QMessageBox.Yes

    def _show_no_active_recipe(self):
        QMessageBox.information(
            self,
            text.tr(text.RECIPE_NO_ACTIVE_TITLE),
            text.tr(text.RECIPE_NO_ACTIVE_MESSAGE),
        )

    def _show_recipe_error(self, error):
        message = str(error)
        QMessageBox.warning(
            self,
            text.tr(text.RECIPE_INVALID_TITLE),
            text.tr(message),
        )

    def update_texts(self, *_):
        translate_widget_tree(self)
