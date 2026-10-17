"""Registro del último intento de apagado seguro."""

from datetime import datetime
from pathlib import Path

SHUTDOWN_LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "shutdown.log"


class ShutdownLog:
    """Sobrescribe ``logs/shutdown.log`` y conserva errores de escritura."""

    def __init__(self):
        self.path = SHUTDOWN_LOG_PATH
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
