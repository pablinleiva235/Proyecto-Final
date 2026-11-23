"""
Simulación del hardware utilizada para desarrollo de la GUI.

MockHardware implementa la misma interfaz pública utilizada por los
controladores, pero no accede a drivers ni placas físicas.
"""

from config.digital_signals import DIGITALSIGNALS
from PyQt5.QtCore import QTimer


class MockHardware:

    _DEVICE_FAILURE_SIGNALS = {
        "LAMP1_ON_CMD": "LAMP1_FAIL",
        "LAMP2_ON_CMD": "LAMP2_FAIL",
        "LAMP3_ON_CMD": "LAMP3_FAIL",
        "RF_ON_CMD": "PLASMA_FAIL",
    }

    _THROTTLE_MAX_STEPS = 1400
    _TEMPERATURE_MIN_C = 25.0
    _EOP_STEP_V = 1.0
    _EOP_MIN_V = 0.0
    _EOP_MAX_V = 10.0
    _EOP_RAMP_UP_INTERVAL_MS = 500
    _EOP_RAMP_DOWN_INTERVAL_MS = 1000
    _EOP_RAMP_DOWN_STEP_V = 0.5
    _VENT_TO_ATM_DELAY_MS = 500

    _BARATRON_MAX_TORR = 10.0
    _BARATRON_REFERENCE_THROTTLE_STEPS = 400
    _BARATRON_O2_FLOW_PRESSURES = (
        (0.0, 0.83), (1.0, 1.14), (2.0, 1.51), (3.0, 1.86),
        (4.0, 2.23), (5.0, 2.63), (6.0, 3.0),
    )

    def __init__(self):
        self._vent_to_atm_timer = QTimer()
        self._vent_to_atm_timer.setSingleShot(True)
        self._vent_to_atm_timer.setInterval(self._VENT_TO_ATM_DELAY_MS)
        self._vent_to_atm_timer.timeout.connect(self._activate_atm_switch_after_vent)
        self._temperature_timer = QTimer()
        self._temperature_timer.timeout.connect(self._advance_simulated_temperature)
        self._temperature_step_c = 0.0
        self._temperature_min_c = None
        self._eop_timer = QTimer()
        self._eop_timer.setSingleShot(True)
        self._eop_timer.timeout.connect(self._advance_eop_cycle)
        self._eop_phase = None
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
            "EOP": self._EOP_MIN_V,
            "CHAMBER_TEMP": self._TEMPERATURE_MIN_C,
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
        was_active = self._digital_states[signal_name]
        if signal_name == "STEPPER_STEP" and active and not self._digital_states[signal_name]:
            self._advance_simulated_throttle()
        self._digital_states[signal_name] = active
        failure_signal = self._DEVICE_FAILURE_SIGNALS.get(signal_name)
        if failure_signal is not None:
            self._digital_states[failure_signal] = not active
        self._update_simulated_pressure(signal_name, active)

        if signal_name in ("MFC1_OPEN", "MFC2_OPEN"):
            setpoint_name = signal_name.replace("_OPEN", "_SETPOINT")
            self._update_simulated_mfc_flow(
                setpoint_name,
                self._analog_outputs.get(setpoint_name, 0.0),
            )

        if signal_name == "VENT_VALVE_CONTROL":
            if active and not was_active:
                self._vent_to_atm_timer.start()
            elif not active:
                self._vent_to_atm_timer.stop()

        if signal_name in self._DEVICE_FAILURE_SIGNALS:
            if active != was_active:
                self._configure_temperature_simulation()
            if signal_name == "RF_ON_CMD" and active and not was_active:
                self._start_eop_cycle()

    def _activate_atm_switch_after_vent(self):
        """Activa ATM_SWITCH si la válvula sigue abierta tras la demora."""
        if self._digital_states["VENT_VALVE_CONTROL"]:
            self.set_input_state("ATM_SWITCH", True)

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
        self._update_simulated_pressure()

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
        self._vent_to_atm_timer.stop()
        for signal_name, signal in DIGITALSIGNALS.items():
            if signal["dir"] == "OUT":
                self._digital_states[signal_name] = (
                    signal["initial_state"] == signal["active_state"]
                )
        for command_signal, failure_signal in self._DEVICE_FAILURE_SIGNALS.items():
            self._digital_states[failure_signal] = not self._digital_states[command_signal]
        self._configure_temperature_simulation()

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

    def _update_simulated_pressure(self, signal_name=None, active=None):
        """Actualiza BARATRON según ATM o el modelo de caudal y throttle."""
        if signal_name == "ATM_SWITCH" and active:
            self._analog_values["BARATRON"] = self._BARATRON_MAX_TORR
            return

        if signal_name in ("SOFT_START_CONTROL", "MAIN_VACUUM_CONTROL") and active:
            self._digital_states["ATM_SWITCH"] = False

        if self._digital_states["ATM_SWITCH"]:
            self._analog_values["BARATRON"] = self._BARATRON_MAX_TORR
        elif self._vacuum_pump_active():
            self._analog_values["BARATRON"] = self._calculate_simulated_pressure()

    def _vacuum_pump_active(self):
        return any(
            self._digital_states.get(name, False)
            for name in ("SOFT_START_CONTROL", "MAIN_VACUUM_CONTROL")
        )

    def _calculate_simulated_pressure(self):
        o2_flow_voltage = self._analog_values["MFC1_FLOW"]
        o2_flow = o2_flow_voltage / 5.0 * 10.0 * 0.981
        table = self._BARATRON_O2_FLOW_PRESSURES
        for (flow_a, pressure_a), (flow_b, pressure_b) in zip(table, table[1:]):
            if o2_flow <= flow_b:
                ratio = (o2_flow - flow_a) / (flow_b - flow_a)
                base_pressure = pressure_a + ratio * (pressure_b - pressure_a)
                break
        else:
            (flow_a, pressure_a), (flow_b, pressure_b) = table[-2:]
            ratio = (o2_flow - flow_a) / (flow_b - flow_a)
            base_pressure = pressure_a + ratio * (pressure_b - pressure_a)

        pressure = base_pressure * (
            self._throttle_position_steps / self._BARATRON_REFERENCE_THROTTLE_STEPS
        )
        return min(self._BARATRON_MAX_TORR, max(0.0, pressure))

    def _update_simulated_mfc_flow(self, setpoint_name, voltage):
        """Simula caudal solo cuando la válvula del MFC está abierta."""
        mfc_signals = {
            "MFC1_SETPOINT": ("MFC1_FLOW", "MFC1_OPEN"),
            "MFC2_SETPOINT": ("MFC2_FLOW", "MFC2_OPEN"),
        }.get(setpoint_name)
        if mfc_signals is None:
            return
        input_name, valve_name = mfc_signals
        self._analog_values[input_name] = (
            max(0.0, voltage) if self._digital_states[valve_name] else 0.0
        )
        self._update_simulated_pressure()

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

    def _configure_temperature_simulation(self):
        """Selecciona el ritmo térmico a partir de lámparas y RF."""
        if not hasattr(self, "_analog_values"):
            return

        lamps = tuple(
            self._digital_states[name]
            for name in ("LAMP1_ON_CMD", "LAMP2_ON_CMD", "LAMP3_ON_CMD")
        )
        rf_on = self._digital_states["RF_ON_CMD"]

        if all(lamps):
            interval_ms, step_c, minimum_c = 250, 5.0, None
        elif lamps[0] or lamps[2]:
            interval_ms, step_c, minimum_c = 1000, 5.0, None
        elif lamps[1]:
            interval_ms, step_c, minimum_c = 1000, 1.0, None
        elif rf_on:
            interval_ms, step_c, minimum_c = 1000, -0.5, None
        else:
            interval_ms, step_c, minimum_c = 500, -10.0, self._TEMPERATURE_MIN_C

        self._temperature_step_c = step_c
        self._temperature_min_c = minimum_c
        if minimum_c is not None and self._analog_values["CHAMBER_TEMP"] <= minimum_c:
            self._temperature_timer.stop()
            return
        self._temperature_timer.start(interval_ms)

    def _advance_simulated_temperature(self):
        temperature = self._analog_values["CHAMBER_TEMP"] + self._temperature_step_c
        if self._temperature_min_c is not None:
            temperature = max(self._temperature_min_c, temperature)
        self._analog_values["CHAMBER_TEMP"] = temperature
        if self._temperature_min_c is not None and temperature <= self._temperature_min_c:
            self._temperature_timer.stop()

    def adjust_eop(self, direction):
        """Ajusta el EOP simulado en un paso de 1 V, limitado a 0–10 V."""
        direction = float(direction)
        if direction not in (-1.0, 1.0):
            raise ValueError("La dirección debe ser -1 o 1.")
        self._analog_values["EOP"] = min(
            self._EOP_MAX_V,
            max(
                self._EOP_MIN_V,
                self._analog_values["EOP"] + direction * self._EOP_STEP_V,
            ),
        )

    def _start_eop_cycle(self):
        """Inicia una rampa EOP si no hay otro ciclo en curso."""
        if self._eop_phase is not None:
            return
        self._analog_values["EOP"] = self._EOP_MIN_V
        self._eop_phase = "rising"
        self._eop_timer.start(self._EOP_RAMP_UP_INTERVAL_MS)

    def _advance_eop_cycle(self):
        """Avanza un paso de la subida o bajada automática de EOP."""
        if self._eop_phase == "rising":
            self._analog_values["EOP"] = min(
                self._EOP_MAX_V,
                self._analog_values["EOP"] + self._EOP_STEP_V,
            )
            if self._analog_values["EOP"] >= self._EOP_MAX_V:
                self._eop_phase = "falling"
                self._eop_timer.start(self._EOP_RAMP_DOWN_INTERVAL_MS)
            else:
                self._eop_timer.start(self._EOP_RAMP_UP_INTERVAL_MS)
            return

        if self._eop_phase == "falling":
            self._analog_values["EOP"] = max(
                self._EOP_MIN_V,
                self._analog_values["EOP"] - self._EOP_RAMP_DOWN_STEP_V,
            )
            if self._analog_values["EOP"] <= self._EOP_MIN_V:
                self._eop_phase = None
                self._eop_timer.stop()
            else:
                self._eop_timer.start(self._EOP_RAMP_DOWN_INTERVAL_MS)

    def analog_write(self, signal_name, voltage):
        from config.analog_signals import ANALOG_OUTPUTS
        if signal_name not in ANALOG_OUTPUTS:
            raise KeyError(f"Salida analógica no configurada: {signal_name}")
        config = ANALOG_OUTPUTS[signal_name]
        value = float(voltage)
        if not config["min_voltage"] <= value <= config["max_voltage"]:
            raise ValueError(f"Tensión fuera de rango para {signal_name}")
        self._analog_outputs[signal_name] = value
        self._update_simulated_mfc_flow(signal_name, value)

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
