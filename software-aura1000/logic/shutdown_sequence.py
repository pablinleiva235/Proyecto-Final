"""
Secuencia de apagado seguro del equipo.

Responsabilidades:
- Detener las secuencias funcionales.
- Intentar llevar todos los subsistemas a estado seguro.
- Aplicar el estado seguro global del hardware.
- Informar la finalización o los errores encontrados.

La secuencia intenta continuar con el apagado aunque
alguno de los subsistemas produzca un error.
"""

from PyQt5.QtCore import QObject, pyqtSignal


class ShutdownSequence(QObject):

    sequence_completed = pyqtSignal()
    sequence_error = pyqtSignal(str)

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

    def start(self):
        #Ejecuta la secuencia de apagado seguro.

        errors = self._shutdown_sequences()

        try:
            self._hardware.shutdown_state()

        except Exception as error:
            errors.append(
                f"Hardware safe state: {error}"
            )

        if errors:
            self.sequence_error.emit(
                " | ".join(errors)
            )
            return

        self.sequence_completed.emit()

    def _shutdown_sequences(self):
        """
        Intenta detener todas las secuencias funcionales.
        Si una secuencia falla, continúa intentando
        apagar las restantes.
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