"""
Secuencia de Main Vacuum.

Responsabilidades:
- Activar y desactivar Main Vacuum.
- Mantener el estado lógico actual.
- Validar si la secuencia puede comenzar.
- Informar cambios de estado y errores.

No modifica widgets ni conoce MaintainerScreen.
"""

from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal

from config.digital_signals import ACTIVE, INACTIVE


class MainVacuumState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class MainVacuumSequence(QObject):
    """Gestiona el control de Main Vacuum."""

    state_changed = pyqtSignal(object)
    sequence_error = pyqtSignal(str)

    def __init__(
        self,
        hardware,
        can_start=None,
        can_stop=None,
        parent=None,
    ):
        super().__init__(parent)

        self._hardware = hardware
        self._can_start = can_start
        self._can_stop = can_stop

        self._state = MainVacuumState.IDLE

    @property
    def state(self):
        """Devuelve el último estado lógico conocido."""
        return self._state

    def set_can_start(self, can_start):
        """
        Configura la validación externa que determina
        si Main Vacuum puede iniciarse.
        """
        self._can_start = can_start

    def set_can_stop(self, can_stop):
        """
        Configura la validación externa que determina
        si Main Vacuum puede detenerse.
        """
        self._can_stop = can_stop

    def toggle(self):
        """Activa o desactiva Main Vacuum."""

        if self._state in (
            MainVacuumState.STARTING,
            MainVacuumState.STOPPING,
        ):
            return

        if self._state == MainVacuumState.IDLE:
            self.start()

        elif self._state == MainVacuumState.RUNNING:
            self.stop()

    def start(self):
        """Activa Main Vacuum."""

        if self._state != MainVacuumState.IDLE:
            return

        if self._can_start is not None:
            if not self._can_start():
                self.sequence_error.emit(
                    "No es posible iniciar Main Vacuum "
                    "en el estado actual del equipo."
                )
                return

        try:
            self._set_state(
                MainVacuumState.STARTING
            )

            self._hardware.digital_set(
                "MAIN_VACUUM_CONTROL",
                ACTIVE,
            )

            self._set_state(
                MainVacuumState.RUNNING
            )

        except Exception as error:
            self._handle_error(error)

    def stop(self):
        """Desactiva Main Vacuum."""

        if self._state != MainVacuumState.RUNNING:
            return

        if self._can_stop is not None:
            if not self._can_stop():
                self.sequence_error.emit(
                    "No es posible detener Main Vacuum "
                    "en el estado actual del equipo."
                )
                return

        try:
            self._set_state(
                MainVacuumState.STOPPING
            )

            self._set_safe_outputs()

            self._set_state(
                MainVacuumState.IDLE
            )

        except Exception as error:
            self._handle_error(error)

    def _set_safe_outputs(self):
        """Lleva Main Vacuum a su estado seguro."""

        self._hardware.digital_set(
            "MAIN_VACUUM_CONTROL",
            INACTIVE,
        )

    def _set_state(self, state):
        """Actualiza y comunica el estado."""

        self._state = state
        self.state_changed.emit(state)

    def _handle_error(self, error):
        """Gestiona errores de la secuencia."""

        try:
            self._set_safe_outputs()

        except Exception as safe_error:
            print(
                "[MainVacuumSequence] Error intentando "
                f"alcanzar estado seguro: {safe_error}"
            )

        self._set_state(
            MainVacuumState.ERROR
        )

        self.sequence_error.emit(
            str(error)
        )