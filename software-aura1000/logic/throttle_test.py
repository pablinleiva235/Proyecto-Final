from config.digital_signals import ACTIVE, INACTIVE

class ThrottleController:
    def __init__(self, main_window):
        self.win = main_window
        self.hw = main_window.hw
        
        # Apuntamos directamente al objeto alojado en el manager central
        self.step_timer = main_window.timer_manager.timers['stepper_pulse']
        self.step_state = INACTIVE

    def set_enable(self, state: bool):
        """Habilita o deshabilita las salidas de potencia del driver"""
        self.hw.digital_set("STEPPER_OUTPUT_ENABLE", state)

    def set_half_step(self, use_half: bool):
        """True = Half Step (M0=1), False = Full Step (M0=0)"""
        self.hw.digital_set("STEPPER_HALF_STEP", use_half)

    def set_direction(self, close_direction: bool):
        """True = Cierra (1), False = Abre (0)"""
        self.hw.digital_set("STEPPER_DIR", close_direction)

    def start_movement(self, speed_ms=5):
        """Inicia el tren de pulsos asíncrono"""
        if not self.step_timer.isActive():
            self.step_state = INACTIVE
            self.hw.digital_set("STEPPER_STEP", self.step_state)
            
            # Limpiamos conexiones previas por seguridad antes de enlazar el callback
            try:
                self.step_timer.timeout.disconnect()
            except TypeError:
                pass
                
            self.step_timer.timeout.connect(self._toggle_step)
            self.step_timer.start(speed_ms)

    def stop_movement(self):
        """Detiene el tren de pulsos y limpia la línea"""
        self.step_timer.stop()
        self.step_state = INACTIVE
        self.hw.digital_set("STEPPER_STEP", INACTIVE)

    def _toggle_step(self):
        """Genera la onda cuadrada para el pin de STEP"""
        self.step_state = not self.step_state
        self.hw.digital_set("STEPPER_STEP", self.step_state)