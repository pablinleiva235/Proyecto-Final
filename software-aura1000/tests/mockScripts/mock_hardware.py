"""
Implementación simulada de Hardware para pruebas.

MockHardware permite probar SignalController sin utilizar la placa
USB-DIO96H-50 ni cargar las DLL del fabricante.

Implementa únicamente las funciones necesarias para este hito:

- digital_read()
- digital_set()

La escritura posee una demora artificial para simular el tiempo de
comunicación con el hardware.
"""


class MockHardware:
    """Simula el estado lógico de un conjunto de señales digitales."""

    WRITE_DELAY_SECONDS = 1

    def __init__(self):
        self._states = {
            "POWER_ON": False,
            "POWER_ON_SWITCH": False,
            "SYS_POWER": True,
            "DRIVER_ENABLE": False,
        }

        self._outputs = {
            "POWER_ON",
            "DRIVER_ENABLE",
        }

    def digital_read(self, signal_name):
        """Devuelve el estado lógico actual de una señal."""

        if signal_name not in self._states:
            raise KeyError(
                f"La señal '{signal_name}' no existe en MockHardware."
            )

        state = self._states[signal_name]

        print(
            f"[MockHardware] READ  {signal_name}: {state}"
        )

        return state

    def digital_set(
        self,
        signal_name,
        active,
    ):
        """Modifica el estado lógico de una salida simulada.

        Se introduce una demora artificial de un segundo antes de realizar
        el cambio para simular una operación de hardware.
        """

        if signal_name not in self._states:
            raise KeyError(
                f"La señal '{signal_name}' no existe en MockHardware."
            )

        if signal_name not in self._outputs:
            raise ValueError(
                f"La señal '{signal_name}' no es una salida."
            )

        if not isinstance(active, bool):
            raise TypeError(
                "'active' debe ser un valor booleano."
            )

        print(
            f"[MockHardware] WRITE START "
            f"{signal_name}: {active}"
        )

    

        self._states[signal_name] = active

        print(
            f"[MockHardware] WRITE END   "
            f"{signal_name}: {active}"
        )