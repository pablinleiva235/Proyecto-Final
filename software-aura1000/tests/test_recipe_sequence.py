import unittest

from PyQt5.QtWidgets import QApplication

from logic.door_sequence import DoorState
from logic.main_vacuum_sequence import MainVacuumState
from logic.recipe_sequence import RecipeSequence, RecipeState
from logic.soft_vacuum_sequence import SoftVacuumState
from logic.vent_sequence import VentState
from gui.maintainer_screen import MaintainerScreen
from services.recipe_service import Recipe


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

    def start(self):
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

    def stop(self):
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
        self.door = Door()
        self.soft = Vacuum(SoftVacuumState.IDLE, SoftVacuumState.RUNNING)
        self.main = Vacuum(MainVacuumState.IDLE, MainVacuumState.RUNNING)
        self.vent = Vent()
        self.mfc = Mfc()
        self.pressure = Pressure()
        self.temperature = Temperature()
        self.process = Process()
        self.sequence = RecipeSequence(
            self.door, self.soft, self.main, self.vent, self.mfc,
            self.pressure, self.temperature, self.process,
            digital_state_getter=lambda name: name == "DOOR_CLOSE",
        )
        self.recipe = Recipe("test", "test", 2, 0.2, 1, 1.5, 150)

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
        self.assertFalse(self.process.plasma_active)
        self.assertEqual(self.main.state, MainVacuumState.IDLE)
        self.assertEqual(self.soft.state, SoftVacuumState.IDLE)
        self.sequence.vent_completed()
        self.assertEqual(self.door.state, DoorState.OPEN)
        self.assertEqual(self.sequence.state, RecipeState.COMPLETED)

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
        self.sequence.vent_completed()
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
        self.sequence.vent_completed()
        self.assertEqual(self.sequence.state, RecipeState.ERROR)
        self.assertFalse(results[0][0])
        self.assertIn("sensor desconectado", results[0][1])


if __name__ == "__main__":
    unittest.main()
