"""Modal dialog for choosing the hardware backend before application startup."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from config_gui.strings import (
    APP_TITLE,
    STARTUP_CANCEL,
    STARTUP_CONTINUE,
    STARTUP_MODE_TITLE,
    STARTUP_REAL_MODE,
    STARTUP_SIMULATION_MODE,
    tr,
)


class StartupModeDialog(QDialog):
    """Let the operator select real or simulated startup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr(APP_TITLE))
        self.setModal(True)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(18)

        self.mode_title_label = QLabel(tr(STARTUP_MODE_TITLE))
        self.mode_title_label.setObjectName("StartupModeTitle")
        self.mode_title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.mode_title_label)

        self.real_mode_radio = QRadioButton(tr(STARTUP_REAL_MODE))
        self.simulation_mode_radio = QRadioButton(tr(STARTUP_SIMULATION_MODE))
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.real_mode_radio)
        self.mode_group.addButton(self.simulation_mode_radio)
        self.real_mode_radio.setChecked(True)
        layout.addWidget(self.real_mode_radio)
        layout.addWidget(self.simulation_mode_radio)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.cancel_button = QPushButton(tr(STARTUP_CANCEL))
        self.continue_button = QPushButton(tr(STARTUP_CONTINUE))
        self.continue_button.setDefault(True)
        self.cancel_button.clicked.connect(self.reject)
        self.continue_button.clicked.connect(self.accept)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.continue_button)
        layout.addLayout(buttons)

    @property
    def simulation_selected(self):
        return self.simulation_mode_radio.isChecked()
