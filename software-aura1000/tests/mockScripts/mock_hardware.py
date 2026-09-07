"""
Simulación del hardware utilizada para desarrollo de la GUI.

MockHardware implementa la misma interfaz pública utilizada por los
controladores, pero no accede a drivers ni placas físicas.
"""


class MockHardware:

    def __init__(self):
        self._digital_states = {}

        print(
            "[MockHardware] Hardware simulado inicializado."
        )

    def digital_read(self, signal_name):
        """Simula la lectura de una señal digital."""

        state = self._digital_states.get(
            signal_name,
            False,
        )

        print(
            f"[MockHardware] READ "
            f"{signal_name} -> {state}"
        )

        return state

    def digital_set(
        self,
        signal_name,
        active,
    ):
        """Simula la escritura de una salida digital."""

        self._digital_states[
            signal_name
        ] = bool(active)

        print(
            f"[MockHardware] WRITE "
            f"{signal_name} -> {bool(active)}"
        )

    def set_input_state(self, signal_name, active):
        """
        Simula un cambio físico en una señal de entrada digital.

        Utilizado únicamente durante pruebas con MockHardware.
        """
        self._digital_states[signal_name] = bool(active)
        print(
            f"[MockHardware] INPUT "
            f"{signal_name} -> {bool(active)}"
        )

    def initialize_AD(self):
        """Simula la inicialización de la placa analógica."""

        print(
            "[MockHardware] initialize_AD()"
        )