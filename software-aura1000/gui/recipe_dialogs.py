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
from services.recipe_service import Recipe


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
        pressure_min=None,
        save_callback=None,
    ):
        super().__init__(parent)
        self._recipe = recipe
        self._pressure_min = pressure_min
        self._save_callback = save_callback
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

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(text.tr(text.RECIPE_SAVE_BUTTON))
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
            except ValueError:
                self._show_invalid(text.RECIPE_ERROR_INVALID_VALUES)
                return
            if not math.isfinite(value):
                self._show_invalid(text.RECIPE_ERROR_INVALID_VALUES)
                return
            values[key] = value

        if self._pressure_min is None or not math.isfinite(float(self._pressure_min)):
            self._show_invalid(text.RECIPE_ERROR_PRESSURE_UNAVAILABLE)
            return
        if self._pressure_min > 3:
            self._show_invalid(text.RECIPE_ERROR_BASE_PRESSURE_MINIMUM)
            return

        limits = {
            "o2_flow": (0.0, 10.0),
            "n2_flow": (0.0, 1.0),
            "base_pressure": (float(self._pressure_min), 3.0),
            "process_pressure": (0.0, 10.0),
            "process_temperature": (130.0, 190.0),
        }
        adjusted_values = []
        field_labels = {
            key: (label, unit)
            for key, label, unit in self.FIELDS
        }
        for key, (minimum, maximum) in limits.items():
            original_value = values[key]
            clamped_value = min(maximum, max(minimum, values[key]))
            if clamped_value != original_value:
                label, unit = field_labels[key]
                adjusted_values.append(
                    text.tr(text.RECIPE_VALUE_RANGE_DETAIL).format(
                        label=text.tr(label),
                        value=self._format_number(original_value),
                        unit=unit,
                        minimum=self._format_number(minimum),
                        maximum=self._format_number(maximum),
                    )
                )
            values[key] = clamped_value
            self.parameter_edits[key].setText(self._format_number(values[key]))

        if adjusted_values:
            message = text.tr(text.RECIPE_VALUES_CLAMPED_MESSAGE).format(
                details="\n".join(adjusted_values)
            )
            self._show_invalid(message)
            return

        recipe = Recipe(
            name=name,
            description=description,
            source_path=self._recipe.source_path,
            **values,
        )
        if self._save_callback is not None:
            try:
                recipe = self._save_callback(recipe)
            except (ValueError, OSError) as error:
                self._show_invalid(str(error))
                return
            if recipe is None:
                return
        self._recipe = recipe
        self.accept()

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
