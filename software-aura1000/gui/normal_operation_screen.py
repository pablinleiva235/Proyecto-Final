"""Pantalla de demostración para la operación normal del equipo.

Los valores y estados de esta pantalla son locales y simulados. No se conecta
con Hardware, controladores ni secuencias de proceso.
"""

import math
from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import config_gui.strings as text
from gui.widgets.localization import set_localized_text, translate_widget_tree


class NonNegativeNumberValidator(QValidator):
    """Acepta números decimales no negativos y coma o punto decimal."""

    def __init__(self, maximum=None, decimals=3, parent=None):
        super().__init__(parent)
        self._maximum = maximum
        self._decimals = decimals

    def validate(self, value, position):
        if value == "":
            return self.Intermediate, value, position

        normalized = value.replace(",", ".")
        if normalized.count(".") > 1:
            return self.Invalid, value, position

        whole, separator, fraction = normalized.partition(".")
        if not whole and not separator:
            return self.Invalid, value, position
        if (whole and not whole.isdigit()) or (fraction and not fraction.isdigit()):
            return self.Invalid, value, position
        if len(fraction) > self._decimals:
            return self.Invalid, value, position

        if separator and fraction == "":
            return self.Intermediate, value, position

        try:
            number = float(normalized)
        except ValueError:
            return self.Intermediate, value, position

        if not math.isfinite(number) or (self._maximum is not None and number > self._maximum):
            return self.Invalid, value, position

        return self.Acceptable, value, position


class NormalOperationScreen(QWidget):
    """Prototipo interactivo de operación normal, sin acceso al equipo."""

    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._states = {"vacuum": False, "plasma": False}
        self._accepted_setpoints = {
            "mfc1": 0.0,
            "mfc2": 0.0,
            "pressure": 0.5,
            "temperature": 100.0,
        }
        self._setpoint_controls = {}
        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

    def create_widgets(self):
        self.title_label = QLabel(text.NORMAL_OPERATION_TITLE)
        self.title_label.setObjectName("NormalOperationTitle")

        self.save_recipe_button = QPushButton(text.SAVE_RECIPE_BUTTON)
        self.save_recipe_button.setObjectName("RecipeActionButton")
        self.load_recipe_button = QPushButton(text.LOAD_RECIPE_BUTTON)
        self.load_recipe_button.setObjectName("RecipeActionButton")
        self.start_process_button = QPushButton(text.START_PROCESS_BUTTON)
        self.start_process_button.setObjectName("DemoActionButton")
        self.start_process_button.setEnabled(False)
        self.start_process_button.setToolTip(text.START_PROCESS_PENDING_TOOLTIP)
        self.start_process_button.setAccessibleDescription(
            text.tr(text.START_PROCESS_PENDING_TOOLTIP)
        )

        self.simulation_badge = QLabel(text.SIMULATION_MODE_LABEL)
        self.simulation_badge.setObjectName("SimulationBadge")
        self.simulation_badge.setAlignment(Qt.AlignCenter)

        self.simulation_description = QLabel(text.SIMULATION_MODE_DESCRIPTION)
        self.simulation_description.setObjectName("SimulationDescription")
        self.simulation_description.setWordWrap(True)

        self.equipment_card = QFrame()
        self.equipment_card.setObjectName("OperationStatusCard")
        equipment_layout = QHBoxLayout(self.equipment_card)
        equipment_layout.setContentsMargins(14, 6, 14, 6)
        equipment_layout.setSpacing(12)
        equipment_title = QLabel(text.EQUIPMENT_STATUS_TITLE)
        equipment_title.setObjectName("OperationStatusTitle")
        equipment_layout.addWidget(equipment_title)
        equipment_layout.addStretch()
        self.equipment_status = QLabel(text.EQUIPMENT_STATUS_READY)
        self.equipment_status.setObjectName("DemoStatusGood")
        equipment_layout.addWidget(self.equipment_status)

        self.gas_card, gas_layout = self._make_card(text.GAS_FLOWS_TITLE)
        self._add_setpoint_row(
            gas_layout,
            key="mfc1",
            label=f"{text.OXYGEN_FLOW_LABEL} · {text.FLOW_SETPOINT_LABEL}",
            initial="0.0",
            measured="0.00 SLPM",
            maximum=10.0,
            range_label=text.MFC1_RANGE_LABEL,
            step=0.05,
            display_decimals=2,
        )
        self._add_setpoint_row(
            gas_layout,
            key="mfc2",
            label=f"{text.NITROGEN_FLOW_LABEL} · {text.FLOW_SETPOINT_LABEL}",
            initial="0.0",
            measured="0.00 SLPM",
            maximum=1.0,
            range_label=text.MFC2_RANGE_LABEL,
            step=0.05,
            display_decimals=2,
        )

        self.chamber_card, chamber_layout = self._make_card(text.VACUUM_PRESSURE_TITLE)
        self._add_setpoint_row(
            chamber_layout,
            key="pressure",
            label=text.PRESSURE_SETPOINT_LABEL,
            initial="0.500",
            measured="0.760 Torr",
            unit="Torr · ±0,05",
            step=0.05,
            display_decimals=3,
        )
        self.pressure_reading = self._setpoint_controls["pressure"]["reading"]
        self._add_setpoint_row(
            chamber_layout,
            key="temperature",
            label=text.TEMPERATURE_SETPOINT_LABEL,
            initial="100.0",
            measured="24.0 °C",
            unit="°C · ±5",
            step=5.0,
            display_decimals=1,
        )
        self.temperature_reading = self._setpoint_controls["temperature"]["reading"]

        self.digital_card, digital_layout = self._make_card(text.DIGITAL_STATUS_TITLE)
        digital_grid = QGridLayout()
        digital_grid.setHorizontalSpacing(14)
        digital_grid.setVerticalSpacing(10)
        digital_layout.addLayout(digital_grid)
        self.digital_indicators = {}
        statuses = (
            ("atmosphere", text.ATMOSPHERE_STATUS_LABEL, text.DEMO_STATUS_ATMOSPHERE),
            ("door", text.DOOR_STATUS_LABEL, text.DEMO_STATUS_DOOR),
            ("air_flow", text.AIR_FLOW_STATUS_LABEL, text.DEMO_STATUS_OK),
            ("lamp_failure", text.LAMP_FAILURE_STATUS_LABEL, text.DEMO_STATUS_NO_FAILURE),
            ("plasma_failure", text.PLASMA_FAILURE_STATUS_LABEL, text.DEMO_STATUS_NO_FAILURE),
            ("magnetron_warning", text.MAGNETRON_WARNING_STATUS_LABEL, text.DEMO_STATUS_NORMAL),
            ("magnetron_overheat", text.MAGNETRON_OVERHEAT_STATUS_LABEL, text.DEMO_STATUS_NORMAL),
        )
        for index, (key, label, value) in enumerate(statuses):
            row, indicator = self._make_digital_indicator(label, value)
            digital_grid.addLayout(row, index // 2, index % 2)
            self.digital_indicators[key] = indicator
        digital_grid.setColumnStretch(0, 1)
        digital_grid.setColumnStretch(1, 1)

        self.module_card, module_layout = self._make_card(text.MODULE_CONTROLS_TITLE)
        self.vacuum_state = QLabel(text.SIMULATED_OFF)
        self.vacuum_state.setObjectName("DemoStatus")
        self.vacuum_button = QPushButton(text.SIMULATED_START_BUTTON)
        self.vacuum_button.setObjectName("DemoActionButton")
        vacuum_row = QHBoxLayout()
        vacuum_row.addWidget(QLabel(text.VACUUM_STATE_LABEL))
        vacuum_row.addWidget(self.vacuum_state)
        vacuum_row.addStretch()
        vacuum_row.addWidget(self.vacuum_button)
        module_layout.addLayout(vacuum_row)

        self.plasma_state = QLabel(text.SIMULATED_OFF)
        self.plasma_state.setObjectName("DemoStatus")
        self.plasma_button = QPushButton(text.SIMULATED_START_BUTTON)
        self.plasma_button.setObjectName("DemoActionButton")
        plasma_row = QHBoxLayout()
        plasma_row.addWidget(QLabel(text.PLASMA_STATE_LABEL))
        plasma_row.addWidget(self.plasma_state)
        plasma_row.addStretch()
        plasma_row.addWidget(self.plasma_button)
        module_layout.addLayout(plasma_row)

        self.back_button = QPushButton(text.BACK_BUTTON_TEXT)
        self.back_button.setObjectName("BackButton")

    def setup_layout(self):
        header = QHBoxLayout()
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.simulation_badge)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addWidget(self.start_process_button)
        action_row.addStretch()
        action_row.addWidget(self.save_recipe_button)
        action_row.addWidget(self.load_recipe_button)

        cards = QGridLayout()
        cards.setHorizontalSpacing(18)
        cards.setVerticalSpacing(16)
        cards.addWidget(self.equipment_card, 0, 0, 1, 2)
        cards.addWidget(self.gas_card, 1, 0)
        cards.addWidget(self.chamber_card, 1, 1)
        cards.addWidget(self.digital_card, 2, 0)
        cards.addWidget(self.module_card, 2, 1)
        cards.setColumnStretch(0, 1)
        cards.setColumnStretch(1, 1)

        footer = QHBoxLayout()
        footer.addWidget(self.simulation_description)
        footer.addStretch()
        footer.addWidget(self.back_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        layout.addLayout(header)
        layout.addLayout(action_row)
        layout.addLayout(cards, 1)
        layout.addLayout(footer)

    def connect_signals(self):
        self.back_button.clicked.connect(self.back_requested.emit)
        self.save_recipe_button.clicked.connect(self._show_recipe_pending_notice)
        self.load_recipe_button.clicked.connect(self._show_recipe_pending_notice)
        self.vacuum_button.clicked.connect(self._toggle_vacuum_demo)
        self.plasma_button.clicked.connect(self._toggle_plasma_demo)
        for key, controls in self._setpoint_controls.items():
            controls["button"].clicked.connect(
                partial(self._apply_setpoint, key)
            )
            controls["decrease"].clicked.connect(
                partial(self._adjust_setpoint, key, -1)
            )
            controls["increase"].clicked.connect(
                partial(self._adjust_setpoint, key, 1)
            )
            controls["edit"].textChanged.connect(
                partial(self._update_step_button_states, key)
            )
            self._update_step_button_states(key)

    def _show_recipe_pending_notice(self):
        QMessageBox.information(
            self,
            text.tr(text.RECIPE_FEATURE_PENDING_TITLE),
            text.tr(text.RECIPE_FEATURE_PENDING_MESSAGE),
        )

    @staticmethod
    def _make_card(title):
        card = QFrame()
        card.setObjectName("OperationCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        heading = QLabel(title)
        heading.setObjectName("OperationCardTitle")
        layout.addWidget(heading)
        return card, layout

    def _add_setpoint_row(
        self,
        parent_layout,
        key,
        label,
        initial,
        measured,
        maximum=None,
        range_label=None,
        unit=None,
        step=1.0,
        display_decimals=2,
    ):
        row_widget = QWidget()
        row_widget.setObjectName("SetpointRow")
        row_layout = QGridLayout(row_widget)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setHorizontalSpacing(8)
        row_layout.setVerticalSpacing(3)

        name_label = QLabel(label)
        name_label.setObjectName("SetpointLabel")
        edit = QLineEdit(initial)
        edit.setObjectName(f"SetpointInput_{key}")
        edit.setValidator(NonNegativeNumberValidator(maximum=maximum, decimals=3, parent=edit))
        edit.setFixedWidth(100)
        decrease_button = QPushButton("−")
        decrease_button.setObjectName("SetpointStepButton")
        decrease_button.setAccessibleName(f"Disminuir {label}")
        decrease_button.setToolTip(f"Disminuir de a {step:g}")
        decrease_button.setFixedSize(38, 36)
        increase_button = QPushButton("+")
        increase_button.setObjectName("SetpointStepButton")
        increase_button.setAccessibleName(f"Aumentar {label}")
        increase_button.setToolTip(f"Aumentar de a {step:g}")
        increase_button.setFixedSize(38, 36)
        apply_button = QPushButton(text.APPLY_DEMO_BUTTON)
        apply_button.setObjectName("DemoActionButton")
        reading = QLabel(f"{text.MEASURED_VALUE_PREFIX}: {measured}")
        reading.setObjectName("DemoValueSmall")
        feedback = QLabel(" ")
        feedback.setObjectName("SetpointFeedback")
        feedback.setMinimumHeight(14)
        feedback.setWordWrap(True)

        row_layout.addWidget(name_label, 0, 0, 1, 4)
        row_layout.addWidget(decrease_button, 1, 0)
        row_layout.addWidget(edit, 1, 1)
        row_layout.addWidget(increase_button, 1, 2)
        if range_label:
            range_text = QLabel(range_label)
        else:
            range_text = QLabel(unit or "")
        range_text.setObjectName("SetpointUnit")
        row_layout.addWidget(range_text, 1, 3)
        row_layout.addWidget(reading, 2, 0, 1, 3)
        row_layout.addWidget(apply_button, 2, 3)
        row_layout.addWidget(feedback, 3, 0, 1, 4)

        parent_layout.addWidget(row_widget)
        self._setpoint_controls[key] = {
            "edit": edit,
            "button": apply_button,
            "feedback": feedback,
            "reading": reading,
            "maximum": maximum,
            "step": step,
            "display_decimals": display_decimals,
            "decrease": decrease_button,
            "increase": increase_button,
        }

    @staticmethod
    def _make_digital_indicator(label, value):
        row = QHBoxLayout()
        name = QLabel(label)
        name.setObjectName("DigitalStatusLabel")
        status = QLabel(value)
        status.setObjectName("DigitalStatusValue")
        status.setAlignment(Qt.AlignCenter)
        row.addWidget(name)
        row.addStretch()
        row.addWidget(status)
        return row, status

    def _apply_setpoint(self, key, checked=False):
        controls = self._setpoint_controls[key]
        raw_value = controls["edit"].text().strip().replace(",", ".")
        try:
            value = float(raw_value)
        except ValueError:
            return self._reject_setpoint(controls)

        if not math.isfinite(value) or value < 0:
            return self._reject_setpoint(controls)

        maximum = controls["maximum"]
        if maximum is not None and value > maximum:
            return self._reject_setpoint(controls)

        self._accepted_setpoints[key] = value
        set_localized_text(controls["feedback"], text.SETPOINT_APPLIED)
        controls["feedback"].setProperty("valid", "true")
        self._refresh_style(controls["feedback"])
        self._update_step_button_states(key)
        return True

    def _adjust_setpoint(self, key, direction, checked=False):
        """Cambia y aplica el valor deseado en el paso configurado."""
        controls = self._setpoint_controls[key]
        try:
            current = float(controls["edit"].text().strip().replace(",", "."))
        except ValueError:
            return self._reject_setpoint(controls)

        candidate = round(current + direction * controls["step"], controls["display_decimals"])
        maximum = controls["maximum"]
        if candidate < 0 or (maximum is not None and candidate > maximum):
            return False

        controls["edit"].setText(f"{candidate:.{controls['display_decimals']}f}")
        return self._apply_setpoint(key)

    def _update_step_button_states(self, key, value=None):
        controls = self._setpoint_controls[key]
        try:
            current = float(controls["edit"].text().strip().replace(",", "."))
        except ValueError:
            controls["decrease"].setEnabled(False)
            controls["increase"].setEnabled(False)
            return

        maximum = controls["maximum"]
        step = controls["step"]
        controls["decrease"].setEnabled(current >= step)
        controls["increase"].setEnabled(maximum is None or current + step <= maximum)

    @staticmethod
    def _reject_setpoint(controls):
        set_localized_text(controls["feedback"], text.SETPOINT_INVALID)
        controls["feedback"].setProperty("valid", "false")
        NormalOperationScreen._refresh_style(controls["feedback"])
        return False

    @staticmethod
    def _refresh_style(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _toggle_vacuum_demo(self):
        self._states["vacuum"] = not self._states["vacuum"]
        active = self._states["vacuum"]
        set_localized_text(
            self.vacuum_state,
            text.SIMULATED_ON if active else text.SIMULATED_OFF,
        )
        set_localized_text(
            self.vacuum_button,
            text.SIMULATED_STOP_BUTTON if active else text.SIMULATED_START_BUTTON,
        )
        set_localized_text(
            self.pressure_reading,
            f"{text.MEASURED_VALUE_PREFIX}: {'0.120 Torr' if active else '0.760 Torr'}",
        )
        set_localized_text(
            self._setpoint_controls["mfc1"]["reading"],
            f"{text.MEASURED_VALUE_PREFIX}: {'0.50 SLPM' if active else '0.00 SLPM'}",
        )

    def _toggle_plasma_demo(self):
        self._states["plasma"] = not self._states["plasma"]
        active = self._states["plasma"]
        set_localized_text(
            self.plasma_state,
            text.SIMULATED_ON if active else text.SIMULATED_OFF,
        )
        set_localized_text(
            self.plasma_button,
            text.SIMULATED_STOP_BUTTON if active else text.SIMULATED_START_BUTTON,
        )
        set_localized_text(
            self.temperature_reading,
            f"{text.MEASURED_VALUE_PREFIX}: {'38.5 °C' if active else '24.0 °C'}",
        )

    def update_texts(self, *_):
        translate_widget_tree(self)
