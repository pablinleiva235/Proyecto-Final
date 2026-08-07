"""
Pantalla de mantenimiento del Plasma Asher.

Esta pantalla organiza visualmente las señales disponibles para tareas de
diagnóstico y mantenimiento.

Responsabilidades:
- Crear y organizar los widgets de señales.
- Separar las entradas digitales de las salidas digitales.
- Reenviar las solicitudes de cambio generadas por las salidas.
- Actualizar visualmente los estados recibidos desde una capa externa.
- Emitir una solicitud para volver a la pantalla anterior.

La lectura y escritura de señales será responsabilidad de SignalController.
"""

from typing import Dict, List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.digital_signals import DIGITALSIGNALS
from config_gui.maintainer_signals import MAINTAINER_SIGNALS
from config_gui.strings import (
    BACK_BUTTON_TEXT,
    DIGITAL_INPUTS_TITLE,
    DIGITAL_OUTPUTS_TITLE,
    MAINTAINER_TITLE,
)
from gui.widgets.signal_widget import SignalWidget


class MaintainerScreen(QWidget):
    """Pantalla para visualizar y controlar señales del equipo."""

    back_requested = pyqtSignal()

    # La pantalla reenvía la solicitud sin ejecutar directamente la operación.
    output_toggle_requested = pyqtSignal(str)

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

        self.inputs_title_label = QLabel(DIGITAL_INPUTS_TITLE)
        self.inputs_title_label.setObjectName("SectionTitleLabel")

        self.outputs_title_label = QLabel(DIGITAL_OUTPUTS_TITLE)
        self.outputs_title_label.setObjectName("SectionTitleLabel")

        self.back_button = QPushButton(BACK_BUTTON_TEXT)
        self.back_button.setObjectName("BackButton")

        self._create_signal_widgets()

    def setup_layout(self) -> None:
        """Organiza las señales en secciones de entradas y salidas."""

        inputs_layout = self._create_signal_grid(
            self._input_widgets
        )

        outputs_layout = self._create_signal_grid(
            self._output_widgets
        )

        navigation_layout = QHBoxLayout()
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        navigation_layout.addStretch()
        navigation_layout.addWidget(self.back_button)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(48, 32, 48, 32)
        main_layout.setSpacing(24)

        main_layout.addWidget(self.title_label)
        main_layout.addSpacing(10)

        main_layout.addWidget(self.inputs_title_label)
        main_layout.addLayout(inputs_layout)

        main_layout.addSpacing(20)

        main_layout.addWidget(self.outputs_title_label)
        main_layout.addLayout(outputs_layout)

        main_layout.addStretch()
        main_layout.addLayout(navigation_layout)


    def connect_signals(self) -> None:
        """Conecta navegación y solicitudes de las señales de salida."""

        self.back_button.clicked.connect(
            self.back_requested.emit
        )

        for widget in self._output_widgets:
            widget.toggle_requested.connect(
                self._handle_output_toggle_requested
            )

    # ==================================================================
    # Interfaz pública para SignalController
    # ==================================================================

    def set_signal_active(
        self,
        signal_name: str,
        active: bool,
    ) -> None:
        """Actualiza una señal con un estado confirmado.

        Este método será invocado más adelante por SignalController después
        de obtener una lectura válida o confirmar una escritura.

        Parameters
        ----------
        signal_name:
            Nombre lógico de la señal que se desea actualizar.

        active:
            ``True`` si la señal está activa.
            ``False`` si la señal está inactiva.
        """

        widget = self._get_signal_widget(signal_name)
        widget.set_active(active)

    def set_signal_processing(
        self,
        signal_name: str,
    ) -> None:
        """Muestra una salida en estado de procesamiento."""

        widget = self._get_signal_widget(signal_name)

        if not widget.is_interactive:
            raise ValueError(
                f"La señal '{signal_name}' no es interactiva "
                "y no puede pasar a PROCESSING."  #cambiar por un string de error en config_gui.strings
            )

        widget.set_processing()

    def get_signal_names(self) -> tuple:
        """Devuelve los nombres de todas las señales mostradas."""

        return tuple(self._signal_widgets.keys())
    
    # =========================================================================
    # Creación dinámica de señales
    # =========================================================================

    def _create_signal_widgets(self) -> None:
        """Crea los widgets a partir de la configuración seleccionada."""

        for signal_name in MAINTAINER_SIGNALS:
            signal_config = self._get_signal_config(
                signal_name
            )

            direction = signal_config["dir"]
            is_output = direction == self.OUTPUT_DIRECTION

            widget = SignalWidget(
                signal_name=signal_name,
                interactive=is_output,
            )

            self._signal_widgets[signal_name] = widget

            if direction == self.INPUT_DIRECTION:
                self._input_widgets.append(widget)
            else:
                self._output_widgets.append(widget)

    def _create_signal_grid(
        self,
        widgets: List[SignalWidget],
        columns: int = 2,
    ) -> QGridLayout:
        """Construye una grilla para una colección de señales.

        Parameters
        ----------
        widgets:
            Widgets que se deben incorporar a la grilla.

        columns:
            Cantidad máxima de columnas utilizadas.

        Returns
        -------
        QGridLayout
            Layout configurado con los widgets recibidos.
        """

        if columns < 1:
            raise ValueError(
                "'columns' debe ser mayor o igual a 1."
            )

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(24)
        grid_layout.setVerticalSpacing(24)

        for index, widget in enumerate(widgets):
            row = index // columns
            column = index % columns

            grid_layout.addWidget(
                widget,
                row,
                column,
            )

        # Mantiene una distribución uniforme cuando la última fila
        # no contiene todas las columnas.
        for column in range(columns):
            grid_layout.setColumnStretch(column, 1)

        return grid_layout


    # ==================================================================
    # Gestión interna
    # ==================================================================

    def _handle_output_toggle_requested(
        self,
        signal_name: str,
    ) -> None:
        """Reenvía una solicitud de cambio sin modificar el estado."""
        print(f"[MaintainerScreen] Toggle solicitado: {signal_name}")
        self.output_toggle_requested.emit(signal_name)

    def _get_signal_widget(
        self,
        signal_name: str,
    ) -> SignalWidget:
        """Obtiene el widget asociado con una señal registrada."""

        try:
            return self._signal_widgets[signal_name]

        except KeyError as error:
            raise KeyError(
                f"La señal '{signal_name}' no está registrada "
                "en MaintainerScreen." #cambiar por un string de error en config_gui.strings
            ) from error

    def _get_signal_config(
        self,
        signal_name: str,
    ) -> dict:
        """Obtiene y valida la configuración técnica de una señal."""

        try:
            signal_config = DIGITALSIGNALS[signal_name]

        except KeyError as error:
            raise KeyError(
                f"La señal '{signal_name}' está incluida en "
                "MAINTAINER_SIGNALS, pero no existe en DIGITALSIGNALS."
            ) from error

        direction = signal_config.get("dir")

        if direction not in {
            self.INPUT_DIRECTION,
            self.OUTPUT_DIRECTION,
        }:
            raise ValueError(
                f"La señal '{signal_name}' posee una dirección "
                f"inválida: {direction!r}. Se esperaba 'IN' u 'OUT'."
            )

        return signal_config
