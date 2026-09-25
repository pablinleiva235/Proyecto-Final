"""
Secuencia de control de puerta.

Responsabilidades:
- Abrir la puerta de la cámara.
- Cerrar la puerta de la cámara.
- Mantener el estado lógico actual.
- Validar si la apertura está permitida.
- Informar cambios de estado y errores.

No modifica widgets ni conoce MaintainerScreen.
"""

from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal

from config.digital_signals import ACTIVE, INACTIVE


class DoorState(Enum):
    OPEN = "open"
    CLOSED = "closed"
    OPENING = "opening"
    CLOSING = "closing"
    ERROR = "error"


class DoorSequence(QObject):
    """Gestiona el control físico de apertura y cierre de puerta."""

    state_changed = pyqtSignal(object)
    sequence_error = pyqtSignal(str)

    def __init__(
        self,
        hardware,
        can_open=None,
        parent=None,
    ):
        super().__init__(parent)

        self._hardware = hardware
        self._can_open = can_open

        # El estado inicial coincide con el estado seguro configurado:
        # DOOR_CLOSE_CMD activo y DOOR_OPEN_CMD inactivo.
        self._state = DoorState.CLOSED

    @property
    def state(self):
        """Devuelve el último estado lógico conocido."""
        return self._state

    def set_can_open(self, can_open):
        """
        Configura la validación externa que determina
        si la puerta puede abrirse.
        """
        self._can_open = can_open

    def toggle(self):
        """Solicita abrir o cerrar la puerta según el estado actual."""

        if self._state in (
            DoorState.OPENING,
            DoorState.CLOSING,
        ):
            return

        if self._state == DoorState.CLOSED:
            self.open()

        elif self._state == DoorState.OPEN:
            self.close()

    def open(self):
        """Ejecuta el comando físico de apertura."""

        if self._state in (
            DoorState.OPENING,
            DoorState.CLOSING,
        ):
            return

        # Interlock de seguridad.
        if self._can_open is not None:
            if not self._can_open():
                self.sequence_error.emit(
                    "No es posible abrir la puerta "
                    "en el estado actual del equipo."
                )
                return

        try:
            self._set_state(
                DoorState.OPENING
            )

            # Primero se elimina cualquier orden de cierre.
            self._hardware.digital_set(
                "DOOR_CLOSE_CMD",
                INACTIVE,
            )

            # Luego se solicita la apertura.
            self._hardware.digital_set(
                "DOOR_OPEN_CMD",
                ACTIVE,
            )

            self._set_state(
                DoorState.OPEN
            )

        except Exception as error:
            self._handle_error(error)

    def close(self):
        """Ejecuta el comando físico de cierre."""

        if self._state in (
            DoorState.OPENING,
            DoorState.CLOSING,
        ):
            return

        try:
            self._set_state(
                DoorState.CLOSING
            )

            # Primero se elimina cualquier orden de apertura.
            self._hardware.digital_set(
                "DOOR_OPEN_CMD",
                INACTIVE,
            )

            # Luego se solicita el cierre.
            self._hardware.digital_set(
                "DOOR_CLOSE_CMD",
                ACTIVE,
            )

            self._set_state(
                DoorState.CLOSED
            )

        except Exception as error:
            self._handle_error(error)

    def _set_state(self, state):
        """Actualiza y comunica el estado de la puerta."""

        self._state = state
        self.state_changed.emit(state)

    def _handle_error(self, error):
        """
        Intenta llevar las órdenes de puerta
        a un estado seguro ante una falla.
        """

        try:
            self._hardware.digital_set(
                "DOOR_OPEN_CMD",
                INACTIVE,
            )

            self._hardware.digital_set(
                "DOOR_CLOSE_CMD",
                INACTIVE,
            )

        except Exception as safe_error:
            print(
                "[DoorSequence] Error intentando "
                f"alcanzar estado seguro: {safe_error}"
            )

        self._set_state(
            DoorState.ERROR
        )

        self.sequence_error.emit(
            str(error)
        )