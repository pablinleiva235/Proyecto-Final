"""Registro legible de la ejecución más reciente de una receta."""

from datetime import datetime
from pathlib import Path
import csv
from services.maintenance_data_log import MAINTENANCE_COLUMNS


RECIPE_LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "recipe.log"
RECIPE_DATA_PATH = RECIPE_LOG_PATH.with_name("recipe_data.csv")
RECIPE_LOG_DIRECTORY = RECIPE_LOG_PATH.parent / "recetas"
RECIPE_LOG_LIMIT = 100


def next_recipe_log_paths(directory=None):
    """Devuelve rutas coordinadas para el siguiente par de logs en rotación."""
    directory = Path(directory or RECIPE_LOG_DIRECTORY)
    latest_path = None
    latest_modified = None
    for number in range(1, RECIPE_LOG_LIMIT + 1):
        candidate = directory / f"recipe_{number}.log"
        try:
            modified = candidate.stat().st_mtime_ns
        except OSError:
            continue
        if latest_modified is None or modified > latest_modified:
            latest_path = candidate
            latest_modified = modified

    if latest_path is None:
        next_number = 1
    else:
        latest_number = int(latest_path.stem.removeprefix("recipe_"))
        next_number = latest_number % RECIPE_LOG_LIMIT + 1

    return (
        directory / f"recipe_{next_number}.log",
        directory / f"recipe_data_{next_number}.csv",
    )

PROCESS_DATA_UNITS = {"BARATRON": "Torr", "CHAMBER_TEMP": "°C"}


class RecipeDataLog:
    """Writes process data samples for a recipe."""

    def __init__(self, path=None):
        self.path = Path(path or RECIPE_DATA_PATH)
        self.error = None
        self._file = None
        self._writer = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._file = self.path.open("w", encoding="utf-8", newline="")
            self._writer = csv.writer(self._file)
            headers = ("timestamp", *(column for column, _, _ in MAINTENANCE_COLUMNS))
            self._writer.writerow(headers)
            self._file.flush()
        except (OSError, ValueError) as error:
            self.error = str(error)
            self.close()

    @property
    def available(self):
        return self._file is not None and self.error is None

    def record(self, values, timestamp=None):
        if not self.available:
            return False
        try:
            timestamp = timestamp or datetime.now().astimezone().isoformat(timespec="milliseconds")
            row = [timestamp]
            for _, signal, _ in MAINTENANCE_COLUMNS:
                value = values.get(signal)
                if value is None:
                    row.append("")
                elif signal == "PLASMA":
                    row.append("ON" if bool(value) else "OFF")
                else:
                    row.append(f"{float(value):g}")
            self._writer.writerow(row)
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
