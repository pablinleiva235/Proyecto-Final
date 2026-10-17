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
from services.shutdown_log import ShutdownLog


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
        shutdown_log = ShutdownLog()
        errors = []
        shutdown_log.log("Inicio del apagado seguro")
        errors.extend(shutdown_log.errors)
        errors.extend(self._shutdown_sequences(shutdown_log))
        try:
            hardware_errors = self._hardware.shutdown_state(
                result_callback=shutdown_log.log_result
            )
            errors.extend(hardware_errors or [])
        except Exception as error:
            message = f"Estado seguro global del hardware: {error}"
            errors.append(message)
            shutdown_log.log_result("Estado seguro global del hardware", False, str(error))

        errors.extend(shutdown_log.errors)
        if errors:
            shutdown_log.log("Apagado finalizado con fallas: " + " | ".join(errors))
        else:
            shutdown_log.log("Apagado finalizado sin fallas")
        shutdown_log.close()
        errors.extend(error for error in shutdown_log.errors if error not in errors)

        if errors:
            self.sequence_error.emit(
                " | ".join(errors)
            )
        self.sequence_completed.emit()

    def _shutdown_sequences(self, shutdown_log):
        """
        Intenta detener todas las secuencias funcionales.
        Si una secuencia falla, continúa intentando
        apagar las restantes.
        """

        errors = []

        sequences = (
            ("Venteo", self._vent_sequence),
            ("Vacío principal", self._main_vacuum_sequence),
            ("Soft Vacuum", self._soft_vacuum_sequence),
        )

        for name, sequence in sequences:
            shutdown_log.log(f"{name}: inicio")
            try:
                sequence.shutdown()
                shutdown_log.log_result(name, True)

            except Exception as error:
                message = f"{name}: {error}"
                errors.append(message)
                shutdown_log.log_result(name, False, str(error))

        return errors
