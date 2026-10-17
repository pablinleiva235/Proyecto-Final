"""
Controlador del proceso de apagado del equipo.

Responsabilidades:
- Iniciar la secuencia de apagado.
- Evitar múltiples solicitudes simultáneas.
- Mantener el estado general del proceso.
- Propagar finalización y errores.

No accede directamente al hardware.
"""

from PyQt5.QtCore import QObject, pyqtSignal


class ShutdownController(QObject):

    shutdown_started = pyqtSignal()
    shutdown_completed = pyqtSignal()
    shutdown_error = pyqtSignal(str)

    def __init__(
        self,
        shutdown_sequence,
        parent=None,
    ):
        super().__init__(parent)

        self._shutdown_sequence = shutdown_sequence

        self._is_shutting_down = False

        self._shutdown_sequence.sequence_completed.connect(
            self._handle_sequence_completed
        )
        self._shutdown_sequence.sequence_error.connect(
            self._handle_sequence_error
        )

    @property
    def is_shutting_down(self):
        return self._is_shutting_down

    def start(self):
        # Inicia la secuencia de apagado del equipo.
        if self._is_shutting_down:
            return

        self._is_shutting_down = True
        self.shutdown_started.emit()
        self._shutdown_sequence.start()
        
        
    def _handle_sequence_completed(self):
        self.shutdown_completed.emit()

    def _handle_sequence_error(self,message):
        self.shutdown_error.emit(message)