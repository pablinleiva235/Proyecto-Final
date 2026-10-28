"""Pruebas del registro y verificación del estado seguro del hardware."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from drivers import dio_driver
from logic.shutdown_sequence import ShutdownSequence
from services import hardware as hardware_module
from services import shutdown_log as shutdown_log_module
from services.hardware import Hardware
from tests.mockScripts.mock_hardware import MockHardware


class HardwareShutdownStateTests(unittest.TestCase):
    DIGITAL_OUTPUTS = {
        "OUTPUT_ACTIVE_HIGH": {
            "port": 1,
            "bit": 0,
            "dir": "OUT",
            "active_state": 1,
            "initial_state": 0,
        },
        "OUTPUT_ACTIVE_LOW": {
            "port": 1,
            "bit": 1,
            "dir": "OUT",
            "active_state": 0,
            "initial_state": 1,
        },
        "INPUT_ONLY": {
            "port": 1,
            "bit": 2,
            "dir": "IN",
            "active_state": 1,
            "initial_state": 0,
        },
    }

    def setUp(self):
        self.hardware = Hardware.__new__(Hardware)
        self.hardware.dio_board = 3
        self.hardware.map_to_ul_bit = Mock(return_value=(10, 4))
        self.hardware.analog_write = Mock()

    def _run_shutdown(self, read_side_effect, write_side_effect=None):
        results = []
        with (
            patch.object(hardware_module, "DIGITALSIGNALS", self.DIGITAL_OUTPUTS),
            patch.object(hardware_module, "ANALOG_OUTPUTS", {"MFC1_SETPOINT": {}}),
            patch.object(
                hardware_module.dio,
                "write_bit",
                side_effect=write_side_effect,
            ) as write_bit,
            patch.object(
                hardware_module.dio,
                "read_bit",
                side_effect=read_side_effect,
            ) as read_bit,
        ):
            errors = self.hardware.shutdown_state(
                result_callback=lambda name, success, detail: results.append(
                    (name, success, detail)
                )
            )
        return errors, results, write_bit, read_bit

    def test_logs_sent_levels_and_matching_readbacks(self):
        errors, results, write_bit, read_bit = self._run_shutdown([0, 1])

        self.assertEqual(errors, [])
        self.assertEqual(write_bit.call_count, 2)
        self.assertEqual(read_bit.call_count, 2)
        digital_results = results[:2]
        self.assertTrue(all(success for _, success, _ in digital_results))
        self.assertIn("nivel enviado=0", digital_results[0][2])
        self.assertIn("lectura de pin=0", digital_results[0][2])
        self.assertIn("estado lógico solicitado=inactivo", digital_results[0][2])
        self.assertIn("nivel enviado=1", digital_results[1][2])
        self.assertIn("lectura de pin=1", digital_results[1][2])
        analog_result = results[2]
        self.assertEqual(analog_result[:2], ("MFC1_SETPOINT", True))
        self.assertIn("setpoint enviado: 0.0 V", analog_result[2])
        self.assertIn("lectura física=no disponible", analog_result[2])
        self.hardware.analog_write.assert_called_once_with("MFC1_SETPOINT", 0.0)

    def test_reports_readback_mismatch_as_error(self):
        errors, results, _, _ = self._run_shutdown([1, 1])

        self.assertTrue(any("OUTPUT_ACTIVE_HIGH" in error for error in errors))
        self.assertFalse(results[0][1])
        self.assertIn("lectura de pin=1", results[0][2])
        self.assertIn("verificación ERROR", results[0][2])

    def test_reports_readback_failure_without_skipping_other_outputs(self):
        errors, results, write_bit, read_bit = self._run_shutdown(
            [RuntimeError("read failure"), 1]
        )

        self.assertTrue(any("lectura de verificación fallida" in error for error in errors))
        self.assertEqual(write_bit.call_count, 2)
        self.assertEqual(read_bit.call_count, 2)
        self.assertFalse(results[0][1])
        self.assertIn("lectura de pin=ERROR", results[0][2])
        self.assertTrue(results[1][1])

    def test_reports_write_failure_without_attempting_readback(self):
        errors, results, write_bit, read_bit = self._run_shutdown(
            [1],
            [RuntimeError("write failure"), None],
        )

        self.assertTrue(any("escritura fallida" in error for error in errors))
        self.assertEqual(write_bit.call_count, 2)
        self.assertEqual(read_bit.call_count, 1)
        self.assertFalse(results[0][1])
        self.assertIn("nivel enviado=0", results[0][2])
        self.assertIn("escritura ERROR", results[0][2])

    def test_digital_driver_raises_when_vendor_read_fails(self):
        with patch.object(dio_driver.cbw, "cbDBitIn", return_value=7):
            with self.assertRaisesRegex(Exception, "cbDBitIn error 7"):
                dio_driver.read_bit(0, 10, 4)


class MockHardwareShutdownStateTests(unittest.TestCase):
    def test_logs_simulated_readback_and_analog_feedback_limit(self):
        hardware = MockHardware()
        results = []

        errors = hardware.shutdown_state(
            result_callback=lambda name, success, detail: results.append(
                (name, success, detail)
            )
        )

        self.assertEqual(errors, [])
        digital_outputs = [
            name
            for name, signal in hardware_module.DIGITALSIGNALS.items()
            if signal["dir"] == "OUT"
        ]
        logged_names = [name for name, _, _ in results]
        for name in digital_outputs:
            self.assertIn(name, logged_names)
            result = results[logged_names.index(name)]
            self.assertTrue(result[1])
            self.assertIn("nivel enviado=", result[2])
            self.assertIn("lectura simulada=", result[2])

        analog_results = [result for result in results if result[0].endswith("_SETPOINT")]
        self.assertEqual(len(analog_results), 4)
        self.assertTrue(all("0.0 V" in result[2] for result in analog_results))
        self.assertTrue(
            all("lectura física=no disponible" in result[2] for result in analog_results)
        )

    def test_shutdown_sequence_writes_signal_values_to_log(self):
        class NoOpSequence:
            def shutdown(self):
                pass

        with TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "shutdown_1.log"
            with patch.object(shutdown_log_module, "SHUTDOWN_LOG_PATH", log_path):
                sequence = ShutdownSequence(
                    hardware=MockHardware(),
                    soft_vacuum_sequence=NoOpSequence(),
                    main_vacuum_sequence=NoOpSequence(),
                    vent_sequence=NoOpSequence(),
                )
                sequence.start()

            log_content = log_path.read_text(encoding="utf-8")

        self.assertIn("PURGE_VALVE_CONTROL: OK | nivel enviado=0; lectura simulada=0", log_content)
        self.assertIn("MFC1_SETPOINT: OK | setpoint enviado: 0.0 V", log_content)
        self.assertIn("lectura física=no disponible", log_content)
        self.assertIn("Apagado finalizado sin fallas", log_content)

    def test_shutdown_log_rotates_and_continues_after_reopening(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            configured_path = directory / "shutdown_1.log"
            with patch.object(shutdown_log_module, "SHUTDOWN_LOG_PATH", configured_path):
                first = shutdown_log_module.ShutdownLog()
                self.assertEqual(first.path, directory / "shutdown_1.log")
                first.log("primer apagado")
                first.close()

                second = shutdown_log_module.ShutdownLog()
                self.assertEqual(second.path, directory / "shutdown_2.log")
                second.log("segundo apagado")
                second.close()

                after_restart = shutdown_log_module.ShutdownLog()
                self.assertEqual(after_restart.path, directory / "shutdown_3.log")
                after_restart.close()

    def test_shutdown_log_wraps_after_one_hundred(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "shutdown_100.log").write_text("log anterior", encoding="utf-8")
            with patch.object(
                shutdown_log_module, "SHUTDOWN_LOG_PATH", directory / "shutdown_1.log"
            ):
                log = shutdown_log_module.ShutdownLog()
                self.assertEqual(log.path, directory / "shutdown_1.log")
                log.log("reutiliza el primer archivo")
                log.close()
            self.assertIn("reutiliza el primer archivo", (directory / "shutdown_1.log").read_text(encoding="utf-8"))

    def test_shutdown_log_write_error_reports_selected_path(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            blocker = directory / "not_a_directory"
            blocker.write_text("archivo", encoding="utf-8")
            configured_path = blocker / "shutdown_1.log"
            with patch.object(shutdown_log_module, "SHUTDOWN_LOG_PATH", configured_path):
                log = shutdown_log_module.ShutdownLog()
            self.assertEqual(log.path, configured_path)
            self.assertTrue(any(str(configured_path) in error for error in log.errors))


if __name__ == "__main__":
    unittest.main()
