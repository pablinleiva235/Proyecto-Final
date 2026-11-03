"""CSV recorder for maintenance screen measurements."""

import csv
from datetime import datetime
from pathlib import Path


MAINTENANCE_DATA_DIRECTORY = (
    Path(__file__).resolve().parents[1] / "logs" / "mantenimiento_data"
)
MAINTENANCE_COLUMNS = (
    ("pressure_Torr", "BARATRON", "Torr"),
    ("temperature_C", "CHAMBER_TEMP", "°C"),
    ("MFC1_flow_SLPM", "MFC1_FLOW", "SLPM"),
    ("MFC2_flow_SLPM", "MFC2_FLOW", "SLPM"),
    ("throttle_position_steps", "THROTTLE_POSITION", "steps"),
    ("plasma_state", "PLASMA", "ON/OFF"),
)


class MaintenanceDataLog:
    """Writes one wide row per timestamp to an independent maintenance CSV."""

    def __init__(self, path=None):
        self.path = Path(path) if path else self.new_path()
        self.error = None
        self._file = None
        self._writer = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._file = self.path.open("x", encoding="utf-8", newline="")
            self._writer = csv.writer(self._file)
            self._writer.writerow(("timestamp", *(column for column, _, _ in MAINTENANCE_COLUMNS)))
            self._file.flush()
        except (OSError, ValueError) as error:
            self.error = str(error)
            self.close()

    @staticmethod
    def new_path(now=None):
        now = now or datetime.now().astimezone()
        stamp = now.strftime("%Y%m%d_%H%M")
        return MAINTENANCE_DATA_DIRECTORY / f"mantenimiento_{stamp}.csv"

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
        file_handle = self._file
        self._file = None
        self._writer = None
        if file_handle is None:
            return
        try:
            file_handle.flush()
            file_handle.close()
        except (OSError, ValueError) as error:
            if self.error is None:
                self.error = str(error)
