from PyQt5.QtCore import QObject, QEvent, Qt


class SimulationController(QObject):

    def __init__(self, hardware, parent=None):
        super().__init__(parent)

        self._hardware = hardware

    def eventFilter(self,obj,event):
        if event.type() == QEvent.KeyPress:

            if event.key() == Qt.Key_P:
                self._toggle_input("POWER_ON_SWITCH")
                return True

            if event.key() == Qt.Key_A:
                self._toggle_input("ATM_SWITCH")
                return True

        return super().eventFilter(obj,event)

    def _toggle_input(self,signal_name):
        current_state = self._hardware.digital_read(
            signal_name
        )

        new_state = not current_state

        self._hardware.set_input_state(
            signal_name,
            new_state,
        )

        print(
            "[SimulationController] "
            f"{signal_name} -> {new_state}"
        )