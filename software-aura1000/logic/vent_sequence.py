"""
Secuencia de venteo de cámara.

Responsabilidades:
- Activar y desactivar el venteo de la cámara.
- Mantener el estado lógico actual.
- Validar si la secuencia puede comenzar.
- Detectar la condición de presión atmosférica.
- Esperar el tiempo de estabilización en atmósfera.
- Finalizar automáticamente el venteo.
- Informar cambios de estado y errores.

No modifica widgets ni conoce MaintainerScreen.
"""

from enum import Enum

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from config.digital_signals import ACTIVE, INACTIVE


VENT_STABILIZATION_TIME_MS = 4000


class VentState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class VentSequence(QObject):
    """Gestiona el venteo de la cámara."""

    state_changed = pyqtSignal(object)
    sequence_error = pyqtSignal(str)
    vent_completed = pyqtSignal()

    def __init__(
        self,
        hardware,
        can_start=None,
        parent=None,
    ):
        super().__init__(parent)

        self._hardware = hardware
        self._can_start = can_start
        self._state = VentState.IDLE

        self._stabilization_timer = QTimer(self)
        self._stabilization_timer.setSingleShot(True)

        self._stabilization_timer.timeout.connect(
            self._finish_vent
        )

    @property
    def state(self):
        """Devuelve el último estado lógico conocido."""
        return self._state

    def set_can_start(self, can_start):
        """Configura la validación de inicio."""
        self._can_start = can_start

    def toggle(self):
        """Activa o detiene manualmente el venteo."""

        if self._state in (
            VentState.STARTING,
            VentState.STOPPING,
        ):
            return

        if self._state == VentState.IDLE:
            self.start()

        elif self._state == VentState.RUNNING:
            self.stop()

    def start(self):
        """Inicia el venteo de la cámara."""

        if self._state != VentState.IDLE:
            return

        if self._can_start is not None:
            if not self._can_start():
                self.sequence_error.emit(
                    "No es posible iniciar el venteo "
                    "en el estado actual del equipo."
                )
                return

        try:
            self._set_state(
                VentState.STARTING
            )

            self._hardware.digital_set(
                "VENT_VALVE_CONTROL",
                ACTIVE,
            )

            self._set_state(
                VentState.RUNNING
            )

        except Exception as error:
            self._handle_error(error)

    def stop(self):
        """
        Detiene manualmente el venteo.

        Si estaba corriendo el tiempo de estabilización
        de ATM, también se cancela.
        """

        if self._state != VentState.RUNNING:
            return

        try:
            self._stabilization_timer.stop()

            self._set_state(
                VentState.STOPPING
            )

            self._set_safe_outputs()

            self._set_state(
                VentState.IDLE
            )

        except Exception as error:
            self._handle_error(error)

    def update_atmospheric_state(
        self,
        is_atmospheric,
    ):
        """
        Recibe el estado lógico de ATM_SWITCH.

        Cuando ATM_SWITCH permanece activo durante
        el tiempo de estabilización, el venteo
        finaliza automáticamente.
        """

        if self._state != VentState.RUNNING:
            return

        if is_atmospheric:

            if not self._stabilization_timer.isActive():
                self._stabilization_timer.start(
                    VENT_STABILIZATION_TIME_MS
                )

        else:

            if self._stabilization_timer.isActive():
                self._stabilization_timer.stop()

    def _finish_vent(self):
        """
        Finaliza automáticamente el venteo después
        de mantener ATM_SWITCH activo durante el
        tiempo de estabilización.
        """
        if self._state != VentState.RUNNING:
            return

        try:
            self._set_state(
                VentState.STOPPING
            )

            self._set_safe_outputs()

            self._set_state(
                VentState.IDLE
            )
            self.vent_completed.emit()
            
        except Exception as error:
            self._handle_error(error)

    def _set_safe_outputs(self):
        """Cierra la válvula de venteo."""

        self._hardware.digital_set(
            "VENT_VALVE_CONTROL",
            INACTIVE,
        )

    def _set_state(
        self,
        state,
    ):
        """Actualiza y comunica el estado."""

        self._state = state
        self.state_changed.emit(state)

    def _handle_error(
        self,
        error,
    ):
        """Gestiona errores de la secuencia."""

        self._stabilization_timer.stop()

        try:
            self._set_safe_outputs()

        except Exception as safe_error:
            print(
                "[VentSequence] Error intentando "
                f"alcanzar estado seguro: {safe_error}"
            )

        self._set_state(
            VentState.ERROR
        )

        self.sequence_error.emit(
            str(error)
        )