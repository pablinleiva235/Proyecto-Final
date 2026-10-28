"""Registro legible de la ejecución más reciente de una receta."""

from datetime import datetime
from pathlib import Path
import csv


RECIPE_LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "recipe.log"
RECIPE_DATA_PATH = RECIPE_LOG_PATH.with_name("recipe_data.csv")

PROCESS_DATA_UNITS = {"BARATRON": "Torr", "CHAMBER_TEMP": "°C"}


class RecipeDataLog:
    """CSV de lecturas de presión y temperatura para graficar la receta."""

    def __init__(self, path=None):
        self.path = Path(path or RECIPE_DATA_PATH)
        self.error = None
        self._file = None
        self._writer = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._file = self.path.open("w", encoding="utf-8", newline="")
            self._writer = csv.writer(self._file)
            self._writer.writerow(("timestamp", "señal", "valor", "unidad"))
            self._file.flush()
        except (OSError, ValueError) as error:
            self.error = str(error)
            self.close()

    @property
    def available(self):
        return self._file is not None and self.error is None

    def record(self, signal, value, timestamp=None):
        if not self.available:
            return False
        unit = PROCESS_DATA_UNITS.get(signal)
        if unit is None:
            return True
        try:
            timestamp = timestamp or datetime.now().astimezone().isoformat(timespec="milliseconds")
            self._writer.writerow((timestamp, signal, f"{float(value):g}", unit))
            self._file.flush()
            return True
        except (OSError, ValueError, TypeError) as error:
            self.error = str(error)
            self.close()
            return False

    def close(self):
        if self._file is None:
            return
        file_handle = self._file
        self._file = None
        self._writer = None
        try:
            file_handle.flush()
        except (OSError, ValueError) as error:
            if self.error is None:
                self.error = str(error)
        try:
            file_handle.close()
        except (OSError, ValueError) as error:
            if self.error is None:
                self.error = str(error)

ANALOG_UNITS = {
    "BARATRON": "Torr",
    "CHAMBER_TEMP": "°C",
    "MFC1_FLOW": "SLPM",
    "MFC2_FLOW": "SLPM",
    "EOP": "V",
}


class RecipeLog:
    """Sobrescribe el archivo por ejecución y falla explícitamente al escribir."""

    def __init__(self, path=None):
        self.path = Path(path or RECIPE_LOG_PATH)
        self.error = None
        self._file = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._file = self.path.open("w", encoding="utf-8", newline="\n")
        except OSError as error:
            self.error = str(error)

    @property
    def available(self):
        return self._file is not None and self.error is None

    def record(self, event, readings, outputs=None):
        if not self.available:
            return False
        timestamp = datetime.now().astimezone().isoformat(timespec="milliseconds")
        parts = []
        for name, unit in ANALOG_UNITS.items():
            reading = readings.get(name)
            if reading is None:
                parts.append(f"{name}=NO DISPONIBLE")
            else:
                value, read_at = reading
                parts.append(f"{name}={value:g} {unit} (lectura {read_at})")
        event = str(event).replace("\r", " ").replace("\n", " ")
        output_text = self._format_outputs(outputs or {})
        line = f"{timestamp} | {event} | Salidas: {output_text} | " + "; ".join(parts) + "\n"
        try:
            self._file.write(line)
            self._file.flush()
            return True
        except (OSError, ValueError) as error:
            self.error = str(error)
            self.close()
            return False

    @staticmethod
    def _format_outputs(outputs):
        if not outputs:
            return "ninguna"
        formatted = []
        for name, value in outputs.items():
            if isinstance(value, bool):
                value = "ACTIVO" if value else "INACTIVO"
            formatted.append(f"{name}={value}")
        return ", ".join(formatted)

    def close(self):
        if self._file is None:
            return
        file_handle = self._file
        self._file = None
        try:
            file_handle.flush()
        except (OSError, ValueError) as error:
            if self.error is None:
                self.error = str(error)
        try:
            file_handle.close()
        except (OSError, ValueError) as error:
            if self.error is None:
                self.error = str(error)
