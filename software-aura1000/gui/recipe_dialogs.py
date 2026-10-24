"""Diálogos de edición y consulta de recetas."""

import math

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

import config_gui.strings as text
from services.recipe_service import Recipe, RecipeError, RecipeService


class RecipeEditorDialog(QDialog):
    """Edita un borrador de receta, sin interactuar con el hardware."""

    FIELDS = (
        ("o2_flow", text.RECIPE_O2_FLOW_LABEL, "SLPM"),
        ("n2_flow", text.RECIPE_N2_FLOW_LABEL, "SLPM"),
        ("base_pressure", text.RECIPE_BASE_PRESSURE_LABEL, "Torr"),
        ("process_pressure", text.RECIPE_PROCESS_PRESSURE_LABEL, "Torr"),
        ("process_temperature", text.RECIPE_PROCESS_TEMPERATURE_LABEL, "°C"),
    )

    def __init__(
        self,
        recipe,
        parent=None,
        allow_name_edit=True,
        recipe_service=None,
        on_commit=None,
        confirm_text=None,
    ):
        super().__init__(parent)
        self._recipe = recipe
        self._recipe_service = recipe_service or RecipeService()
        self._on_commit = on_commit
        self.setObjectName("RecipeEditorDialog")
        self.setWindowTitle(text.tr(text.RECIPE_EDITOR_TITLE))

        self.name_edit = QLineEdit(recipe.name)
        self.name_edit.setObjectName("RecipeInput")
        self.name_edit.setEnabled(allow_name_edit)
        self.description_edit = QLineEdit(recipe.description)
        self.description_edit.setObjectName("RecipeInput")

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        form.addRow(text.tr(text.RECIPE_NAME_LABEL), self.name_edit)
        form.addRow(text.tr(text.RECIPE_DESCRIPTION_LABEL), self.description_edit)
        self.parameter_edits = {}
        for key, label, unit in self.FIELDS:
            edit = QLineEdit(self._format_number(getattr(recipe, key)))
            edit.setObjectName("RecipeInput")
            edit.setAlignment(Qt.AlignRight)
            self.parameter_edits[key] = edit
            form.addRow(f"{text.tr(label)} ({unit})", edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(
            text.tr(confirm_text or text.RECIPE_CREATE_BUTTON)
        )
        buttons.button(QDialogButtonBox.Cancel).setText(text.tr(text.RECIPE_CANCEL_BUTTON))
        buttons.accepted.connect(self._accept_recipe)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(16)
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setMinimumWidth(480)

    def _accept_recipe(self):
        name = self.name_edit.text().strip()
        description = self.description_edit.text().strip()
        if not name:
            self._show_invalid(text.RECIPE_ERROR_NAME_REQUIRED)
            return
        if not description:
            self._show_invalid(text.RECIPE_ERROR_METADATA)
            return

        values = {}
        for key, _, _unit in self.FIELDS:
            raw = self.parameter_edits[key].text().strip().replace(",", ".")
            try:
                value = float(raw)
            except (ValueError, OverflowError):
                self._show_invalid(text.RECIPE_ERROR_INVALID_VALUES)
                return
            if not math.isfinite(value):
                self._show_invalid(text.RECIPE_ERROR_NONFINITE)
                return
            values[key] = value

        candidate = Recipe(
            name=name,
            description=description,
            source_path=self._recipe.source_path,
            **values,
        )
        try:
            candidate, changes = self._recipe_service.clamp_parameters(candidate)
        except RecipeError as error:
            self._show_invalid(str(error))
            return

        if changes:
            self._apply_parameter_values(candidate)
            details = "\n".join(
                self._format_clamp_change(change) for change in changes
            )
            QMessageBox.warning(
                self,
                text.tr(text.RECIPE_RANGE_WARNING_TITLE),
                text.tr(text.RECIPE_RANGE_WARNING_MESSAGE).format(details=details),
            )
            return

        if self._on_commit is not None:
            saved_recipe = self._on_commit(candidate)
            if saved_recipe is None:
                return
            candidate = saved_recipe
        self._recipe = candidate
        self.accept()

    def _apply_parameter_values(self, recipe):
        for key, edit in self.parameter_edits.items():
            edit.setText(self._format_number(getattr(recipe, key)))

    def _format_clamp_change(self, change):
        key, original, adjusted, minimum, maximum, unit = change
        label = next(label for field, label, _unit in self.FIELDS if field == key)
        return text.tr(text.RECIPE_RANGE_ADJUSTMENT).format(
            field=text.tr(label),
            original=self._format_number(original),
            adjusted=self._format_number(adjusted),
            minimum=self._format_number(minimum),
            maximum=self._format_number(maximum),
            unit=unit,
        )

    def _show_invalid(self, message):
        QMessageBox.warning(
            self,
            text.tr(text.RECIPE_INVALID_TITLE),
            text.tr(message),
        )

    @property
    def recipe(self):
        return self._recipe

    @staticmethod
    def _format_number(value):
        return format(float(value), ".15g")


class RecipeViewerDialog(QDialog):
    """Muestra los datos de una receta en modo de solo lectura."""

    def __init__(self, recipe, parent=None):
        super().__init__(parent)
        self.edit_requested = False
        self.setObjectName("RecipeViewerDialog")
        self.setWindowTitle(text.tr(text.RECIPE_VIEW_TITLE))

        details = QFormLayout()
        details.setHorizontalSpacing(18)
        details.setVerticalSpacing(12)
        details.addRow(text.tr(text.RECIPE_NAME_LABEL), QLabel(recipe.name))
        details.addRow(text.tr(text.RECIPE_DESCRIPTION_LABEL), QLabel(recipe.description))
        for key, label, unit in RecipeEditorDialog.FIELDS:
            value = format(float(getattr(recipe, key)), ".15g")
            details.addRow(f"{text.tr(label)} ({unit})", QLabel(value))

        close_button = QPushButton(text.tr(text.RECIPE_CLOSE_BUTTON))
        edit_button = QPushButton(text.tr(text.RECIPE_EDIT_BUTTON))
        edit_button.setObjectName("RecipeActionButton")
        edit_button.clicked.connect(self._request_edit)
        close_button.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(16)
        layout.addLayout(details)
        buttons = QVBoxLayout()
        buttons.addWidget(edit_button)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        self.setMinimumWidth(440)

    def _request_edit(self):
        self.edit_requested = True
        self.accept()
