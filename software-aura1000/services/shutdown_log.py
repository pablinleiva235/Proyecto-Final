"""Registro del último intento de apagado seguro."""

from datetime import datetime
from pathlib import Path

SHUTDOWN_LOG_DIRECTORY = Path(__file__).resolve().parents[1] / "logs" / "shutdown"
SHUTDOWN_LOG_PATH = SHUTDOWN_LOG_DIRECTORY / "shutdown_1.log"
SHUTDOWN_LOG_LIMIT = 100


def next_shutdown_log_path(directory=None):
    """Devuelve el siguiente archivo dentro de la rotación circular de logs."""
    directory = Path(directory or SHUTDOWN_LOG_DIRECTORY)
    latest_number = None
    latest_modified = None
    for number in range(1, SHUTDOWN_LOG_LIMIT + 1):
        candidate = directory / f"shutdown_{number}.log"
        try:
            modified = candidate.stat().st_mtime_ns
        except OSError:
            continue
        if latest_modified is None or modified > latest_modified:
            latest_number = number
            latest_modified = modified

    next_number = 1 if latest_number is None else latest_number % SHUTDOWN_LOG_LIMIT + 1
    return directory / f"shutdown_{next_number}.log"


class ShutdownLog:
    """Guarda cada intento en rotación y conserva errores de escritura."""

    def __init__(self):
        # Usar el directorio de la ruta constante también permite aislar el
        # almacenamiento en pruebas y conserva la ruta seleccionada en errores.
        self.path = next_shutdown_log_path(SHUTDOWN_LOG_PATH.parent)
        self.errors = []
        self._file = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._file = self.path.open("w", encoding="utf-8")
        except OSError as error:
            self._record_log_error(error)

    def log(self, message):
        line = f"{datetime.now().astimezone().isoformat(timespec='seconds')} | {message}"
        if self._file is None:
            print(f"[ShutdownLog] {line}")
            return
        try:
            self._file.write(line + "\n")
            self._file.flush()
        except OSError as error:
            self._record_log_error(error)

    def log_result(self, name, success, detail=""):
        result = "OK" if success else "ERROR"
        suffix = f" | {detail}" if detail else ""
        self.log(f"{name}: {result}{suffix}")

    def _record_log_error(self, error):
        message = f"No se pudo escribir {self.path}: {error}"
        if message not in self.errors:
            self.errors.append(message)
        print(f"[ShutdownLog] {message}")
        if self._file is not None:
            try:
                self._file.close()
            except OSError:
                pass
            self._file = None

    def close(self):
        if self._file is not None:
            try:
                self._file.close()
            except OSError as error:
                self._record_log_error(error)
            finally:
                self._file = None
