"""
Controlador de apagado ordenado del equipo.

Responsabilidades:
- Coordinar la detención de las secuencias funcionales.
- Llevar el hardware al estado seguro final.
- Informar la finalización o error del apagado.

No modifica widgets directamente.
"""

from PyQt5.QtCore import QObject, pyqtSignal


class ShutdownController(QObject):

    shutdown_started = pyqtSignal()
    shutdown_completed = pyqtSignal()
    shutdown_error = pyqtSignal(str)

    def __init__(
        self,
        hardware,
        soft_vacuum_sequence,
        main_vacuum_sequence,
        vent_sequence,
        parent=None,
    ):
        super().__init__(parent)

        self._hardware = hardware

        self._soft_vacuum_sequence = (soft_vacuum_sequence)
        self._main_vacuum_sequence = (main_vacuum_sequence)
        self._vent_sequence = (vent_sequence)

        self._is_shutting_down = False

    @property
    def is_shutting_down(self):
        return self._is_shutting_down

    def start(self):
        if self._is_shutting_down:
            return

        self._is_shutting_down = True
        self.shutdown_started.emit()
        errors = self._shutdown_sequences()
        try:
            self._hardware.shutdown_state()

        except Exception as error:
            errors.append(f"Hardware safe state: {error}")

        if errors:
            self.shutdown_error.emit(" | ".join(errors))
            return
        self.shutdown_completed.emit()
        
    def _shutdown_sequences(self):
        """
        Intenta detener todas las secuencias funcionales.

        Si una secuencia falla, continúa intentando apagar
        las restantes y registra el error.
        """

        errors = []

        sequences = (
            ("Vent",self._vent_sequence),
            ("Main Vacuum",self._main_vacuum_sequence),
            ("Soft Vacuum",self._soft_vacuum_sequence),
        )
        for name, sequence in sequences:
            try:
                sequence.shutdown()

            except Exception as error:
                errors.append(
                    f"{name}: {error}"
                )

        return errors
    
    def _handle_error(
        self,
        error,
    ):
        self.shutdown_error.emit(
            str(error)
        )