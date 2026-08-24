from config.digital_signals import ACTIVE, INACTIVE

# logic/throttle_controller.py

from config.digital_signals import ACTIVE, INACTIVE


class ThrottleController:

    def __init__(self, main_window):
        self.win = main_window
        self.hw = main_window.hw
        self.ui = main_window.ui

        # Apuntamos directamente al timer en el manager central
        self.step_timer = main_window.timer_manager.timers["stepper_pulse"]
        self.step_state = INACTIVE
        self._closing = False  # True = Cierra, False = Abre

        # Conectar señales de la UI a los métodos de esta clase
        self._connect_ui_signals()

    def _connect_ui_signals(self):
        """Conecta los botones del menú de la Throttle a sus manejadores internos."""
        self.ui.ThrottleMenu_btn_toggle_enable.clicked.connect(
            self.on_enable_toggled
        )
        self.ui.ThrottleMenu_btn_toggle_step.clicked.connect(
            self.on_step_toggled
        )
        self.ui.ThrottleMenu_btn_toggle_dir.clicked.connect(self.on_dir_toggled)
        self.ui.ThrottleMenu_btn_toggle_run.clicked.connect(self.on_run_toggled)

    # ── Métodos de Hardware / Control ─────────────────────────────

    def set_enable(self, state: bool):
        self.hw.digital_set("STEPPER_OUTPUT_ENABLE", state)

    def set_half_step(self, use_half: bool):
        self.hw.digital_set("STEPPER_HALF_STEP", use_half)

    def set_direction(self, close_direction: bool):
        self._closing = close_direction
        self.hw.digital_set("STEPPER_DIR", close_direction)

    def start_movement(self, speed_ms=6):
        if not self.step_timer.isActive():
            self.step_state = INACTIVE
            self.hw.digital_set("STEPPER_STEP", self.step_state)

            try:
                self.step_timer.timeout.disconnect()
            except TypeError:
                pass

            self.step_timer.timeout.connect(self._toggle_step)
            self.step_timer.start(speed_ms)

    def stop_movement(self):
        self.step_timer.stop()
        self.step_state = INACTIVE
        self.hw.digital_set("STEPPER_STEP", INACTIVE)
        self.reset_run_button()

    def _toggle_step(self):
        if self._check_limits():
            return
        self.step_state = not self.step_state
        self.hw.digital_set("STEPPER_STEP", self.step_state)

    # ── Handlers de Eventos de Botones (UI) ────────────────────────

    def on_enable_toggled(self):
        btn = self.ui.ThrottleMenu_btn_toggle_enable
        if btn.text() == "Habilitar Driver":
            self.set_enable(ACTIVE)
            btn.setText("Deshabilitar Driver")
            btn.setStyleSheet("background-color: #f44336; color: white;")
        else:
            self.set_enable(INACTIVE)
            btn.setText("Habilitar Driver")
            btn.setStyleSheet("")

    def on_step_toggled(self):
        btn = self.ui.ThrottleMenu_btn_toggle_step
        if "Full Step" in btn.text():
            self.set_half_step(ACTIVE)
            btn.setText("Modo: Half Step")
        else:
            self.set_half_step(INACTIVE)
            btn.setText("Modo: Full Step")

    def on_dir_toggled(self):
        btn = self.ui.ThrottleMenu_btn_toggle_dir
        if "Apertura" in btn.text():
            self.set_direction(ACTIVE)
            btn.setText("Dirección: Cierre")
        else:
            self.set_direction(INACTIVE)
            btn.setText("Dirección: Apertura")

    def on_run_toggled(self):
        btn = self.ui.ThrottleMenu_btn_toggle_run
        if btn.text() == "Girar Motor":
            self.start_movement(speed_ms=6)
            btn.setText("Detener Motor")
            btn.setStyleSheet(
                "background-color: #ff9800; color: black; font-weight: bold;"
            )
        else:
            self.stop_movement()

    def reset_run_button(self):
        btn = self.ui.ThrottleMenu_btn_toggle_run
        btn.setText("Girar Motor")
        btn.setStyleSheet("")

    # ── Limit Switches y Monitoreo ─────────────────────────────────

    def is_fully_closed(self) -> bool:
        return self.hw.digital_read("THROTTLE_CLOSED")

    def is_fully_open(self) -> bool:
        return self.hw.digital_read("THROTTLE_OPEN")

    def _check_limits(self) -> bool:
        if self._closing and self.is_fully_closed():
            print("[LÍMITE] Válvula Throttle completamente CERRADA.")
            self.stop_movement()
            return True

        if not self._closing and self.is_fully_open():
            print("[LÍMITE] Válvula Throttle completamente ABIERTA.")
            self.stop_movement()
            return True

        return False

    def update_limit_switch_status(self):
        """Llamado en el lazo principal (io_loop) cada 100ms."""
        lbl_closed = self.ui.lbl_throttle_closed
        lbl_open = self.ui.lbl_throttle_open

        if self.is_fully_closed():
            lbl_closed.setText("CERRADA ✓")
            lbl_closed.setStyleSheet("color: red; font-weight: bold;")
        else:
            lbl_closed.setText("Cerrada: —")
            lbl_closed.setStyleSheet("")

        if self.is_fully_open():
            lbl_open.setText("ABIERTA ✓")
            lbl_open.setStyleSheet("color: green; font-weight: bold;")
        else:
            lbl_open.setText("Abierta: —")
            lbl_open.setStyleSheet("")