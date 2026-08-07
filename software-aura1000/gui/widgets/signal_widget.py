"""
Widget reutilizable para representar visualmente el estado de una señal.

SignalWidget pertenece exclusivamente a la capa de presentación.

Responsabilidades:
- Mostrar el nombre de una señal.
- Mostrar su estado visual.
- Emitir una solicitud cuando el usuario hace click sobre una señal
  configurada como interactiva.

SignalWidget no:
- Accede al hardware.
- Lee ni escribe señales.
- Conoce puertos, bits o polaridades.
- Modifica automáticamente su estado cuando recibe un click.

El cambio de estado y su posterior confirmación son responsabilidad de
SignalController.
"""

from enum import Enum
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from config_gui.strings import (
    SIGNAL_STATE_ACTIVE,
    SIGNAL_STATE_INACTIVE,
    SIGNAL_STATE_PROCESSING,
)


class SignalVisualState(Enum):
    """Estados visuales disponibles para SignalWidget."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PROCESSING = "processing"


class SignalWidget(QFrame):
    """Tarjeta visual que representa el estado de una señal.

    Parameters
    ----------
    signal_name:
        Nombre lógico de la señal.

    interactive:
        Indica si el widget puede emitir una solicitud de cambio al recibir
        un clic.

    display_name:
        Nombre opcional para mostrar en pantalla. Si no se proporciona,
        se muestra ``signal_name``.

    parent:
        Widget padre de Qt.
    """

    toggle_requested = pyqtSignal(str)

    _STATE_TEXT = {
        SignalVisualState.ACTIVE: SIGNAL_STATE_ACTIVE,
        SignalVisualState.INACTIVE: SIGNAL_STATE_INACTIVE,
        SignalVisualState.PROCESSING: SIGNAL_STATE_PROCESSING,
    }

    def __init__(
        self,
        signal_name: str,
        interactive: bool,
        display_name: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self._signal_name = self._validate_signal_name(signal_name)
        self._interactive = self._validate_interactive(interactive)
        self._display_name = display_name or self._signal_name

        # Estado inicial temporal. El controlador deberá reemplazarlo con
        # la primera lectura confirmada proveniente del hardware.
        self._visual_state = SignalVisualState.INACTIVE

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

        self.setObjectName("signalWidget")

        # Se utiliza texto en lugar de bool para que el selector QSS
        # [interactive="true"] sea consistente.
        self.setProperty(
            "interactive",
            "true" if self._interactive else "false",
        )

        self._set_visual_state(self._visual_state)

    def create_widgets(self) -> None:
    
        self._name_label = QLabel(self._display_name)
        self._name_label.setObjectName("signalNameLabel")

        self._led_indicator = QLabel()
        self._led_indicator.setObjectName("signalLedIndicator")

        # El LED es puramente visual y no debe interceptar eventos del mouse.
        self._led_indicator.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )

        self._status_label = QLabel()
        self._status_label.setObjectName("signalStatusLabel")

    def setup_layout(self) -> None:
    
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)

        status_layout.addWidget(self._led_indicator)
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(14)

        main_layout.addWidget(self._name_label)
        main_layout.addLayout(status_layout)

    def connect_signals(self) -> None:
        """Conecta las señales internas del widget.

        Actualmente no existen controles internos que requieran conexiones.
        El clic sobre la tarjeta se procesa mediante ``mousePressEvent``.
        """

        pass

    # ================================================================
    # Propiedades públicas
    # ================================================================

    @property
    def signal_name(self) -> str:
        """Devuelve el nombre lógico de la señal."""

        return self._signal_name

    @property
    def visual_state(self) -> SignalVisualState:
        """Devuelve el estado visual actual."""

        return self._visual_state

    @property
    def is_interactive(self) -> bool:
        """Indica si el widget permite solicitar un cambio."""

        return self._interactive

    # ================================================================
    # Interfaz pública de actualización visual
    # ================================================================

    def set_active(self, active: bool) -> None:
        """Muestra la señal como activa o inactiva.

        Este método debe ser llamado por SignalController después de obtener
        un estado confirmado.

        Parameters
        ----------
        active:
            ``True`` para mostrar la señal activa.
            ``False`` para mostrar la señal inactiva.
        """

        if not isinstance(active, bool):
            raise TypeError(
                "'active' debe ser un valor booleano."
            )

        state = (
            SignalVisualState.ACTIVE
            if active
            else SignalVisualState.INACTIVE
        )

        self._set_visual_state(state)

    def set_processing(self) -> None:
        """Muestra que existe una solicitud de cambio en proceso.

        Mientras el widget se encuentra en PROCESSING, no puede emitir una
        nueva solicitud de cambio.
        """

        self._set_visual_state(
            SignalVisualState.PROCESSING
        )

    # ================================================================
    # Interacción del usuario
    # ================================================================

    def mousePressEvent(
        self,
        event: QMouseEvent,
    ) -> None:
        """Procesa el clic sobre la tarjeta.

        Se emite ``toggle_requested`` únicamente cuando:

        - Se utilizó el botón izquierdo.
        - El widget es interactivo.
        - Su estado actual es ACTIVE o INACTIVE.

        El widget no cambia automáticamente a PROCESSING. Esa decisión
        corresponde a SignalController.
        """

        if (
            event.button() == Qt.LeftButton
            and self._can_request_toggle()
        ):
            self.toggle_requested.emit(
                self._signal_name
            )

            event.accept()
            return

        super().mousePressEvent(event)

    # ================================================================
    # Gestión interna del estado
    # ================================================================

    def _set_visual_state(
        self,
        state: SignalVisualState,
    ) -> None:
        """Actualiza el texto y las propiedades dinámicas del widget."""

        if not isinstance(state, SignalVisualState):
            raise TypeError(
                "'state' debe ser una instancia de SignalVisualState."
            )

        self._visual_state = state

        self._status_label.setText(
            self._STATE_TEXT[state]
        )

        self.setProperty(
            "visualState",
            state.value,
        )

        self._led_indicator.setProperty(
            "visualState",
            state.value,
        )

        self._status_label.setProperty(
            "visualState",
            state.value,
        )

        self._update_cursor()

        # Qt no siempre vuelve a evaluar automáticamente las reglas QSS
        # cuando cambia una propiedad dinámica.
        self._refresh_style(self)
        self._refresh_style(self._led_indicator)
        self._refresh_style(self._status_label)

    def _can_request_toggle(self) -> bool:
        """Indica si el widget puede emitir una solicitud de cambio."""

        return (
            self._interactive
            and self.isEnabled()
            and self._visual_state
            in {
                SignalVisualState.ACTIVE,
                SignalVisualState.INACTIVE,
            }
        )

    def _update_cursor(self) -> None:
        """Actualiza el cursor según la posibilidad de interacción."""

        if self._can_request_toggle():
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    @staticmethod
    def _refresh_style(widget: QWidget) -> None:
        """Fuerza a Qt a reevaluar el APP_STYLE para el widget."""

        style = widget.style()

        style.unpolish(widget)
        style.polish(widget)

        widget.update()

    # ================================================================
    # Validaciones
    # ================================================================

    @staticmethod
    def _validate_signal_name(
        signal_name: str,
    ) -> str:
        """Valida y normaliza el nombre lógico de la señal."""

        if not isinstance(signal_name, str):
            raise TypeError(
                "'signal_name' debe ser una cadena de texto."
            )

        normalized_name = signal_name.strip()

        if not normalized_name:
            raise ValueError(
                "'signal_name' no puede estar vacío."
            )

        return normalized_name

    @staticmethod
    def _validate_interactive(
        interactive: bool,
    ) -> bool:
        """Valida el indicador de interacción."""

        if not isinstance(interactive, bool):
            raise TypeError(
                "'interactive' debe ser un valor booleano."
            )

        return interactive