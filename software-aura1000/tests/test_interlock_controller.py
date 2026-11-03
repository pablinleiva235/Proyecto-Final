import unittest
from types import SimpleNamespace

from controllers.interlock_controller import InterlockController
from logic.door_sequence import DoorState
from logic.main_vacuum_sequence import MainVacuumState
from logic.soft_vacuum_sequence import SoftVacuumState
from logic.vent_sequence import VentState


class InterlockControllerVentTests(unittest.TestCase):
    def setUp(self):
        self.process_states = {
            "lamps13": False,
            "lamp2": False,
            "plasma": False,
        }
        self.door = SimpleNamespace(state=DoorState.CLOSED)
        self.soft_vacuum = SimpleNamespace(state=SoftVacuumState.IDLE)
        self.main_vacuum = SimpleNamespace(state=MainVacuumState.IDLE)
        self.vent = SimpleNamespace(state=VentState.IDLE)
        self.interlocks = InterlockController(
            door_sequence=self.door,
            soft_vacuum_sequence=self.soft_vacuum,
            main_vacuum_sequence=self.main_vacuum,
            vent_sequence=self.vent,
            driver_enabled=lambda: True,
            processes_inactive=lambda: not any(self.process_states.values()),
        )

    def test_can_start_vent_when_lamps_and_plasma_are_inactive(self):
        self.assertTrue(self.interlocks.can_start_vent())
        self.assertTrue(self.interlocks.is_vent_control_enabled())

    def test_cannot_start_vent_when_any_lamp_or_plasma_is_active(self):
        for process in self.process_states:
            with self.subTest(process=process):
                self.process_states[process] = True
                self.assertFalse(self.interlocks.can_start_vent())
                self.assertFalse(self.interlocks.is_vent_control_enabled())
                self.process_states[process] = False

    def test_active_vent_can_still_be_stopped_while_process_is_active(self):
        self.vent.state = VentState.RUNNING
        self.process_states["plasma"] = True

        self.assertTrue(self.interlocks.is_vent_control_enabled())


if __name__ == "__main__":
    unittest.main()
