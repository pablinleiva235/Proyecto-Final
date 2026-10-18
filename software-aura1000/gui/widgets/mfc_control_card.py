"""Tarjeta de lectura y control para MFC1 o MFC2."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from gui.widgets.localization import set_localized_text
from gui.widgets.status_indicator import StatusIndicatorWidget
from config_gui.strings import tr


class MFCControlCard(QFrame):
    flow_requested = pyqtSignal(str, float)
    valve_requested = pyqtSignal(str, bool)

    def __init__(self, name, gas, maximum_flow, parent=None):
        super().__init__(parent)
        self.name = name
        self.maximum_flow = float(maximum_flow)
        self.setObjectName("MFCControlCard")
        self._valve_open = False
        self._measurement_fault = False
        self.status_indicator = StatusIndicatorWidget("off", "Válvula cerrada")

        header = QHBoxLayout()
        self.title_label = QLabel(f"{name} — {gas}")
        self.title_label.setObjectName("MaintenanceCardTitle")
        self.valve_status = QLabel("CERRADA")
        self.valve_status.setObjectName("MaintenancePill")
        self.valve_status.setProperty("state", "inactive")
        header.addWidget(self.title_label)

        reading = QHBoxLayout()
        self.icon_label = QLabel(gas)
        self.icon_label.setObjectName("MaintenanceCardIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.measured_value = QLabel("---")
        self.measured_value.setObjectName("MaintenanceCardValue")
        self.measured_unit = QLabel("SLPM medidos")
        self.measured_unit.setObjectName("MaintenanceCardUnit")
        reading.addWidget(self.icon_label)
        reading.addWidget(self.measured_value)
        reading.addWidget(self.measured_unit)
        reading.addStretch()

        self.progress = QProgressBar()
        self.progress.setObjectName("MFCFlowProgress")
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.hide()

        setpoint_row = QHBoxLayout()
        self.setpoint_label = QLabel("Flujo deseado")
        self.setpoint_label.setObjectName("MaintenanceCardFooter")
        self.setpoint = QDoubleSpinBox()
        self.setpoint.setRange(0.0, self.maximum_flow)
        self.setpoint.setDecimals(2)
        self.setpoint.setSingleStep(0.05)
        self.setpoint.setSuffix(" SLPM")
        self.setpoint.setObjectName("MaintenanceSetpointInput")
        self.setpoint.setMaximumWidth(150)
        self.apply_button = QPushButton("Aplicar")
        self.apply_button.setObjectName("MFCControlButton")
        setpoint_row.addWidget(self.setpoint_label)
        setpoint_row.addStretch()
        setpoint_row.addWidget(self.setpoint)
        setpoint_row.addWidget(self.apply_button)

        self.valve_button = QPushButton("Abrir válvula")
        self.valve_button.setObjectName("MFCControlButton")
        self.valve_button.setCheckable(True)
        self.valve_button.setMinimumWidth(
            self.valve_button.fontMetrics().horizontalAdvance("Cerrar válvula") + 32
        )

        details = QVBoxLayout()
        details.setContentsMargins(0, 0, 0, 0)
        details.setSpacing(6)
        details.addLayout(header)
        details.addLayout(reading)

        overview = QHBoxLayout()
        overview.setSpacing(14)
        overview.addWidget(self.status_indicator)
        overview.addLayout(details, 1)
        overview.addWidget(self.valve_status)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)
        layout.addLayout(overview)
        layout.addWidget(self.progress)
        layout.addLayout(setpoint_row)
        layout.addWidget(self.valve_button)

        self.apply_button.clicked.connect(self._request_flow)
        self.valve_button.clicked.connect(
            lambda checked: self.valve_requested.emit(self.name, checked)
        )

    def _request_flow(self):
        self.flow_requested.emit(self.name, self.setpoint.value())

    def set_measured_flow(self, flow):
        flow = max(0.0, float(flow))
        self.measured_value.setText(f"{flow:.3f}")
        self.measured_value.setProperty("error", False)
        self.measured_value.setToolTip("")
        progress = min(1.0, flow / self.maximum_flow)
        self.progress.setValue(round(progress * 1000))
        self.progress.show()
        self._measurement_fault = False
        self._update_status_indicator()
        self.measured_value.style().unpolish(self.measured_value)
        self.measured_value.style().polish(self.measured_value)

    def set_measurement_error(self, message):
        self.measured_value.setText("ERR")
        self.measured_value.setProperty("error", True)
        self.measured_value.setToolTip(message)
        self.progress.hide()
        self._measurement_fault = True
        self.status_indicator.set_state("fault", "Error de lectura")
        self.measured_value.style().unpolish(self.measured_value)
        self.measured_value.style().polish(self.measured_value)

    def set_setpoint(self, flow):
        self.setpoint.setValue(float(flow))

    def set_valve_state(self, opened):
        self._valve_open = bool(opened)
        self.valve_button.blockSignals(True)
        self.valve_button.setChecked(bool(opened))
        valve_text = "Cerrar válvula" if opened else "Abrir válvula"
        set_localized_text(self.valve_button, valve_text)
        self.valve_button.blockSignals(False)
        set_localized_text(self.valve_status, "ABIERTA" if opened else "CERRADA")
        self.valve_status.setProperty("state", "active" if opened else "inactive")
        self.valve_status.style().unpolish(self.valve_status)
        self.valve_status.style().polish(self.valve_status)
        self._update_status_indicator()

    def _update_status_indicator(self):
        if self._measurement_fault:
            self.status_indicator.set_state("fault", "Error de lectura")
            return
        state = "on" if self._valve_open else "off"
        label = "Válvula abierta" if self._valve_open else "Válvula cerrada"
        self.status_indicator.set_state(state, label)

    def set_controls_enabled(self, enabled):
        enabled = bool(enabled)
        for widget in (self.setpoint, self.apply_button, self.valve_button):
            widget.setEnabled(enabled)
