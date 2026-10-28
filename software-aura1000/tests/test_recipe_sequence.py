import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PyQt5.QtWidgets import QApplication

from logic.door_sequence import DoorState
from logic.main_vacuum_sequence import MainVacuumState
from logic.recipe_sequence import RecipeSequence, RecipeState
from logic.soft_vacuum_sequence import SoftVacuumState
from logic.vent_sequence import VentState
from gui.maintainer_screen import MaintainerScreen
from services.recipe_service import Recipe
from services.recipe_log import RecipeDataLog, RecipeLog


class Door:
    def __init__(self):
        self.state = DoorState.CLOSED

    def open(self):
        self.state = DoorState.OPEN

    def close(self):
        self.state = DoorState.CLOSED


class Vacuum:
    def __init__(self, idle, running):
        self.state = idle
        self._idle = idle
        self._running = running

    def start(self):
        self.state = self._running

    def stop(self):
        self.state = self._idle


class Vent:
    def __init__(self):
        self.state = VentState.IDLE
        self.start_calls = 0

    def start(self):
        self.start_calls += 1
        self.state = VentState.RUNNING

    def stop(self):
        self.state = VentState.IDLE


class Mfc:
    def __init__(self):
        self.calls = []

    def set_flow(self, name, value):
        self.calls.append(("flow", name, value))

    def set_valve(self, name, opened):
        self.calls.append(("valve", name, opened))

    def shutdown(self):
        self.calls.append(("shutdown",))


class Pressure:
    is_active = False

    def start(self, value):
        self.target = value
        self.is_active = True

    def stop(self, return_to_rest=True):
        self.is_active = False


class Temperature:
    is_active = False

    def start(self, value):
        self.target = value
        self.is_active = True

    def stop(self):
        self.is_active = False


class Process:
    def __init__(self):
        self.plasma_active = False

    def set_plasma(self, enabled):
        self.plasma_active = enabled

    def stop_all(self):
        self.plasma_active = False


class RecipeSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.log_path = Path(self.tempdir.name) / "recipe.log"
        self.data_log_path = Path(self.tempdir.name) / "recipe_data.csv"
        self.door = Door()
        self.soft = Vacuum(SoftVacuumState.IDLE, SoftVacuumState.RUNNING)
        self.main = Vacuum(MainVacuumState.IDLE, MainVacuumState.RUNNING)
        self.vent = Vent()
        self.mfc = Mfc()
        self.pressure = Pressure()
        self.temperature = Temperature()
        self.process = Process()
        self.digital_states = {
            "DOOR_OPEN": False,
            "DOOR_CLOSE": True,
            "DRIVER_ENABLE": True,
        }
        self.digital_set_calls = []
        self.sequence = RecipeSequence(
            self.door, self.soft, self.main, self.vent, self.mfc,
            self.pressure, self.temperature, self.process,
            digital_state_getter=lambda name: self.digital_states.get(name),
            recipe_log_factory=lambda: RecipeLog(self.log_path),
            recipe_data_log_factory=lambda: RecipeDataLog(self.data_log_path),
            digital_state_setter=self._digital_set,
            digital_hardware_reader=lambda name: self.digital_states.get(name),
        )
        self.recipe = Recipe("test", "test", 2, 0.2, 1, 1.5, 150)

    def _digital_set(self, name, active):
        self.digital_set_calls.append((name, active))
        self.digital_states[name] = active

    def _finish_with_door_open(self):
        self.sequence.vent_completed()
        self.assertEqual(self.sequence.state, RecipeState.WAITING_FOR_WAFER_REMOVAL)
        self.sequence.confirm_wafer_removed(False)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_recipe_waits_for_base_pressure_and_eop_below_two_volts(self):
        self.sequence.start(self.recipe)
        self.sequence.confirm_wafer_loaded(True)
        self.assertEqual(self.sequence.state, RecipeState.PUMPING_TO_BASE)

        self.sequence.update_analog("BARATRON", 1.0)
        self.assertEqual(self.sequence.state, RecipeState.CONTROLLING_PRESSURE)
        self.sequence.pressure_reached(1.5)
        self.assertEqual(self.temperature.target, 150)
        self.sequence.temperature_reached(150)
        self.sequence.update_analog("EOP", 2.0)
        self.assertEqual(self.sequence.state, RecipeState.RUNNING_PLASMA)
        self.sequence.update_analog("EOP", 1.99)

        self.assertEqual(self.sequence.state, RecipeState.VENTING)
        self.assertFalse(self.sequence._rf_timer.isActive())
        self.assertFalse(self.process.plasma_active)
        self.assertEqual(self.main.state, MainVacuumState.IDLE)
        self.assertEqual(self.soft.state, SoftVacuumState.IDLE)
        self.sequence.vent_completed()
        self.assertEqual(self.door.state, DoorState.OPEN)
        self.assertEqual(self.sequence.state, RecipeState.WAITING_FOR_WAFER_REMOVAL)
        self.assertTrue(self.sequence.is_active)
        self.digital_states.update({"DOOR_OPEN": True, "DOOR_CLOSE": False})
        self.sequence.confirm_wafer_removed(True)
        self.assertEqual(self.door.state, DoorState.CLOSED)
        self.assertEqual(self.sequence.state, RecipeState.VERIFYING_DOOR_CLOSED_AFTER_RECIPE)
        self.digital_states.update({"DOOR_OPEN": False, "DOOR_CLOSE": True})
        self.sequence.digital_value("DOOR_CLOSE", True)
        self.assertEqual(self.sequence.state, RecipeState.COMPLETED)
        contents = self.log_path.read_text(encoding="utf-8")
        door_open = next(line for line in contents.splitlines() if "ACCION: Abrir puerta para cargar" in line)
        self.assertIn("DOOR_CLOSE_CMD=INACTIVO", door_open)
        self.assertIn("DOOR_OPEN_CMD=ACTIVO", door_open)
        door_close = next(line for line in contents.splitlines() if "ACCION: Cerrar puerta después" in line)
        self.assertIn("DOOR_OPEN_CMD=INACTIVO", door_close)
        self.assertIn("DOOR_CLOSE_CMD=ACTIVO", door_close)
        self.assertIn("EOP=1.99 V", contents)
        self.assertIn("ACCION: Desactivar RF/plasma", contents)
        rf_shutdown = next(
            line for line in contents.splitlines()
            if "ACCION: Desactivar RF/plasma" in line
        )
        self.assertIn("EOP=1.99 V", rf_shutdown)
        self.assertIn("FIN DE RECETA | resultado=OK", contents)
        self.assertIn("NO DISPONIBLE", contents)
        self.assertTrue(self.sequence.log_saved)
        self.assertTrue(self.sequence.data_log_saved)
        csv_text = self.data_log_path.read_text(encoding="utf-8")
        self.assertIn(",BARATRON,1,Torr", csv_text)

    def test_rf_time_limit_runs_safe_shutdown(self):
        self.sequence.start(self.recipe)
        self.sequence.confirm_wafer_loaded(True)
        self.sequence.update_analog("BARATRON", 1.0)
        self.sequence.pressure_reached(1.5)
        self.sequence.temperature_reached(150)

        self.assertTrue(self.sequence._rf_timer.isActive())
        self.sequence._rf_time_limit_reached()

        self.assertFalse(self.process.plasma_active)
        self.assertEqual(self.sequence.state, RecipeState.VENTING)
        self.assertFalse(self.sequence._rf_timer.isActive())
        self._finish_with_door_open()
        contents = self.log_path.read_text(encoding="utf-8")
        self.assertIn("tiempo_maximo_RF=90 s", contents)
        self.assertIn("Tiempo máximo de RF alcanzado (90 s)", contents)

    def test_process_data_csv_records_pressure_and_temperature_during_recipe(self):
        self.sequence.start(self.recipe)
        self.sequence.update_analog("BARATRON", 0.7)
        self.sequence.update_analog("CHAMBER_TEMP", 143.25)
        rows = self.data_log_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(rows[0], "timestamp,señal,valor,unidad")
        self.assertTrue(any(",BARATRON,0.7,Torr" in row for row in rows))
        self.assertTrue(any(",CHAMBER_TEMP,143.25,°C" in row for row in rows))
        self.sequence.confirm_wafer_loaded(False)

    def test_data_log_write_failure_runs_safe_shutdown(self):
        class FailingDataLog:
            def __init__(inner_self):
                inner_self.path = self.data_log_path
                inner_self.error = None
                inner_self.available = True

            def record(inner_self, *_args):
                inner_self.error = "disco lleno"
                inner_self.available = False
                return False

            def close(inner_self):
                pass

        self.sequence._recipe_data_log_factory = FailingDataLog
        finished = []
        self.sequence.finished.connect(lambda success, message: finished.append((success, message)))
        self.sequence.start(self.recipe)
        self.sequence.confirm_wafer_loaded(True)
        self.sequence.update_analog("BARATRON", 0.5)

        self.assertEqual(self.sequence.state, RecipeState.VENTING)
        self.assertEqual(self.main.state, MainVacuumState.IDLE)
        self._finish_with_door_open()
        self.assertEqual(self.sequence.state, RecipeState.ERROR)
        self.assertFalse(finished[0][0])
        self.assertIn(str(self.data_log_path), finished[0][1])

    def test_data_log_creation_failure_blocks_recipe_start(self):
        class UnavailableDataLog:
            path = self.data_log_path
            available = False
            error = "acceso denegado"

            def close(self):
                pass

        results = []
        self.sequence._recipe_data_log_factory = UnavailableDataLog
        self.sequence.finished.connect(lambda success, message: results.append((success, message)))

        self.assertFalse(self.sequence.start(self.recipe))
        self.assertEqual(self.sequence.state, RecipeState.ERROR)
        self.assertEqual(self.door.state, DoorState.CLOSED)
        self.assertFalse(results[0][0])
        self.assertIn(str(self.data_log_path), results[0][1])

    def test_stop_during_process_turns_modules_off_and_starts_vent(self):
        self.sequence.start(self.recipe)
        self.sequence.confirm_wafer_loaded(True)
        self.sequence.update_analog("BARATRON", 0.5)
        self.sequence.pressure_reached(1.5)
        self.sequence.temperature_reached(150)
        self.sequence.stop()

        self.assertFalse(self.process.plasma_active)
        self.assertFalse(self.temperature.is_active)
        self.assertFalse(self.pressure.is_active)
        self.assertEqual(self.vent.state, VentState.RUNNING)
        self._finish_with_door_open()
        self.assertEqual(self.sequence.state, RecipeState.COMPLETED)

    def test_manual_maintenance_controls_lock_and_restore(self):
        screen = MaintainerScreen()
        screen.set_sequence_enabled("door", True)
        screen.set_module_controls_enabled(True)
        screen.set_pressure_control_state("regulando")
        screen.set_temperature_control_state("manteniendo")
        screen.set_manual_controls_locked(True)
        self.assertFalse(screen.door_sequence_button.isEnabled())
        self.assertFalse(screen.back_button.isEnabled())
        self.assertFalse(screen.pressure_stop_button.isEnabled())
        self.assertFalse(screen.temperature_stop_button.isEnabled())
        self.assertTrue(all(not widget.isEnabled() for widget in screen._output_widgets))

        screen.set_manual_controls_locked(False)
        self.assertTrue(screen.door_sequence_button.isEnabled())
        self.assertTrue(screen.back_button.isEnabled())

    def test_baratron_failure_runs_safe_shutdown_and_finishes_as_error(self):
        results = []
        self.sequence.finished.connect(lambda success, message: results.append((success, message)))
        self.sequence.start(self.recipe)
        self.sequence.confirm_wafer_loaded(True)
        self.sequence.analog_error("BARATRON", "sensor desconectado")

        self.assertEqual(self.sequence.state, RecipeState.VENTING)
        self.assertFalse(self.process.plasma_active)
        self._finish_with_door_open()
        self.assertEqual(self.sequence.state, RecipeState.ERROR)
        self.assertFalse(results[0][0])
        self.assertIn("sensor desconectado", results[0][1])

    def test_log_write_failure_stops_progress_and_runs_safe_shutdown(self):
        class FailingLog:
            def __init__(inner_self):
                inner_self.path = self.log_path
                inner_self.error = None
                inner_self.available = True
                inner_self.closed = False

            def record(inner_self, event, _readings, outputs=None):
                if event.startswith("ACCION: Activar Main Vacuum"):
                    inner_self.error = "disco lleno"
                    inner_self.available = False
                    return False
                return True

            def close(inner_self):
                inner_self.closed = True

        self.sequence._recipe_log_factory = FailingLog
        finished = []
        self.sequence.finished.connect(lambda success, message: finished.append((success, message)))
        self.sequence.start(self.recipe)
        self.sequence.confirm_wafer_loaded(True)

        self.assertEqual(self.main.state, MainVacuumState.IDLE)
        self.assertEqual(self.soft.state, SoftVacuumState.IDLE)
        self.assertEqual(self.vent.state, VentState.RUNNING)
        self._finish_with_door_open()
        self.assertEqual(self.sequence.state, RecipeState.ERROR)
        self.assertFalse(finished[0][0])
        self.assertFalse(self.sequence.log_saved)
        self.assertIn(str(self.log_path), finished[0][1])

    def test_driver_enable_is_set_only_when_inactive_and_verified(self):
        self.digital_states["DRIVER_ENABLE"] = False

        self.assertTrue(self.sequence.start(self.recipe))

        self.assertEqual(self.digital_set_calls, [("DRIVER_ENABLE", True)])
        self.assertTrue(self.digital_states["DRIVER_ENABLE"])
        self.assertEqual(self.sequence.state, RecipeState.WAITING_FOR_WAFER)
        self.sequence.confirm_wafer_loaded(False)

    def test_driver_enable_already_active_is_not_written(self):
        self.assertTrue(self.sequence.start(self.recipe))

        self.assertEqual(self.digital_set_calls, [])
        self.sequence.confirm_wafer_loaded(False)

    def test_driver_enable_confirmation_failure_blocks_door_opening(self):
        def fail_to_enable(_name, _active):
            raise RuntimeError("salida desconectada")

        self.digital_states["DRIVER_ENABLE"] = False
        self.sequence._digital_state_setter = fail_to_enable
        results = []
        self.sequence.finished.connect(lambda success, message: results.append((success, message)))

        self.assertFalse(self.sequence.start(self.recipe))

        self.assertEqual(self.door.state, DoorState.CLOSED)
        self.assertEqual(self.sequence.state, RecipeState.ERROR)
        self.assertFalse(results[0][0])
        self.assertIn("DRIVER_ENABLE", results[0][1])

    def test_driver_enable_readback_mismatch_blocks_door_opening(self):
        self.digital_states["DRIVER_ENABLE"] = False
        self.sequence._digital_state_setter = lambda _name, _active: None

        self.assertFalse(self.sequence.start(self.recipe))

        self.assertEqual(self.door.state, DoorState.CLOSED)
        self.assertEqual(self.sequence.state, RecipeState.ERROR)

    def test_stop_while_waiting_for_wafer_removal_does_not_restart_vent(self):
        self.sequence.start(self.recipe)
        self.sequence.confirm_wafer_loaded(True)
        self.sequence.update_analog("BARATRON", 0.5)
        self.sequence.stop()
        vent_starts_before_completion = self.vent.start_calls
        self.sequence.vent_completed()
        self.assertEqual(self.sequence.state, RecipeState.WAITING_FOR_WAFER_REMOVAL)

        self.sequence.stop()

        self.assertEqual(self.vent.start_calls, vent_starts_before_completion)
        self.assertEqual(self.door.state, DoorState.OPEN)
        self.assertEqual(self.sequence.state, RecipeState.COMPLETED)

    def test_recipe_finishes_open_when_user_confirms_wafer_not_removed(self):
        self.sequence.start(self.recipe)
        self.sequence.confirm_wafer_loaded(True)
        self.sequence.update_analog("BARATRON", 0.5)
        self.sequence.stop()
        self.sequence.vent_completed()

        self.sequence.confirm_wafer_removed(False)

        self.assertEqual(self.sequence.state, RecipeState.COMPLETED)
        self.assertEqual(self.door.state, DoorState.OPEN)


if __name__ == "__main__":
    unittest.main()
