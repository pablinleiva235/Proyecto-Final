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
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config.digital_signals import DIGITALSIGNALS
from config_gui.maintainer_signals import MAINTAINER_SIGNALS
from config_gui.strings import (
    BACK_BUTTON_TEXT,
    DIGITAL_INPUTS_TITLE,
    DIGITAL_OUTPUTS_TITLE,
    MAINTAINER_SIGNALS_TAB,
    MAINTAINER_SECUENCES_TAB,
    MAINTAINER_TITLE,
    DOOR_SEQUENCE_BUTTON,
    SOFT_VACUUM_SEQUENCE_BUTTON,
    MAIN_VACUUM_SEQUENCE_BUTTON,
    VENT_CHAMBER_SEQUENCE_BUTTON,
)
from gui.widgets.signal_widget import SignalWidget


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

    INPUT_DIRECTION = "IN"
    OUTPUT_DIRECTION = "OUT"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._signal_widgets: Dict[str, SignalWidget] = {}
        self._input_widgets: List[SignalWidget] = []
        self._output_widgets: List[SignalWidget] = []

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

    def create_widgets(self) -> None:
        """Crea los componentes visuales de la pantalla."""

        self.title_label = QLabel(MAINTAINER_TITLE)
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("MaintainerTabs")

        self.sequences_tab = QWidget()
        self.sequences_tab.setObjectName("MaintainerSequencesTab")

        self.signals_tab = QWidget()
        self.signals_tab.setObjectName("MaintainerSignalsTab")

        self.tabs.addTab(
            self.sequences_tab,
            MAINTAINER_SECUENCES_TAB,
        )

        self.tabs.addTab(
            self.signals_tab,
            MAINTAINER_SIGNALS_TAB,
        )

        # ---------------------------------------------------------------------
        # Pestaña de módulos funcionales
        # ---------------------------------------------------------------------

        self.door_sequence_button = QPushButton(
            DOOR_SEQUENCE_BUTTON
        )
        self.door_sequence_button.setObjectName(
            "MaintainerSequenceButton"
        )

        self.soft_vacuum_sequence_button = QPushButton(
            SOFT_VACUUM_SEQUENCE_BUTTON
        )
        self.soft_vacuum_sequence_button.setObjectName(
            "MaintainerSequenceButton"
        )

        self.main_vacuum_sequence_button = QPushButton(
            MAIN_VACUUM_SEQUENCE_BUTTON
        )
        self.main_vacuum_sequence_button.setObjectName(
            "MaintainerSequenceButton"
        )

        self.vent_chamber_sequence_button = QPushButton(
            VENT_CHAMBER_SEQUENCE_BUTTON
        )
        self.vent_chamber_sequence_button.setObjectName(
            "MaintainerSequenceButton"
        )

        # ---------------------------------------------------------------------
        # Pestaña de señales
        # ---------------------------------------------------------------------

        self.inputs_title_label = QLabel(
            DIGITAL_INPUTS_TITLE
        )
        self.inputs_title_label.setObjectName(
            "SectionTitleLabel"
        )

        self.outputs_title_label = QLabel(
            DIGITAL_OUTPUTS_TITLE
        )
        self.outputs_title_label.setObjectName(
            "SectionTitleLabel"
        )

        self._create_signal_widgets()

        # ---------------------------------------------------------------------
        # Navegación
        # ---------------------------------------------------------------------

        self.back_button = QPushButton(
            BACK_BUTTON_TEXT
        )
        self.back_button.setObjectName(
            "BackButton"
        )

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
        main_layout.setContentsMargins(
            48,
            32,
            48,
            32,
        )
        main_layout.setSpacing(24)

        main_layout.addWidget(
            self.title_label
        )

        main_layout.addWidget(
            self.tabs
        )

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

    # =========================================================================
    # Configuración de pestañas
    # =========================================================================

    def _setup_sequences_tab(self) -> None:
        """Organiza los controles de secuencias funcionales."""

        sequences_layout = QGridLayout(
            self.sequences_tab
        )

        sequences_layout.setContentsMargins(
            40,
            40,
            40,
            40,
        )

        sequences_layout.setHorizontalSpacing(30)
        sequences_layout.setVerticalSpacing(30)

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

        sequences_layout.setColumnStretch(
            0,
            1,
        )

        sequences_layout.setColumnStretch(
            1,
            1,
        )

        sequences_layout.setRowStretch(
            0,
            1,
        )

        sequences_layout.setRowStretch(
            1,
            1,
        )

    def _setup_signals_tab(self) -> None:
        """Organiza las señales digitales en entradas y salidas."""

        inputs_layout = self._create_signal_grid(
            self._input_widgets
        )

        outputs_layout = self._create_signal_grid(
            self._output_widgets
        )

        signals_layout = QVBoxLayout(
            self.signals_tab
        )

        signals_layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        signals_layout.setSpacing(24)

        signals_layout.addWidget(
            self.inputs_title_label
        )

        signals_layout.addLayout(
            inputs_layout
        )

        signals_layout.addSpacing(20)

        signals_layout.addWidget(
            self.outputs_title_label
        )

        signals_layout.addLayout(
            outputs_layout
        )

        signals_layout.addStretch()

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

            widget = SignalWidget(
                signal_name=signal_name,
                interactive=is_output,
            )

            self._signal_widgets[
                signal_name
            ] = widget

            if (
                direction
                == self.INPUT_DIRECTION
            ):
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

        grid_layout.setHorizontalSpacing(24)
        grid_layout.setVerticalSpacing(24)

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