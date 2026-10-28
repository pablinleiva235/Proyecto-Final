"""
MaintainerScreen permite trabajar en dos niveles:

1. Pruebas funcionales:
   Permiten solicitar secuencias completas de diagnóstico o validación.

2. Señales individuales:
   Permiten visualizar las entradas digitales y controlar las salidas
   digitales de manera individual.

Responsabilidades:
- Organizar las pestañas de mantenimiento.
- Crear dinámicamente los SignalWidget configurados.
- Reenviar solicitudes de cambio de salidas.
- Emitir solicitudes de ejecución de pruebas funcionales.
- Actualizar visualmente el estado de las señales.
- Emitir una solicitud para volver a la pantalla anterior.

MaintainerScreen no:
- Ejecuta directamente secuencias de hardware.
- Lee ni escribe señales.
- Accede a puertos, bits o polaridades.
- Decide si una operación fue exitosa.
"""

from typing import Dict, List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config.digital_signals import DIGITALSIGNALS
from config_gui.maintainer_signals import (
    MAINTAINER_SIGNALS,
    MANUALLY_TOGGLABLE_OUTPUT_SIGNALS,
    SEQUENCE_CONTROLLED_OUTPUT_SIGNALS,
)
import config_gui.strings as myStr
from gui.widgets.signal_widget import SignalWidget
from gui.widgets.analog_readout_card import AnalogReadoutCard
from gui.widgets.mfc_control_card import MFCControlCard
from gui.widgets.localization import set_localized_text
from gui.widgets.status_indicator import StatusIndicatorWidget


class MaintainerScreen(QWidget):
    """Pantalla para diagnóstico y pruebas de mantenimiento."""

    back_requested = pyqtSignal()

    # Solicitudes de control individual de salidas.
    output_toggle_requested = pyqtSignal(str)

    # Solicitudes de ejecución de secuencias funcionales.
    door_sequence_requested = pyqtSignal()
    soft_vacuum_sequence_requested = pyqtSignal()
    main_vacuum_sequence_requested = pyqtSignal()
    vent_chamber_sequence_requested = pyqtSignal()
    mfc_flow_requested = pyqtSignal(str, float)
    mfc_valve_requested = pyqtSignal(str, bool)
    throttle_move_requested = pyqtSignal(bool)
    throttle_stop_requested = pyqtSignal()
    throttle_steps_requested = pyqtSignal(bool, int, bool)
    pressure_start_requested = pyqtSignal(float)
    pressure_stop_requested = pyqtSignal()
    temperature_start_requested = pyqtSignal(float)
    temperature_stop_requested = pyqtSignal()
    lamps13_requested = pyqtSignal(float)
    lamp2_requested = pyqtSignal(bool)
    plasma_requested = pyqtSignal(bool)

    INPUT_DIRECTION = "IN"
    OUTPUT_DIRECTION = "OUT"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._signal_widgets: Dict[str, SignalWidget] = {}
        self._module_signal_widgets: Dict[str, SignalWidget] = {}
        self._input_widgets: List[SignalWidget] = []
        self._output_widgets: List[SignalWidget] = []
        self._analog_values = {}
        self._manual_controls_locked = False
        self._pressure_control_active = False
        self._sequence_button_permissions = {}

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

    def create_widgets(self) -> None:
        """Crea los componentes visuales de la pantalla."""

        self.title_label = QLabel(myStr.MAINTAINER_TITLE)
        self.title_label.setObjectName("MaintainerTitle")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("MaintainerTabs")

        self.sequences_tab = QWidget()
        self.sequences_tab.setObjectName("MaintainerSequencesTab")
        self.sequences_tab.setStyleSheet(
            "QWidget#MaintainerSequencesTab QLabel { font-size: 12px; }"
            "QWidget#MaintainerSequencesTab QPushButton#MaintenanceActionButton {"
            " padding: 4px 6px; font-size: 12px; }"
            "QWidget#MaintainerSequencesTab QPushButton#MFCControlButton {"
            " padding: 4px 6px; font-size: 12px; }"
            "QWidget#MaintainerSequencesTab QDoubleSpinBox#MaintenanceSetpointInput {"
            " padding: 3px 5px; font-size: 12px; }"
            "QWidget#MaintainerSequencesTab QLabel#OperationReadoutLabel {"
            " font-size: 10px; }"
        )

        self.signals_tab = QWidget()
        self.signals_tab.setObjectName("MaintainerSignalsTab")

        self.tabs.addTab(
            self.sequences_tab,
            myStr.MAINTAINER_SECUENCES_TAB,
        )

        self.tabs.addTab(
            self.signals_tab,
            myStr.MAINTAINER_SIGNALS_TAB,
        )
        self.tabs.setTabToolTip(1, "Entradas y salidas digitales")

        # ---------------------------------------------------------------------
        # Pestaña de módulos funcionales
        # ---------------------------------------------------------------------

        self.door_sequence_button = QPushButton(
            myStr.DOOR_SEQUENCE_OPEN_BUTTON
        )
        self.door_sequence_button.setObjectName(
            "MaintainerSequenceButton"
        )

        self.soft_vacuum_sequence_button = QPushButton(
            myStr.SOFT_VACUUM_ON_BUTTON
        )
        self.soft_vacuum_sequence_button.setObjectName(
            "MaintainerSequenceButton"
        )

        self.main_vacuum_sequence_button = QPushButton(
            myStr.MAIN_VACUUM_ON_BUTTON
        )
        self.main_vacuum_sequence_button.setObjectName(
            "MaintainerSequenceButton"
        )

        self.vent_chamber_sequence_button = QPushButton(
            myStr.VENT_ON_BUTTON
        )
        self.vent_chamber_sequence_button.setObjectName(
            "MaintainerSequenceButton"
        )

        # ---------------------------------------------------------------------
        # Pestaña de señales
        # ---------------------------------------------------------------------

        self.inputs_title_label = QLabel(
            myStr.DIGITAL_INPUTS_TITLE
        )
        self.inputs_title_label.setObjectName(
            "SectionTitleLabel"
        )

        self.outputs_title_label = QLabel(
            myStr.DIGITAL_OUTPUTS_TITLE
        )
        self.outputs_title_label.setObjectName(
            "SectionTitleLabel"
        )

        self._create_signal_widgets()
        self._create_module_controls()
        self._create_analog_readouts()
        self._create_module_signal_controls()

        # ---------------------------------------------------------------------
        # Navegación
        # ---------------------------------------------------------------------

        self.back_button = QPushButton(
            myStr.BACK_BUTTON_TEXT
        )
        self.back_button.setObjectName(
            "BackButton"
        )
        self.operation_status_label = QLabel("")
        self.operation_status_label.setWordWrap(True)
        self.operation_status_label.setObjectName("MaintainerOperationStatus")

        self._sequence_buttons = {
        "door": self.door_sequence_button,
        "soft_vacuum": self.soft_vacuum_sequence_button,
        "main_vacuum": self.main_vacuum_sequence_button,
        "vent": self.vent_chamber_sequence_button,
        }

    def setup_layout(self) -> None:
        """Organiza las pestañas y la navegación."""

        self._setup_sequences_tab()
        self._setup_signals_tab()

        navigation_layout = QHBoxLayout()
        navigation_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        navigation_layout.addStretch()
        navigation_layout.addWidget(
            self.back_button
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 8)
        main_layout.setSpacing(8)

        main_layout.addWidget(
            self.title_label
        )

        main_layout.addWidget(
            self.tabs
        )
        main_layout.addWidget(self.operation_status_label)

        main_layout.addLayout(
            navigation_layout
        )

    def connect_signals(self) -> None:
        """Conecta navegación, pruebas y señales individuales."""

        self.back_button.clicked.connect(
            self.back_requested.emit
        )

        # Pruebas funcionales.
        self.door_sequence_button.clicked.connect(
            self.door_sequence_requested.emit
        )

        self.soft_vacuum_sequence_button.clicked.connect(
            self.soft_vacuum_sequence_requested.emit
        )

        self.main_vacuum_sequence_button.clicked.connect(
            self.main_vacuum_sequence_requested.emit
        )

        self.vent_chamber_sequence_button.clicked.connect(
            self.vent_chamber_sequence_requested.emit
        )

        # Control individual de salidas.
        for widget in self._output_widgets:
            widget.toggle_requested.connect(
                self._handle_output_toggle_requested
            )

        self.mfc1_card.flow_requested.connect(self.mfc_flow_requested.emit)
        self.mfc2_card.flow_requested.connect(self.mfc_flow_requested.emit)
        self.mfc1_card.valve_requested.connect(self.mfc_valve_requested.emit)
        self.mfc2_card.valve_requested.connect(self.mfc_valve_requested.emit)
        self.throttle_open_button.pressed.connect(lambda: self.throttle_move_requested.emit(False))
        self.throttle_close_button.pressed.connect(lambda: self.throttle_move_requested.emit(True))
        self.throttle_open_button.released.connect(self.throttle_stop_requested.emit)
        self.throttle_close_button.released.connect(self.throttle_stop_requested.emit)
        self.throttle_open_steps_button.clicked.connect(
            lambda: self.throttle_steps_requested.emit(
                False, self.throttle_step_count.value(), self.throttle_step_mode.currentIndex() == 1
            )
        )
        self.throttle_close_steps_button.clicked.connect(
            lambda: self.throttle_steps_requested.emit(
                True, self.throttle_step_count.value(), self.throttle_step_mode.currentIndex() == 1
            )
        )
        self.pressure_start_button.clicked.connect(
            lambda: self.pressure_start_requested.emit(self.pressure_setpoint.value())
        )
        self.pressure_stop_button.clicked.connect(self.pressure_stop_requested.emit)
        self.temperature_start_button.clicked.connect(
            lambda: self.temperature_start_requested.emit(self.temperature_setpoint.value())
        )
        self.temperature_stop_button.clicked.connect(self.temperature_stop_requested.emit)
        self.lamps13_button.clicked.connect(lambda: self.lamps13_requested.emit(self.lamps13_duration.value()))
        self.lamp2_button.clicked.connect(lambda checked: self.lamp2_requested.emit(checked))
        self.plasma_button.clicked.connect(lambda checked: self.plasma_requested.emit(checked))
        self._module_signal_widgets["DRIVER_ENABLE"].toggle_requested.connect(
            self._handle_output_toggle_requested
        )

    # =========================================================================
    # Configuración de pestañas
    # =========================================================================

    def _setup_sequences_tab(self) -> None:
        """Organiza los controles de secuencias funcionales."""

        # El contenido de mantenimiento puede superar la altura disponible en
        # fullscreen. Mantenerlo dentro de un scroll area evita que empuje la
        # navegación, que vive fuera de la pestaña.
        sequences_content = QWidget()
        sequences_layout = QGridLayout(
            sequences_content
        )

        sequences_layout.setContentsMargins(12, 12, 12, 12)
        sequences_layout.setHorizontalSpacing(12)
        sequences_layout.setVerticalSpacing(12)

        sequences_layout.addWidget(
            self.door_sequence_button,
            0,
            0,
        )

        sequences_layout.addWidget(
            self.soft_vacuum_sequence_button,
            0,
            1,
        )

        sequences_layout.addWidget(
            self.main_vacuum_sequence_button,
            1,
            0,
        )

        sequences_layout.addWidget(
            self.vent_chamber_sequence_button,
            1,
            1,
        )

        sequences_layout.addWidget(self.mfc1_card, 2, 0)
        sequences_layout.addWidget(self.mfc2_card, 2, 1)
        sequences_layout.addWidget(self.throttle_group, 3, 0)
        sequences_layout.addWidget(self.process_group, 3, 1)
        sequences_layout.addWidget(self.temperature_group, 4, 0)
        sequences_layout.addWidget(self.analog_readouts_group, 5, 0, 1, 2)
        sequences_layout.addWidget(self.module_signals_group, 6, 0, 1, 2)

        sequences_layout.setColumnStretch(
            0,
            1,
        )

        sequences_layout.setColumnStretch(
            1,
            1,
        )

        sequences_layout.setRowStretch(0, 0)
        sequences_layout.setRowStretch(1, 0)
        sequences_layout.setRowStretch(2, 0)
        sequences_layout.setRowStretch(3, 0)
        sequences_layout.setRowStretch(4, 0)
        sequences_layout.setRowStretch(5, 0)
        sequences_layout.setRowStretch(6, 0)

        self.sequences_scroll_area = QScrollArea(self.sequences_tab)
        self.sequences_scroll_area.setWidgetResizable(True)
        self.sequences_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.sequences_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.sequences_scroll_area.setWidget(sequences_content)

        sequences_tab_layout = QVBoxLayout(self.sequences_tab)
        sequences_tab_layout.setContentsMargins(0, 0, 0, 0)
        sequences_tab_layout.addWidget(self.sequences_scroll_area)

    def _setup_signals_tab(self) -> None:
        """Muestra entradas y salidas a la vez, con scroll independiente."""

        self.inputs_scroll_area = self._create_signal_scroll_area(
            self._input_widgets
        )
        self.outputs_scroll_area = self._create_signal_scroll_area(
            self._output_widgets
        )

        inputs_column = QWidget()
        inputs_layout = QVBoxLayout(inputs_column)
        inputs_layout.setContentsMargins(0, 0, 0, 0)
        inputs_layout.setSpacing(12)
        inputs_layout.addWidget(self.inputs_title_label)
        inputs_layout.addWidget(self.inputs_scroll_area)

        outputs_column = QWidget()
        outputs_layout = QVBoxLayout(outputs_column)
        outputs_layout.setContentsMargins(0, 0, 0, 0)
        outputs_layout.setSpacing(12)
        outputs_layout.addWidget(self.outputs_title_label)
        outputs_layout.addWidget(self.outputs_scroll_area)

        columns_layout = QHBoxLayout()
        columns_layout.setContentsMargins(8, 8, 8, 8)
        columns_layout.setSpacing(8)
        columns_layout.addWidget(inputs_column, 1)
        columns_layout.addWidget(outputs_column, 1)
        self.signals_tab.setLayout(columns_layout)

    def _create_signal_scroll_area(self, widgets: List[SignalWidget]) -> QScrollArea:
        """Crea una grilla desplazable para las señales de una categoría."""

        grid_layout = self._create_signal_grid(widgets, columns=1)
        content = QWidget()
        content.setLayout(grid_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidget(content)

        scroll_area.setMinimumHeight(100)
        return scroll_area

    def _create_module_controls(self):
        self.mfc1_card = MFCControlCard("MFC1", "O₂", 6.5)
        self.mfc2_card = MFCControlCard("MFC2", "N₂", 0.65, minimum_flow=0.1)
        self.mfc1_setpoint = self.mfc1_card.setpoint
        self.mfc2_setpoint = self.mfc2_card.setpoint
        self.mfc1_set_button = self.mfc1_card.apply_button
        self.mfc2_set_button = self.mfc2_card.apply_button
        self.mfc1_valve_button = self.mfc1_card.valve_button
        self.mfc2_valve_button = self.mfc2_card.valve_button

        self.throttle_group = QGroupBox(myStr.MAINTAINER_THROTTLE_TITLE)
        self.throttle_group.setObjectName("MaintainerCardGroup")
        throttle_layout = QVBoxLayout(self.throttle_group)
        throttle_buttons = QVBoxLayout()
        self.throttle_open_button = QPushButton(myStr.MAINTAINER_THROTTLE_OPEN)
        self.throttle_close_button = QPushButton(myStr.MAINTAINER_THROTTLE_CLOSE)
        self.throttle_open_button.setObjectName("MaintenanceActionButton")
        self.throttle_close_button.setObjectName("MaintenanceActionButton")
        throttle_buttons.addWidget(self.throttle_open_button)
        throttle_buttons.addWidget(self.throttle_close_button)
        self.throttle_step_count = QSpinBox()
        self.throttle_step_count.setRange(1, 1400)
        self.throttle_step_count.setValue(1)
        self.throttle_step_count.setSuffix(" pasos")
        self.throttle_step_count.setObjectName("ThrottleStepCount")
        self.throttle_step_mode = QComboBox()
        self.throttle_step_mode.addItems(("Full step", "Half step"))
        self.throttle_step_mode.setObjectName("ThrottleStepMode")
        step_mode_row = QHBoxLayout()
        step_mode_row.addWidget(QLabel("Modo de paso:"))
        step_mode_row.addWidget(self.throttle_step_mode)
        throttle_buttons.addLayout(step_mode_row)
        throttle_buttons.addWidget(self.throttle_step_count)
        step_action_row = QHBoxLayout()
        self.throttle_open_steps_button = QPushButton("Abrir pasos")
        self.throttle_open_steps_button.setObjectName("MaintenanceActionButton")
        self.throttle_close_steps_button = QPushButton("Cerrar pasos")
        self.throttle_close_steps_button.setObjectName("MaintenanceActionButton")
        step_action_row.addWidget(self.throttle_open_steps_button)
        step_action_row.addWidget(self.throttle_close_steps_button)
        throttle_buttons.addLayout(step_action_row)
        self.throttle_state_label = QLabel("DETENIDO")
        self.throttle_state_label.setObjectName("MaintenancePill")
        self.throttle_state_label.setProperty("state", "inactive")
        throttle_layout.addLayout(throttle_buttons)
        throttle_layout.addWidget(self.throttle_state_label)

        pressure_controls = QVBoxLayout()
        pressure_title = QLabel(myStr.MAINTAINER_PRESSURE_TITLE)
        pressure_title.setObjectName("OperationReadoutLabel")
        pressure_title.setWordWrap(True)
        pressure_title.setMaximumWidth(280)
        pressure_controls.addWidget(pressure_title)
        pressure_setpoint_row = QHBoxLayout()
        pressure_setpoint_row.addWidget(QLabel(myStr.MAINTAINER_PRESSURE_SETPOINT))
        self.pressure_setpoint = QDoubleSpinBox()
        self.pressure_setpoint.setRange(0.0, 3.0)
        self.pressure_setpoint.setDecimals(3)
        self.pressure_setpoint.setSingleStep(0.05)
        self.pressure_setpoint.setSuffix(" Torr")
        self.pressure_setpoint.setObjectName("MaintenanceSetpointInput")
        pressure_setpoint_row.addWidget(self.pressure_setpoint)
        pressure_controls.addLayout(pressure_setpoint_row)
        pressure_buttons = QVBoxLayout()
        self.pressure_start_button = QPushButton(myStr.MAINTAINER_PRESSURE_START)
        self.pressure_start_button.setObjectName("MaintenanceActionButton")
        self.pressure_stop_button = QPushButton(myStr.MAINTAINER_PRESSURE_STOP)
        self.pressure_stop_button.setObjectName("MaintenanceActionButton")
        self.pressure_stop_button.setEnabled(False)
        pressure_buttons.addWidget(self.pressure_start_button)
        pressure_buttons.addWidget(self.pressure_stop_button)
        pressure_controls.addLayout(pressure_buttons)
        self.pressure_reading_label = QLabel(myStr.MAINTAINER_PRESSURE_CURRENT_UNAVAILABLE)
        self.pressure_reading_label.setWordWrap(True)
        self.pressure_reading_label.setMaximumWidth(280)
        self.pressure_state_label = QLabel(myStr.MAINTAINER_PRESSURE_IDLE)
        self.pressure_state_label.setWordWrap(True)
        pressure_controls.addWidget(self.pressure_reading_label)
        pressure_controls.addWidget(self.pressure_state_label)
        throttle_layout.addLayout(pressure_controls)

        self.process_group = QGroupBox(myStr.MAINTAINER_PROCESS_TITLE)
        self.process_group.setObjectName("MaintainerCardGroup")
        process_layout = QVBoxLayout(self.process_group)
        self.lamps13_duration = QDoubleSpinBox()
        self.lamps13_duration.setRange(0.1, 28.0)
        self.lamps13_duration.setDecimals(1)
        self.lamps13_duration.setValue(1.0)
        self.lamps13_duration.setObjectName("MaintenanceSetpointInput")
        self.lamps13_button = QPushButton(myStr.MAINTAINER_LAMPS_PULSE)
        self.lamps13_button.setObjectName("MaintenanceActionButton")
        self.lamps13_state_label = QLabel("LISTAS")
        self.lamps13_state_label.setObjectName("MaintenancePill")
        self.lamps13_state_label.setProperty("state", "inactive")
        self.lamps13_indicator = StatusIndicatorWidget("off", "LISTAS", size=34)
        self.lamp2_button = QPushButton(myStr.MAINTAINER_LAMP2_ON)
        self.lamp2_button.setObjectName("MaintenanceActionButton")
        self.lamp2_button.setCheckable(True)
        self.lamp2_state_label = QLabel("APAGADA")
        self.lamp2_state_label.setObjectName("MaintenancePill")
        self.lamp2_state_label.setProperty("state", "inactive")
        self.lamp2_indicator = StatusIndicatorWidget("off", "APAGADA", size=34)
        self.plasma_button = QPushButton(myStr.MAINTAINER_PLASMA_ON)
        self.plasma_button.setObjectName("MaintenanceActionButton")
        self.plasma_button.setCheckable(True)
        self.plasma_state_label = QLabel("APAGADO")
        self.plasma_state_label.setObjectName("MaintenancePill")
        self.plasma_state_label.setProperty("state", "inactive")
        self.plasma_indicator = StatusIndicatorWidget("off", "APAGADO", size=34)
        lamps13_column = QWidget()
        lamps13_layout = QVBoxLayout(lamps13_column)
        lamps13_layout.setContentsMargins(0, 0, 0, 0)
        lamps13_status = QHBoxLayout()
        lamps13_status.addWidget(self.lamps13_indicator)
        lamps13_status.addWidget(self.lamps13_state_label)
        lamps13_status.addStretch()
        lamps13_layout.addLayout(lamps13_status)
        lamps13_layout.addWidget(QLabel(myStr.MAINTAINER_PULSE_SECONDS))
        lamps13_layout.addWidget(self.lamps13_duration)
        lamps13_layout.addWidget(self.lamps13_button)

        lamp2_column = QWidget()
        lamp2_layout = QVBoxLayout(lamp2_column)
        lamp2_layout.setContentsMargins(0, 0, 0, 0)
        lamp2_status = QHBoxLayout()
        lamp2_status.addWidget(self.lamp2_indicator)
        lamp2_status.addWidget(self.lamp2_state_label)
        lamp2_status.addStretch()
        lamp2_layout.addLayout(lamp2_status)
        lamp2_layout.addWidget(self.lamp2_button)

        plasma_column = QWidget()
        plasma_layout = QVBoxLayout(plasma_column)
        plasma_layout.setContentsMargins(0, 0, 0, 0)
        plasma_status = QHBoxLayout()
        plasma_status.addWidget(self.plasma_indicator)
        plasma_status.addWidget(self.plasma_state_label)
        plasma_status.addStretch()
        plasma_layout.addLayout(plasma_status)
        plasma_layout.addWidget(self.plasma_button)

        process_layout.addWidget(lamps13_column)
        process_layout.addWidget(lamp2_column)
        process_layout.addWidget(plasma_column)

        self.temperature_group = QGroupBox(myStr.MAINTAINER_TEMPERATURE_TITLE)
        self.temperature_group.setObjectName("MaintainerCardGroup")
        temperature_layout = QVBoxLayout(self.temperature_group)
        temperature_setpoint_row = QVBoxLayout()
        temperature_setpoint_row.addWidget(QLabel(myStr.MAINTAINER_TEMPERATURE_SETPOINT))
        self.temperature_setpoint = QDoubleSpinBox()
        self.temperature_setpoint.setRange(130.0, 200.0)
        self.temperature_setpoint.setDecimals(1)
        self.temperature_setpoint.setSingleStep(1.0)
        self.temperature_setpoint.setValue(180.0)
        self.temperature_setpoint.setSuffix(" °C")
        self.temperature_setpoint.setObjectName("MaintenanceSetpointInput")
        temperature_setpoint_row.addWidget(self.temperature_setpoint)
        temperature_layout.addLayout(temperature_setpoint_row)
        self.temperature_start_button = QPushButton(myStr.MAINTAINER_TEMPERATURE_START)
        self.temperature_start_button.setObjectName("MaintenanceActionButton")
        self.temperature_stop_button = QPushButton(myStr.MAINTAINER_TEMPERATURE_STOP)
        self.temperature_stop_button.setObjectName("MaintenanceActionButton")
        self.temperature_stop_button.setEnabled(False)
        temperature_buttons = QVBoxLayout()
        temperature_buttons.addWidget(self.temperature_start_button)
        temperature_buttons.addWidget(self.temperature_stop_button)
        temperature_layout.addLayout(temperature_buttons)
        self.temperature_reading_label = QLabel(myStr.MAINTAINER_TEMPERATURE_CURRENT_UNAVAILABLE)
        self.temperature_reading_label.setWordWrap(True)
        self.temperature_state_label = QLabel(myStr.MAINTAINER_TEMPERATURE_IDLE)
        self.temperature_state_label.setWordWrap(True)
        temperature_readouts = QVBoxLayout()
        temperature_readouts.addWidget(self.temperature_reading_label)
        temperature_readouts.addWidget(self.temperature_state_label)
        temperature_layout.addLayout(temperature_readouts)

    def _create_analog_readouts(self):
        names = (
            ("BARATRON", "Baratron · Presión", "Torr", "P"),
            ("CHAMBER_TEMP", "Temperatura de cámara", "°C", "T"),
            ("EOP", "End of Process", "V", "EOP"),
        )
        self.analog_readouts_group = QGroupBox("Lecturas")
        self.analog_readouts_group.setObjectName("MaintainerCardGroup")
        content = QWidget(self.analog_readouts_group)
        layout = QGridLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(20)
        for index, (name, label, unit, icon) in enumerate(names):
            row, column = divmod(index, 2)
            card = AnalogReadoutCard(label, unit, icon)
            layout.addWidget(card, row, column)
            self._analog_values[name] = card

        self._analog_values["MFC1_FLOW"] = self.mfc1_card
        self._analog_values["MFC2_FLOW"] = self.mfc2_card

        readouts_layout = QVBoxLayout(self.analog_readouts_group)
        readouts_layout.addWidget(content)

    def _create_module_signal_controls(self):
        self.module_signals_group = QGroupBox("Señales digitales")
        self.module_signals_group.setObjectName("MaintainerCardGroup")
        layout = QGridLayout(self.module_signals_group)
        self._module_signal_widgets = {
            "ATM_SWITCH": SignalWidget("ATM_SWITCH", interactive=False),
            "DRIVER_ENABLE": SignalWidget("DRIVER_ENABLE", interactive=True),
        }
        layout.addWidget(self._module_signal_widgets["ATM_SWITCH"], 0, 0)
        layout.addWidget(self._module_signal_widgets["DRIVER_ENABLE"], 0, 1)

    def set_analog_value(self, signal_name, value):
        widget = self._analog_values.get(signal_name)
        if widget is None:
            return
        value = float(value)
        if signal_name in ("BARATRON", "MFC1_FLOW", "MFC2_FLOW"):
            value = max(0.0, value)
        if signal_name in ("MFC1_FLOW", "MFC2_FLOW"):
            widget.set_measured_flow(value)
        else:
            precision = 1 if signal_name == "CHAMBER_TEMP" else 3
            widget.set_value(value, precision)

    def set_analog_error(self, signal_name, message):
        widget = self._analog_values.get(signal_name)
        if widget is not None:
            if signal_name in ("MFC1_FLOW", "MFC2_FLOW"):
                widget.set_measurement_error(message)
            else:
                widget.set_error(message)

    def set_process_state(self, name, enabled):
        if name == "lamps13":
            status_text = "PULSO ACTIVO" if enabled else "LISTAS"
            self._set_pill(
                self.lamps13_state_label,
                status_text,
                "active" if enabled else "inactive",
            )
            self.lamps13_indicator.set_state(
                "running" if enabled else "off",
                myStr.tr(status_text),
            )
        elif name == "lamp2":
            self.lamp2_button.setChecked(enabled)
            status_text = "ENCENDIDA" if enabled else "APAGADA"
            set_localized_text(
                self.lamp2_button,
                myStr.MAINTAINER_LAMP2_OFF if enabled else myStr.MAINTAINER_LAMP2_ON,
            )
            self._set_pill(
                self.lamp2_state_label,
                status_text,
                "active" if enabled else "inactive",
            )
            self.lamp2_indicator.set_state(
                "on" if enabled else "off",
                myStr.tr(status_text),
            )
        elif name == "plasma":
            self.plasma_button.setChecked(enabled)
            status_text = "ACTIVO" if enabled else "APAGADO"
            set_localized_text(
                self.plasma_button,
                myStr.MAINTAINER_PLASMA_OFF if enabled else myStr.MAINTAINER_PLASMA_ON,
            )
            self._set_pill(
                self.plasma_state_label,
                status_text,
                "active" if enabled else "inactive",
            )
            self.plasma_indicator.set_state(
                "on" if enabled else "off",
                myStr.tr(status_text),
            )

    def set_mfc_flow(self, name, flow):
        card = self.mfc1_card if name == "MFC1" else self.mfc2_card
        card.set_setpoint(float(flow))

    def set_mfc_valve_state(self, name, opened):
        card = self.mfc1_card if name == "MFC1" else self.mfc2_card
        card.set_valve_state(opened)

    def set_throttle_moving(self, moving, direction):
        state = direction.upper() if moving else "DETENIDO"
        self._set_pill(
            self.throttle_state_label,
            state,
            "active" if moving else "inactive",
        )
        opening = direction.startswith("abriendo")
        closing = direction.startswith("cerrando")
        is_burst = "pasos" in direction
        set_localized_text(
            self.throttle_open_button,
            myStr.MAINTAINER_THROTTLE_OPEN + (f" ({direction})" if moving and opening else ""),
        )
        set_localized_text(
            self.throttle_close_button,
            myStr.MAINTAINER_THROTTLE_CLOSE + (f" ({direction})" if moving and closing else ""),
        )
        controls_enabled = getattr(self, "_module_controls_enabled", False)
        manual_available = controls_enabled and not getattr(self, "_pressure_control_active", False)
        for widget in (
            self.throttle_step_count, self.throttle_step_mode,
            self.throttle_open_steps_button, self.throttle_close_steps_button,
        ):
            widget.setEnabled(manual_available and not moving)
        self.throttle_open_button.setEnabled(manual_available and not (moving and is_burst))
        self.throttle_close_button.setEnabled(manual_available and not (moving and is_burst))
        if not getattr(self, "_pressure_control_active", False):
            self.pressure_start_button.setEnabled(controls_enabled and not moving)
            self.pressure_setpoint.setEnabled(controls_enabled and not moving)

    def set_module_controls_enabled(self, enabled):
        enabled = bool(enabled) and not self._manual_controls_locked
        self.mfc1_card.set_controls_enabled(enabled)
        self.mfc2_card.set_controls_enabled(enabled)
        widgets = (
            self.throttle_open_button, self.throttle_close_button,
            self.throttle_step_count, self.throttle_step_mode,
            self.throttle_open_steps_button, self.throttle_close_steps_button,
            self.pressure_setpoint,
            self.temperature_setpoint,
            self.lamps13_duration, self.lamps13_button, self.lamp2_button,
            self.plasma_button,
        )
        for widget in widgets:
            widget.setEnabled(enabled)
        self._module_controls_enabled = enabled
        pressure_active = getattr(self, "_pressure_control_active", False)
        self.pressure_start_button.setEnabled(
            enabled and not pressure_active
        )
        self.pressure_stop_button.setEnabled(enabled and pressure_active)
        self.throttle_open_button.setEnabled(enabled and not pressure_active)
        self.throttle_close_button.setEnabled(enabled and not pressure_active)
        self.pressure_setpoint.setEnabled(enabled and not pressure_active)
        temperature_active = self.temperature_stop_button.isEnabled()
        self.temperature_start_button.setEnabled(enabled and not temperature_active)
        self.temperature_stop_button.setEnabled(enabled and temperature_active)
        self.temperature_setpoint.setEnabled(enabled and not temperature_active)
        self.lamps13_button.setEnabled(enabled and not temperature_active)
        self.lamp2_button.setEnabled(enabled and not temperature_active)
        self.plasma_button.setEnabled(enabled and not temperature_active)

    def set_pressure_reading(self, pressure):
        set_localized_text(
            self.pressure_reading_label,
            myStr.MAINTAINER_PRESSURE_CURRENT.format(pressure=float(pressure)),
        )

    def set_pressure_reading_unavailable(self, _message=None):
        set_localized_text(
            self.pressure_reading_label,
            myStr.MAINTAINER_PRESSURE_CURRENT_UNAVAILABLE,
        )

    def set_pressure_control_state(self, state):
        labels = {
            "detenido": myStr.MAINTAINER_PRESSURE_IDLE,
            "posicionando": myStr.MAINTAINER_PRESSURE_POSITIONING,
            "regulando": myStr.MAINTAINER_PRESSURE_RUNNING,
            "reposicionando": "Volviendo a la posición de reposo...",
        }
        set_localized_text(self.pressure_state_label, labels.get(state, state))
        active = state in ("posicionando", "regulando", "reposicionando")
        self._pressure_control_active = active
        self.pressure_stop_button.setEnabled(active)
        controls_enabled = getattr(self, "_module_controls_enabled", False)
        self.pressure_start_button.setEnabled(controls_enabled and not active)
        self.pressure_setpoint.setEnabled(controls_enabled and not active)
        self.throttle_open_button.setEnabled(controls_enabled and not active)
        self.throttle_close_button.setEnabled(controls_enabled and not active)
        for widget in (
            self.throttle_step_count, self.throttle_step_mode,
            self.throttle_open_steps_button, self.throttle_close_steps_button,
        ):
            widget.setEnabled(controls_enabled and not active)

    def set_pressure_control_error(self, message):
        set_localized_text(
            self.pressure_state_label,
            myStr.MAINTAINER_PRESSURE_ERROR.format(message=message),
        )

    def set_temperature_reading(self, temperature):
        set_localized_text(
            self.temperature_reading_label,
            myStr.MAINTAINER_TEMPERATURE_CURRENT.format(temperature=float(temperature)),
        )

    def set_temperature_reading_unavailable(self, _message=None):
        set_localized_text(
            self.temperature_reading_label,
            myStr.MAINTAINER_TEMPERATURE_CURRENT_UNAVAILABLE,
        )

    def set_temperature_control_state(self, state):
        labels = {
            "detenido": myStr.MAINTAINER_TEMPERATURE_IDLE,
            "precalentando": myStr.MAINTAINER_TEMPERATURE_RAMP,
            "manteniendo": myStr.MAINTAINER_TEMPERATURE_HOLD,
        }
        set_localized_text(self.temperature_state_label, labels.get(state, state))
        active = state in ("precalentando", "manteniendo")
        controls_enabled = getattr(self, "_module_controls_enabled", False)
        self.temperature_stop_button.setEnabled(active and controls_enabled)
        self.temperature_start_button.setEnabled(controls_enabled and not active)
        self.temperature_setpoint.setEnabled(controls_enabled and not active)
        self.lamps13_button.setEnabled(controls_enabled and not active)
        self.lamp2_button.setEnabled(controls_enabled and not active)
        self.plasma_button.setEnabled(controls_enabled and not active)

    def set_temperature_control_error(self, message):
        set_localized_text(
            self.temperature_state_label,
            myStr.MAINTAINER_TEMPERATURE_ERROR.format(message=message),
        )


    @staticmethod
    def _set_pill(widget, text, state):
        set_localized_text(widget, text)
        widget.setProperty("state", state)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def set_operation_message(self, message, is_error=False):
        set_localized_text(self.operation_status_label, message)
        self.operation_status_label.setProperty("error", bool(is_error))
        self.operation_status_label.style().unpolish(self.operation_status_label)
        self.operation_status_label.style().polish(self.operation_status_label)
        self.operation_status_label.update()

    # =========================================================================
    # Interfaz pública para SignalController
    # =========================================================================

    def set_signal_active(
        self,
        signal_name: str,
        active: bool,
    ) -> None:
        """Actualiza una señal con un estado confirmado."""

        widget = self._get_signal_widget(
            signal_name
        )

        widget.set_active(
            active
        )
        module_widget = self._module_signal_widgets.get(signal_name)
        if module_widget is not None:
            module_widget.set_active(active)

    def set_signal_fault_monitoring(self, signal_name: str, enabled: bool) -> None:
        """Controla cuándo una entrada de falla se interpreta visualmente como tal."""
        self._get_signal_widget(signal_name).set_fault_monitoring_enabled(enabled)

    def set_signal_error(self, signal_name: str, message: str) -> None:
        """Muestra el error sobre la tarjeta sin alterar su último estado."""
        self._get_signal_widget(signal_name).set_error(message)
        module_widget = self._module_signal_widgets.get(signal_name)
        if module_widget is not None:
            module_widget.set_error(message)

    def set_signal_processing(
        self,
        signal_name: str,
    ) -> None:
        """Muestra una señal de salida en estado PROCESSING."""

        widget = self._get_signal_widget(
            signal_name
        )

        if not widget.is_interactive:
            raise ValueError(
                f"La señal '{signal_name}' "
                "es de solo lectura y no puede pasar "
                "al estado PROCESSING."
            )

        widget.set_processing()
        module_widget = self._module_signal_widgets.get(signal_name)
        if module_widget is not None:
            module_widget.set_processing()

    def get_signal_names(self) -> tuple:
        """Devuelve los nombres de las señales mostradas."""

        return tuple(
            self._signal_widgets.keys()
        )

    # =========================================================================
    # Creación dinámica de señales
    # =========================================================================

    def _create_signal_widgets(self) -> None:
        """Crea SignalWidget desde la configuración seleccionada."""

        for signal_name in MAINTAINER_SIGNALS:
            signal_config = self._get_signal_config(
                signal_name
            )

            direction = signal_config["dir"]

            is_output = (
                direction
                == self.OUTPUT_DIRECTION
            )
            is_controllable_output = (
                is_output
                and signal_name in MANUALLY_TOGGLABLE_OUTPUT_SIGNALS
            )
            module_controlled_output = (
                is_output
                and signal_name in SEQUENCE_CONTROLLED_OUTPUT_SIGNALS
            )

            widget = SignalWidget(
                signal_name=signal_name,
                interactive=is_controllable_output,
                module_controlled=module_controlled_output,
            )

            self._signal_widgets[
                signal_name
            ] = widget

            if (direction == self.INPUT_DIRECTION):
                self._input_widgets.append(
                    widget
                )

            else:
                self._output_widgets.append(
                    widget
                )

    def _create_signal_grid(
        self,
        widgets: List[SignalWidget],
        columns: int = 2,
    ) -> QGridLayout:
        """Construye una grilla para una colección de señales."""

        if columns < 1:
            raise ValueError(
                "'columns' debe ser mayor o igual a 1."
            )

        grid_layout = QGridLayout()

        grid_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        grid_layout.setHorizontalSpacing(12)
        grid_layout.setVerticalSpacing(12)

        for index, widget in enumerate(
            widgets
        ):
            row = (
                index
                // columns
            )

            column = (
                index
                % columns
            )

            grid_layout.addWidget(
                widget,
                row,
                column,
            )

        for column in range(
            columns
        ):
            grid_layout.setColumnStretch(
                column,
                1,
            )

        return grid_layout

    # =========================================================================
    # Gestión interna
    # =========================================================================

    def _handle_output_toggle_requested(
        self,
        signal_name: str,
    ) -> None:
        """Reenvía una solicitud de cambio de salida."""

        self.output_toggle_requested.emit(
            signal_name
        )

    def _get_signal_widget(
        self,
        signal_name: str,
    ) -> SignalWidget:
        """Obtiene el widget asociado con una señal."""

        try:
            return self._signal_widgets[
                signal_name
            ]

        except KeyError as error:
            raise KeyError(
                f"La señal '{signal_name}' "
                "no está registrada en MaintainerScreen."
            ) from error

    def _get_signal_config(
        self,
        signal_name: str,
    ) -> dict:
        """Obtiene y valida la configuración de una señal."""

        try:
            signal_config = DIGITALSIGNALS[
                signal_name
            ]

        except KeyError as error:
            raise KeyError(
                f"La señal '{signal_name}' está incluida "
                "en MAINTAINER_SIGNALS, pero no existe "
                "en DIGITALSIGNALS."
            ) from error

        direction = signal_config.get(
            "dir"
        )

        if direction not in {
            self.INPUT_DIRECTION,
            self.OUTPUT_DIRECTION,
        }:
            raise ValueError(
                f"La señal '{signal_name}' posee "
                f"una dirección inválida: {direction!r}."
            )

        return signal_config

    # =========================================================================
    # Secuencia puerta
    # =========================================================================
    def set_door_state(self, state):
        #Actualiza el texto del botón de puerta según el estado actual
        if state.value == "opening":
            set_localized_text(self.door_sequence_button, myStr.DOOR_SEQUENCE_OPENING_BUTTON)

        elif state.value == "closing":
            set_localized_text(self.door_sequence_button, myStr.DOOR_SEQUENCE_CLOSING_BUTTON)

        elif state.value == "open":
            set_localized_text(self.door_sequence_button, myStr.DOOR_SEQUENCE_CLOSE_BUTTON)

        elif state.value == "closed":
            set_localized_text(self.door_sequence_button, myStr.DOOR_SEQUENCE_OPEN_BUTTON)

        elif state.value == "error":
            set_localized_text(self.door_sequence_button, myStr.DOOR_SEQUENCE_ERROR_BUTTON)
    
    # =========================================================================
    # Secuencia Soft Vacuum
    # =========================================================================
    def set_soft_vacuum_state(self, state):
        #Actualiza el texto del botón de Soft Vacuum según el estado actual
        if state.value == "starting":
            set_localized_text(self.soft_vacuum_sequence_button, myStr.SOFT_VACUUM_ON_BUTTON)

        elif state.value == "running":
            set_localized_text(self.soft_vacuum_sequence_button, myStr.SOFT_VACUUM_OFF_BUTTON)

        elif state.value == "stopping":
            set_localized_text(self.soft_vacuum_sequence_button, myStr.SOFT_VACUUM_OFF_BUTTON)

        elif state.value == "idle":
            set_localized_text(self.soft_vacuum_sequence_button, myStr.SOFT_VACUUM_ON_BUTTON)

        elif state.value == "error":
            set_localized_text(self.soft_vacuum_sequence_button, myStr.SOFT_VACUUM_ERROR_BUTTON)

    # =========================================================================
    # Secuencia Main Vacuum
    # =========================================================================
    def set_main_vacuum_state(self, state):
        #Actualiza el texto del botón de Main Vacuum según el estado actual de la secuencia.
        if state.value == "starting":
            set_localized_text(self.main_vacuum_sequence_button, myStr.MAIN_VACUUM_ON_BUTTON)

        elif state.value == "running":
            set_localized_text(self.main_vacuum_sequence_button, myStr.MAIN_VACUUM_OFF_BUTTON)

        elif state.value == "stopping":
            set_localized_text(self.main_vacuum_sequence_button, myStr.MAIN_VACUUM_OFF_BUTTON)

        elif state.value == "idle":
            set_localized_text(self.main_vacuum_sequence_button, myStr.MAIN_VACUUM_ON_BUTTON)

        elif state.value == "error":
            set_localized_text(self.main_vacuum_sequence_button, myStr.MAIN_VACUUM_ERROR_BUTTON)

    def set_sequence_enabled(
        self,
        sequence_name,
        enabled,
    ):
        button = self._sequence_buttons.get(
            sequence_name
        )

        if button is not None:
            self._sequence_button_permissions[sequence_name] = bool(enabled)
            button.setEnabled(bool(enabled) and not self._manual_controls_locked)

    def set_manual_controls_locked(self, locked):
        """Bloquea acciones manuales durante la ejecución de una receta."""
        self._manual_controls_locked = bool(locked)
        self.back_button.setEnabled(not locked)
        for widget in self._output_widgets:
            widget.setEnabled(not locked)
        driver_widget = self._module_signal_widgets.get("DRIVER_ENABLE")
        if driver_widget is not None:
            driver_widget.setEnabled(not locked)
        for name, button in self._sequence_buttons.items():
            button.setEnabled(
                not locked and self._sequence_button_permissions.get(name, False)
            )
        self.set_module_controls_enabled(
            getattr(self, "_module_controls_enabled", False)
        )


    # =========================================================================
    # Secuencia de Venteo
    # =========================================================================
    def set_vent_state(self,state):
        # modificar el texto del botón de venteo según el estado actual de la secuencia
        if state.value == "starting":
            set_localized_text(self.vent_chamber_sequence_button, myStr.VENT_ON_BUTTON)
        elif state.value == "running":
            set_localized_text(self.vent_chamber_sequence_button, myStr.VENT_OFF_BUTTON)
        elif state.value == "stopping":
            set_localized_text(self.vent_chamber_sequence_button, myStr.VENT_OFF_BUTTON)
        elif state.value == "idle":
            set_localized_text(self.vent_chamber_sequence_button, myStr.VENT_ON_BUTTON)
        elif state.value == "error":
            set_localized_text(self.vent_chamber_sequence_button, myStr.VENT_ERROR_BUTTON)
