# logic/door_sequence.py

"""
Secuencia de control de puerta.

Responsabilidades:
- Abrir la puerta de la cámara.
- Cerrar la puerta de la cámara.
- Mantener el estado lógico actual.
- Informar cambios de estado y errores.

No modifica widgets ni conoce MaintainerScreen.
"""

from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal

from config.digital_signals import ACTIVE, INACTIVE


class DoorState(Enum):
    OPEN = "open"
    CLOSED = "closed"
    PROCESSING = "processing"


class DoorSequence(QObject):
    """Gestiona el control físico de apertura y cierre de puerta."""

    state_changed = pyqtSignal(object)
    sequence_error = pyqtSignal(str)

    def __init__(self, hardware, parent=None):
        super().__init__(parent)

        self._hardware = hardware

        # El estado inicial coincide con el estado seguro configurado:
        # DOOR_CLOSE_CMD activo y DOOR_OPEN_CMD inactivo.
        self._state = DoorState.CLOSED

    @property
    def state(self):
        """Devuelve el último estado lógico conocido."""

        return self._state

    def toggle(self):
        """Solicita abrir o cerrar la puerta según el estado actual."""

        if self._state == DoorState.PROCESSING:
            return

        if self._state == DoorState.CLOSED:
            self.open()
        elif self._state == DoorState.OPEN:
            self.close()

    def open(self):
        """Ejecuta el comando físico de apertura."""

        if self._state == DoorState.PROCESSING:
            return

        try:
            self._set_state(DoorState.PROCESSING)

            # Se elimina primero el comando de cierre.
            self._hardware.digital_set(
                "DOOR_CLOSE_CMD",
                INACTIVE,
            )

            # Luego se solicita la apertura.
            self._hardware.digital_set(
                "DOOR_OPEN_CMD",
                ACTIVE,
            )

            self._set_state(DoorState.OPEN)

        except Exception as error:
            self._handle_error(error)

    def close(self):
        """Ejecuta el comando físico de cierre."""

        if self._state == DoorState.PROCESSING:
            return

        try:
            self._set_state(DoorState.PROCESSING)

            # Se elimina primero el comando de apertura.
            self._hardware.digital_set(
                "DOOR_OPEN_CMD",
                INACTIVE,
            )

            # Luego se solicita el cierre.
            self._hardware.digital_set(
                "DOOR_CLOSE_CMD",
                ACTIVE,
            )

            self._set_state(DoorState.CLOSED)

        except Exception as error:
            self._handle_error(error)

    def _set_state(self, state):
        """Actualiza y comunica el estado de la puerta."""

        self._state = state
        self.state_changed.emit(state)

    def _handle_error(self, error):
        """Gestiona errores durante el control de puerta."""

        self.sequence_error.emit(
            str(error)
        )