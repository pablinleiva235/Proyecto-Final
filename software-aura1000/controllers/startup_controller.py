"""
Controlador de la secuencia de arranque del Plasma Asher.

StartupController supervisa el estado de encendido del equipo y coordina
la ejecución de StartupSequence.

Responsabilidades:
- Iniciar la secuencia de startup.
- Mantener el estado general del proceso.
- Propagar progreso, finalización y errores.

No monitorea señales físicas ni accede directamente
al hardware.

La interacción con el hardware se realiza mediante Hardware.digital_read().
"""

from enum import Enum
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal


class StartupState(Enum):
    """Estados posibles durante el arranque de la aplicación."""

    IDLE = "idle"
    STARTING = "starting"
    READY = "ready"
    ERROR = "error"

class StartupController(QObject):
    """Supervisa y coordina la secuencia de arranque del equipo."""

    # Informa cambios en el estado general del arranque.
    state_changed = pyqtSignal(object)
    # Reenvía el progreso generado por StartupSequence.
    progress_changed = pyqtSignal(int)
    # Informa un error durante la secuencia.
    startup_error = pyqtSignal(str)

    def __init__(
        self,
        startup_sequence,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        self._startup_sequence = startup_sequence

        self._state = StartupState.IDLE

        self._startup_sequence.progress_changed.connect(
            self._handle_progress_changed
        )
        self._startup_sequence.startup_completed.connect(
            self._handle_startup_completed
        )
        self._startup_sequence.startup_error.connect(
            self._handle_startup_error
        )
        
    # =========================================================================
    # Interfaz pública
    # =========================================================================
    @property
    def state(self):
        return self._state
    
    def start(self) -> None:
        #Inicia la supervisión del arranque.

        if self._state == StartupState.STARTING:
            return

        self._set_state(
            StartupState.STARTING
        )

        self._startup_sequence.start()

    def stop(self) -> None:
        """Cancela cualquier timer de preencendido activo."""
        self._startup_sequence.stop()


    # =========================================================================
    # Eventos provenientes de StartupSequence
    # =========================================================================

    def _handle_progress_changed(self, progress: int) -> None:
        #Reenvía el progreso de la secuencia hacia la GUI.
        self.progress_changed.emit(progress)

    def _handle_startup_completed(self) -> None:
        #Finaliza correctamente la supervisión del arranque.
        self._set_state(StartupState.READY)

    def _handle_startup_error(self, message: str) -> None:
        #Gestiona un error ocurrido durante el arranque.
        self._set_state(StartupState.ERROR)
        self.startup_error.emit(message)


    # =========================================================================
    # Gestión de estado
    # =========================================================================

    def _set_state(self, state: StartupState) -> None:
        # Actualiza y comunica el estado general del arranque

        if self._state == state:
            return

        self._state = state

        self.state_changed.emit(state)

    
