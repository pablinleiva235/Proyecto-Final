"""
Secuencia de Soft Vacuum.

Responsabilidades:
- Activar y desactivar Soft Vacuum.
- Mantener el estado lógico actual.
- Validar si la secuencia puede comenzar.
- Informar cambios de estado y errores.

No modifica widgets ni conoce MaintainerScreen.
"""

from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal

from config.digital_signals import ACTIVE, INACTIVE


class SoftVacuumState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class SoftVacuumSequence(QObject):
    """Gestiona el control de Soft Vacuum."""

    state_changed = pyqtSignal(object)
    sequence_error = pyqtSignal(str)

    def __init__(
        self,
        hardware,
        can_start=None,
        parent=None,
    ):
        super().__init__(parent)

        self._hardware = hardware
        self._can_start = can_start

        self._state = SoftVacuumState.IDLE

    @property
    def state(self):
        """Devuelve el último estado lógico conocido."""
        return self._state

    def set_can_start(self, can_start):
        """
        Configura la validación externa que determina
        si Soft Vacuum puede iniciarse.
        """
        self._can_start = can_start

    def toggle(self):
        """Activa o desactiva Soft Vacuum."""

        if self._state in (
            SoftVacuumState.STARTING,
            SoftVacuumState.STOPPING,
        ):
            return

        if self._state == SoftVacuumState.IDLE:
            self.start()

        elif self._state == SoftVacuumState.RUNNING:
            self.stop()

    def start(self):
        """Activa Soft Vacuum."""

        if self._state in (
            SoftVacuumState.STARTING,
            SoftVacuumState.STOPPING,
        ):
            return

        # Interlock de seguridad.
        if self._can_start is not None:
            if not self._can_start():
                self.sequence_error.emit(
                    "No es posible iniciar Soft Vacuum "
                    "en el estado actual del equipo."
                )
                return

        try:
            self._set_state(
                SoftVacuumState.STARTING
            )

            self._hardware.digital_set(
                "SOFT_START_CONTROL",
                ACTIVE,
            )

            self._set_state(
                SoftVacuumState.RUNNING
            )

        except Exception as error:
            self._handle_error(error)

    def stop(self):
        """Desactiva Soft Vacuum."""

        if self._state in (
            SoftVacuumState.STARTING,
            SoftVacuumState.STOPPING,
        ):
            return

        try:
            self._set_state(
                SoftVacuumState.STOPPING
            )

            self._set_safe_outputs()

            self._set_state(
                SoftVacuumState.IDLE
            )

        except Exception as error:
            self._handle_error(error)

    def _set_safe_outputs(self):
        """Lleva Soft Vacuum a su estado seguro."""

        self._hardware.digital_set(
            "SOFT_START_CONTROL",
            INACTIVE,
        )

    def _set_state(self, state):
        """Actualiza y comunica el estado."""

        self._state = state
        self.state_changed.emit(state)

    def _handle_error(self, error):
        """
        Intenta llevar Soft Vacuum a un
        estado seguro ante una falla.
        """

        try:
            self._set_safe_outputs()

        except Exception as safe_error:
            print(
                "[SoftVacuumSequence] Error intentando "
                f"alcanzar estado seguro: {safe_error}"
            )

        self._set_state(
            SoftVacuumState.ERROR
        )

        self.sequence_error.emit(
            str(error)
        )