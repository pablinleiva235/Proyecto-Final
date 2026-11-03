import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from services.maintenance_data_log import MaintenanceDataLog, MAINTENANCE_COLUMNS


class MaintenanceDataLogTests(unittest.TestCase):
    def test_writes_timestamped_rows_and_leaves_unavailable_values_empty(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "maintenance.csv"
            log = MaintenanceDataLog(path)
            values = {
                "BARATRON": 0.25,
                "CHAMBER_TEMP": 42.5,
                "MFC1_FLOW": 1.2,
                "MFC2_FLOW": None,
                "THROTTLE_POSITION": 17,
                "PLASMA": True,
            }
            self.assertTrue(log.record(values, "2026-11-03T12:00:00-03:00"))
            log.close()

            with path.open(encoding="utf-8", newline="") as data_file:
                rows = list(csv.DictReader(data_file))
            self.assertEqual(
                list(rows[0]),
                ["timestamp", *(column for column, _, _ in MAINTENANCE_COLUMNS)],
            )
            self.assertEqual(rows[0]["timestamp"], "2026-11-03T12:00:00-03:00")
            self.assertEqual(rows[0]["MFC1_flow_SLPM"], "1.2")
            self.assertEqual(rows[0]["MFC2_flow_SLPM"], "")
            self.assertEqual(rows[0]["plasma_state"], "ON")
            self.assertFalse(log.available)


if __name__ == "__main__":
    unittest.main()
