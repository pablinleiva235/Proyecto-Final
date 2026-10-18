"""Tarjeta de lectura para una entrada analógica de mantenimiento."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from gui.widgets.localization import set_localized_text
from gui.widgets.status_indicator import StatusIndicatorWidget


class AnalogReadoutCard(QFrame):
    """Presenta una lectura analógica con nombre, unidad y estado."""

    def __init__(self, title, unit, icon, parent=None):
        super().__init__(parent)
        self.setObjectName("MaintenanceCard")
        self.status_indicator = StatusIndicatorWidget("off", title)

        header = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("MaintenanceCardTitle")
        self.type_label = QLabel("ADC")
        self.type_label.setObjectName("MaintenancePill")
        self.type_label.setProperty("state", "info")
        header.addWidget(self.title_label)

        reading = QHBoxLayout()
        self.icon_label = QLabel(icon)
        self.icon_label.setObjectName("MaintenanceCardIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.value_label = QLabel("---")
        self.value_label.setObjectName("MaintenanceCardValue")
        self.unit_label = QLabel(unit)
        self.unit_label.setObjectName("MaintenanceCardUnit")
        reading.addWidget(self.icon_label)
        reading.addWidget(self.value_label)
        reading.addWidget(self.unit_label)
        reading.addStretch()

        self.footer_label = QLabel("Lectura analógica")
        self.footer_label.setObjectName("MaintenanceCardFooter")

        details = QVBoxLayout()
        details.setContentsMargins(0, 0, 0, 0)
        details.setSpacing(6)
        details.addLayout(header)
        details.addLayout(reading)
        details.addWidget(self.footer_label)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)
        layout.addWidget(self.status_indicator)
        layout.addLayout(details, 1)
        layout.addWidget(self.type_label)

    def set_value(self, value, precision=3):
        self.value_label.setText(f"{float(value):.{precision}f}")
        set_localized_text(self.type_label, "Lectura")
        self.type_label.setProperty("state", "active")
        self.value_label.setProperty("error", False)
        self.value_label.setToolTip("")
        self.status_indicator.set_state("on", "Lectura disponible")
        self._refresh_styles()

    def set_error(self, message):
        self.value_label.setText("ERR")
        set_localized_text(self.type_label, "ERROR")
        self.type_label.setProperty("state", "error")
        self.value_label.setProperty("error", True)
        self.value_label.setToolTip(message)
        self.status_indicator.set_state("fault", "Error de lectura")
        self._refresh_styles()

    def _refresh_styles(self):
        for widget in (self.type_label, self.value_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
