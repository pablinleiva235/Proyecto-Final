from PyQt5.QtCore import QObject, QEvent, Qt


class SimulationController(QObject):

    def __init__(self, hardware, parent=None):
        super().__init__(parent)

        self._hardware = hardware

    def eventFilter(self, obj, event):

        if event.type() == QEvent.KeyPress:

            if event.key() == Qt.Key_P:

                current_state = self._hardware.digital_read(
                    "POWER_ON_SWITCH"
                )

                new_state = not current_state

                self._hardware.set_input_state(
                    "POWER_ON_SWITCH",
                    new_state,
                )

                print(
                    "[Simulation] POWER_ON_SWITCH -> "
                    f"{new_state}"
                )

                return True

        return super().eventFilter(obj, event)