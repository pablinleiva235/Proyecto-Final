"""
Simulación del hardware utilizada para desarrollo de la GUI.

MockHardware implementa la misma interfaz pública utilizada por los
controladores, pero no accede a drivers ni placas físicas.
"""

from config.digital_signals import DIGITALSIGNALS


class MockHardware:

    _THROTTLE_MAX_STEPS = 1400
    _TEMPERATURE_STEP_C = 5.0

    _BARATRON_PRESSURES = {
        "ATM_SWITCH": 10.0,
        "SOFT_START_CONTROL": 0.1,
        "MAIN_VACUUM_CONTROL": 0.06,
    }

    def __init__(self):
        self._throttle_position_steps = 0
        self._digital_states = {
            name: (signal["initial_state"] == signal["active_state"])
            for name, signal in DIGITALSIGNALS.items()
        }
        # SYS_POWER debe permanecer inactiva al iniciar la simulación; de lo
        # contrario, el valor inicial configurado como activo solicita apagar.
        self._digital_states["SYS_POWER"] = False
        self._update_simulated_throttle_limits()
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

    def digital_read(self, signal_name):
        """Devuelve el estado digital actual sin iniciar sondeos ni mutarlo."""
        if signal_name not in DIGITALSIGNALS:
            raise KeyError(f"Señal digital no configurada: {signal_name}")
        return self._digital_states[signal_name]

    def digital_set(
        self,
        signal_name,
        active,
    ):
        """Simula la escritura de una salida digital."""

        signal = DIGITALSIGNALS[signal_name]
        if signal["dir"] != "OUT":
            raise ValueError(f"La señal {signal_name} no está configurada como salida.")

        active = bool(active)
        if signal_name == "STEPPER_STEP" and active and not self._digital_states[signal_name]:
            self._advance_simulated_throttle()
        self._digital_states[signal_name] = active
        self._update_simulated_pressure(signal_name, active)

    def _advance_simulated_throttle(self):
        """Cuenta un paso en el flanco ascendente de STEPPER_STEP."""
        direction = self._digital_states["STEPPER_DIR"]
        if direction:
            self._throttle_position_steps = min(
                self._THROTTLE_MAX_STEPS,
                self._throttle_position_steps + 1,
            )
        else:
            self._throttle_position_steps = max(
                0,
                self._throttle_position_steps - 1,
            )
        self._update_simulated_throttle_limits()

    def _update_simulated_throttle_limits(self):
        """Actualiza los finales de carrera simulados según la posición."""
        self._digital_states["THROTTLE_OPEN"] = self._throttle_position_steps == 0
        self._digital_states["THROTTLE_CLOSED"] = (
            self._throttle_position_steps == self._THROTTLE_MAX_STEPS
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
        signal = DIGITALSIGNALS.get(signal_name)
        if signal is None:
            raise KeyError(f"Señal digital no configurada: {signal_name}")
        if signal["dir"] != "IN":
            raise ValueError(f"La señal {signal_name} no está configurada como entrada.")
        active = bool(active)
        self._digital_states[signal_name] = active
        self._update_simulated_pressure(signal_name, active)

    def _update_simulated_pressure(self, signal_name, active):
        """Update BARATRON when ATM or a simulated vacuum pump is activated."""
        if not active or signal_name not in self._BARATRON_PRESSURES:
            return

        self._analog_values["BARATRON"] = self._BARATRON_PRESSURES[signal_name]
        if signal_name in ("SOFT_START_CONTROL", "MAIN_VACUUM_CONTROL"):
            self._digital_states["ATM_SWITCH"] = False

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

    def adjust_temperature(self, direction):
        """Ajusta la temperatura simulada en un paso de 5 °C."""
        direction = float(direction)
        if direction not in (-1.0, 1.0):
            raise ValueError("La dirección debe ser -1 o 1.")
        self._analog_values["CHAMBER_TEMP"] += direction * self._TEMPERATURE_STEP_C

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
        from config.analog_signals import ANALOG_OUTPUTS
        if signal_name not in ANALOG_OUTPUTS:
            raise KeyError(f"Salida analógica no configurada: {signal_name}")
        return self._analog_outputs[signal_name]


    def shutdown_state(self, result_callback=None):
        """
        Simula el estado seguro global del hardware.

        Lleva todas las salidas digitales al estado lógico
        correspondiente a su initial_state.
        """
        errors = []
        for signal_name, signal in DIGITALSIGNALS.items():
            if signal["dir"] != "OUT":
                continue
            try:
                self._digital_states[signal_name] = (
                    signal["initial_state"] == signal["active_state"]
                )
                requested_value = int(signal["initial_state"])
                readback_value = int(
                    self._digital_states[signal_name]
                    == bool(signal["active_state"])
                )
                logical_initial = requested_value == signal["active_state"]
                logical_readback = readback_value == signal["active_state"]
                if result_callback:
                    result_callback(
                        signal_name,
                        readback_value == requested_value,
                        f"nivel enviado={requested_value}; lectura simulada={readback_value}; "
                        f"estado lógico solicitado={'activo' if logical_initial else 'inactivo'}; "
                        f"estado lógico leído={'activo' if logical_readback else 'inactivo'}; "
                        f"verificación {'OK' if readback_value == requested_value else 'ERROR'}",
                    )
                if readback_value != requested_value:
                    errors.append(
                        f"{signal_name}: discrepancia entre nivel enviado "
                        f"({requested_value}) y lectura simulada ({readback_value})"
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
                    result_callback(
                        signal_name,
                        True,
                        "setpoint enviado: 0.0 V; lectura física=no disponible "
                        "(sin realimentación configurada)",
                    )
            except Exception as error:
                errors.append(f"{signal_name}: {error}")
                if result_callback:
                    result_callback(
                        signal_name,
                        False,
                        f"setpoint solicitado: 0.0 V; escritura ERROR: {error}",
                    )
        return errors
