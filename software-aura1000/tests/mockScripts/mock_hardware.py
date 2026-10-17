"""
Simulación del hardware utilizada para desarrollo de la GUI.

MockHardware implementa la misma interfaz pública utilizada por los
controladores, pero no accede a drivers ni placas físicas.
"""

from config.digital_signals import DIGITALSIGNALS


class MockHardware:

    def __init__(self):
        self._digital_states = {
            name: (signal["initial_state"] == signal["active_state"])
            for name, signal in DIGITALSIGNALS.items()
        }
        # SYS_POWER debe permanecer inactiva al iniciar la simulación; de lo
        # contrario, el valor inicial configurado como activo solicita apagar.
        self._digital_states["SYS_POWER"] = False
        self._analog_values = {
            "MFC1_FLOW": 0.0,
            "MFC2_FLOW": 0.0,
            "MFC3_FLOW": 0.0,
            "MFC4_FLOW": 0.0,
            "BARATRON": 0.0,
            "EOP": 0.0,
            "CHAMBER_TEMP": 20.0,
        }
        self._analog_outputs = {}
        self.initialize_DIO()
        self.initialize_AD()

        print(
            "[MockHardware] Hardware simulado inicializado."
        )

    def digital_read(self, signal_name):
        """Simula la lectura de una señal digital."""
        DIGITALSIGNALS[signal_name]
        state = self._digital_states[signal_name]

        # print(
        #     f"[MockHardware] READ "
        #     f"{signal_name} -> {state}"
        # )

        return state

    def digital_set(
        self,
        signal_name,
        active,
    ):
        """Simula la escritura de una salida digital."""

        signal = DIGITALSIGNALS[signal_name]
        if signal["dir"] != "OUT":
            raise ValueError(f"La señal {signal_name} no está configurada como salida.")

        self._digital_states[
            signal_name
        ] = bool(active)

        print(
            f"[MockHardware] WRITE "
            f"{signal_name} -> {bool(active)}"
        )

    def initialize_DIO(self):
        """Inicializa el estado lógico de salidas como el hardware real."""
        self.digital_safe_state()

    def digital_safe_state(self):
        """Lleva las salidas a los estados lógicos iniciales configurados."""
        for signal_name, signal in DIGITALSIGNALS.items():
            if signal["dir"] == "OUT":
                self._digital_states[signal_name] = (
                    signal["initial_state"] == signal["active_state"]
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

        self.analog_safe_state()

    def analog_safe_state(self):
        for signal_name in ("MFC1_SETPOINT", "MFC2_SETPOINT", "MFC3_SETPOINT", "MFC4_SETPOINT"):
            self.analog_write(signal_name, 0.0)

    def analog_read(self, signal_name):
        if signal_name not in self._analog_values:
            raise KeyError(f"Señal analógica no configurada: {signal_name}")
        return self._analog_values[signal_name]

    def analog_read_temperature(self, signal_name):
        if signal_name != "CHAMBER_TEMP":
            raise KeyError(f"Termocupla no configurada: {signal_name}")
        return self._analog_values[signal_name]

    def analog_write(self, signal_name, voltage):
        from config.analog_signals import ANALOG_OUTPUTS
        if signal_name not in ANALOG_OUTPUTS:
            raise KeyError(f"Salida analógica no configurada: {signal_name}")
        config = ANALOG_OUTPUTS[signal_name]
        value = float(voltage)
        if not config["min_voltage"] <= value <= config["max_voltage"]:
            raise ValueError(f"Tensión fuera de rango para {signal_name}")
        self._analog_outputs[signal_name] = value

    def set_analog_value(self, signal_name, value):
        if signal_name not in self._analog_values:
            raise KeyError(f"Señal analógica no configurada: {signal_name}")
        self._analog_values[signal_name] = float(value)

    def get_analog_output(self, signal_name):
        return self._analog_outputs.get(signal_name, 0.0)


    def shutdown_state(self, result_callback=None):
        """
        Simula el estado seguro global del hardware.

        Lleva todas las salidas digitales al estado lógico
        correspondiente a su initial_state.
        """
        print(
            "[MockHardware] shutdown_state()"
        )

        errors = []
        for signal_name, signal in DIGITALSIGNALS.items():
            if signal["dir"] != "OUT":
                continue
            try:
                self._digital_states[signal_name] = (
                    signal["initial_state"] == signal["active_state"]
                )
                if result_callback:
                    result_callback(
                        signal_name, True,
                        f"estado lógico inicial solicitado: {'activo' if self._digital_states[signal_name] else 'inactivo'}",
                    )
            except Exception as error:
                errors.append(f"{signal_name}: {error}")
                if result_callback:
                    result_callback(signal_name, False, str(error))

        from config.analog_signals import ANALOG_OUTPUTS
        for signal_name in ANALOG_OUTPUTS:
            try:
                self.analog_write(signal_name, 0.0)
                if result_callback:
                    result_callback(signal_name, True, "setpoint solicitado: 0.0 V")
            except Exception as error:
                errors.append(f"{signal_name}: {error}")
                if result_callback:
                    result_callback(signal_name, False, str(error))
        return errors
