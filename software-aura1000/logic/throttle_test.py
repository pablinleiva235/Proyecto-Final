# logic/throttle_controller.py
import time
import json
import os
from PyQt5.QtWidgets import QMessageBox
from config.digital_signals import ACTIVE, INACTIVE

# Guardar el archivo con numero de paso actual directamente en la carpeta logic
STATE_FILE = os.path.join("logic", "throttle_state.json")

class ThrottleController:

    # =============================================================================
    #                INICIALIZACION Y CONEXION DE BOTONES CON METODOS
    # =============================================================================    
    def __init__(self, main_window):
        self.win = main_window
        self.hw = main_window.hw
        self.ui = main_window.ui

        # Apuntamos directamente al timer en el manager central
        self.step_timer = main_window.timer_manager.timers["stepper_pulse"]
        self.step_state = INACTIVE
        self._closing = False  # True = Cierra, False = Abre
        self._is_half_step = False  # False = Full step, True = Half step

        # Variables para antirrebote en switchs de limites
        self._closed_count = 0  # contador de lecturas consistentes
        self._open_count   = 0
        self._DEBOUNCE_N   = 3  # N lecturas iguales para confirmar

        # Contador de posición absoluta y control de ráfaga de pasos
        self.current_step = self._load_saved_step() # Cargar último paso guardado al iniciar
        self._target_steps = 0  # Pasos restantes cuando se mueve por ráfaga
        self._step_mode = "CONTINUOUS"  # "CONTINUOUS" o "BURST"

        # Parámetros de Control de Presión 
        self.target_pressure = 0.0  # Setpoint en Torr
        self.deadband = 0.035  # Tolerancia (+/- Torr)
        self.auto_control_enabled = False

        # Listas para graficar ajuste de presion en funcion del tiempo
        self._log_time     = []   # timestamps en segundos
        self._log_pressure = []   # presión medida en Torr
        self._log_setpoint = []   # setpoint para graficarlo como línea de referencia
        self._log_start_time = None

        self.THROTTLE_STEP_FREQUENCY = 186 # Pulsos por segundo
        self.SPEED_MS = int(1000 / self.THROTTLE_STEP_FREQUENCY / 2) # x1000 para ms y divido por 2 porque cada SPEED_MS togglea de HIGH a LOW 

        # Conectar señales de la UI a los métodos de esta clase
        self._connect_ui_signals()

        # Actualizar la pantalla con el valor cargado del ultimo paso
        self._update_step_display()

        # Lanzamos el Homing al iniciar
        self.home_on_startup()

    def _connect_ui_signals(self):
        """Conecta los botones del menú de la Throttle a sus manejadores internos."""
        self.ui.ThrottleMenu_btn_toggle_enable.clicked.connect(self.on_enable_toggled)
        self.ui.ThrottleMenu_btn_toggle_step.clicked.connect(self.on_step_toggled)
        self.ui.ThrottleMenu_btn_toggle_dir.clicked.connect(self.on_dir_toggled)
        self.ui.ThrottleMenu_btn_toggle_run.clicked.connect(self.on_run_toggled)
        self.ui.ThrottleMenu_step_set.clicked.connect(self.on_step_set_clicked)
        self.ui.ThrottleMenu_pressure_set.clicked.connect(self.on_start_auto_control)
        self.ui.ThrottleMenu_pressure_stop.clicked.connect(self.stop_auto_control)
        # Deshabilita al inicio los botones de ajuste de presion hasta no hacer vacio
        # Bloqueo de seguridad inicial al arrancar
        self.ui.ThrottleMenu_pressure_set.setEnabled(False)
        self.ui.ThrottleMenu_pressure_stop.setEnabled(False)
        self.ui.ThrottleMenu_pressure_entry.setEnabled(False)

    # =============================================================================
    #           HOMING DE LA THROTTLE AL INICIAR A POSICION ABIERTA
    # =============================================================================  
    def home_on_startup(self):
        """Busca el límite físico de apertura al arrancar el software para calibrar el paso 0."""
        print("[THROTTLE] Iniciando secuencia de Homing...")
        
        # 1. Aseguramos estado de hardware
        self.set_direction(INACTIVE)  # Dirección: Apertura
        self.set_enable(ACTIVE)       # Mantiene corriente en las bobinas
        self.set_half_step(INACTIVE)  # Full step para homing
        
        # 2. Sincronizamos el botón de la UI para que muestre que está habilitado
        btn_enable = getattr(self.ui, "ThrottleMenu_btn_toggle_enable", None)
        if btn_enable:
            btn_enable.setText("Deshabilitar Driver")
            btn_enable.setStyleSheet("background-color: #f44336; color: white;")

        # 3. Arrancamos el movimiento hacia el Limit Switch
        self.start_movement(self.SPEED_MS)

    # =============================================================================
    #     METODOS PARA CARGAR Y GUARDAR EL ULTIMO PASO DE LA THROTTLE (JSON)
    # =============================================================================  
    def _load_saved_step(self) -> int:
        """Lee el último paso guardado en disco al iniciar la aplicación."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("current_step", 0)
            except Exception as e:
                print(f"[THROTTLE] Error al cargar estado previo del motor: {e}")
        return 0

    def _save_current_step(self):
        """Guarda la posición actual en disco."""
        try:
            os.makedirs("logic", exist_ok=True)
            with open(STATE_FILE, "w") as f:
                json.dump({"current_step": self.current_step}, f)
        except Exception as e:
            print(f"[THROTTLE] Error al guardar estado del motor: {e}")

    # =============================================================================
    #        METODOS PARA GENERAR EL PLOT Y GUARDARLO EN logic/logs
    # =============================================================================  
    def _generate_pressure_plot(self):
        if len(self._log_time) < 2:
            print("[THROTTLE] Sin datos suficientes para graficar.")
            return

        import matplotlib.pyplot as plt
        from datetime import datetime
        import subprocess
        import sys

        # Carpeta logs/ siempre al lado de throttle_controller.py
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = os.path.join(logs_dir, f"throttle_log_{timestamp}.png")

        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(self._log_time, self._log_pressure,
                label="Presión medida", color="royalblue", linewidth=1.5)
        ax.plot(self._log_time, self._log_setpoint,
                label="Setpoint", color="red",
                linewidth=1.2, linestyle="--")

        # Banda muerta
        ax.axhline(self.target_pressure + self.deadband,
                color="orange", linewidth=0.8,
                linestyle=":", label=f"Deadband (±{self.deadband} Torr)")
        ax.axhline(self.target_pressure - self.deadband,
                color="orange", linewidth=0.8, linestyle=":")

        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Presión (Torr)")
        ax.set_title(f"Control de Presión Throttle — Setpoint: {self.target_pressure:.3f} Torr")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close(fig)

        print(f"[THROTTLE] Gráfico guardado en: {filename}")

        '''
        # Abrir automáticamente
        if sys.platform == "win32":
            os.startfile(filename)
        else:
            subprocess.Popen(["xdg-open", filename])
        '''
        
    # =============================================================================
    #              METODOS PARA CONTROL AUTOMATICO DE PRESION
    # =============================================================================  
    def start_auto_control(self, target_torr: float):
        """Activa la regulación automática con el setpoint ingresado."""
        self.target_pressure = max(0.0, target_torr)
        self.auto_control_enabled = True
        self.set_enable(ACTIVE)  # Aseguramos driver habilitado
        self._update_ui_interlocks(running=True)

        # Inicializar log
        self._log_time     = []
        self._log_pressure = []
        self._log_setpoint = []
        self._log_start_time = time.time()

        print(f"[THROTTLE] Control de presión ACTIVADO. Target: {self.target_pressure:.3f} Torr")

    def stop_auto_control(self):
        """Desactiva la regulación automática y detiene el motor."""
        print("[THROTTLE] Control de presión DESACTIVADO manualmente.")
        self.stop_movement()
        self._generate_pressure_plot()

    def update_pressure_loop(self, current_pressure: float):
        if not self.auto_control_enabled:
            return

        error = self.target_pressure - current_pressure

        # Registrar lectura para generar grafico
        if self._log_start_time is not None:
            elapsed = time.time() - self._log_start_time
            self._log_time.append(elapsed)
            self._log_pressure.append(current_pressure)
            self._log_setpoint.append(self.target_pressure)

        # 1. Zona muerta
        if abs(error) <= self.deadband:
            if self.step_timer.isActive():
                self.step_timer.stop()
                self.step_state = INACTIVE
                self.hw.digital_set("STEPPER_STEP", INACTIVE)
                self._save_current_step()
                print("[THROTTLE] Presión dentro de tolerancia. Motor pausado.")
            return

        # 2. Velocidad y modo según magnitud del error
        if abs(error) > 0.3:
            speed_ms  = self.SPEED_MS
            use_half  = False           # Full step
        elif abs(error) > 0.05:
            speed_ms  = self.SPEED_MS * 2
            use_half  = False           # Full step
        else:
            speed_ms  = self.SPEED_MS * 2
            use_half  = True            # Half step

        # 3. Cambiar modo de paso si es necesario (con motor detenido momentáneamente)
        if use_half != self._is_half_step:
            was_active = self.step_timer.isActive()
            if was_active:
                self.step_timer.stop()
                self.hw.digital_set("STEPPER_STEP", INACTIVE)
            self.set_half_step(use_half)
            if was_active:
                self.step_timer.start(speed_ms)

        # 4. Dirección según signo del error
        should_close = error > 0
        if self._closing != should_close:
            self.set_direction(should_close)

        # 5. Arrancar o actualizar velocidad
        if not self.step_timer.isActive():
            self.start_movement(speed_ms)
        elif self.step_timer.interval() != speed_ms:
            self.step_timer.setInterval(speed_ms)

    def on_start_auto_control(self):
        """Handler del botón Ajustar Presión (ThrottleMenu_pressure_set)."""
        try:
            val_text = self.ui.ThrottleMenu_pressure_entry.text().strip()
            target = float(val_text)

            if 1.0 <= target <= 3.0:
                self.start_auto_control(target)
            else:
                QMessageBox.warning(
                    self.win,
                    "Rango Inválido",
                    "Ingrese un setpoint de presión entre 1.0 y 3.0 Torr.",
                    QMessageBox.Ok,
                )
                print(
                    "[THROTTLE] Setpoint fuera de rango (debe ser 1.0 a 3.0 Torr)."
                )

        except ValueError:
            QMessageBox.warning(
                self.win,
                "Entrada Inválida",
                "Ingrese un número válido para el setpoint de presión.",
                QMessageBox.Ok,
            )
            print("[THROTTLE] Valor de presión inválido en el campo de texto.")

    # =============================================================================
    #                    METODOS DE HARDWARE/CONTROL MANUAL
    # =============================================================================  

    def set_enable(self, state: bool):
        self.hw.digital_set("STEPPER_OUTPUT_ENABLE", state)

    def set_half_step(self, use_half: bool):
        self._is_half_step = use_half
        self.hw.digital_set("STEPPER_HALF_STEP", use_half)

    def set_direction(self, close_direction: bool):
        self._closing = close_direction
        self.hw.digital_set("STEPPER_DIR", close_direction)

    def start_movement(self, speed_ms: int, steps: int = 0):
        """
        Inicia el temporizador de pasos.
        Si steps > 0 se configura en modo BURST (se detiene al cumplir los pasos).
        Si steps == 0 se opera en modo CONTINUOUS.
        """
        if not self.step_timer.isActive():
            self.step_state = INACTIVE
            self.hw.digital_set("STEPPER_STEP", self.step_state)

            if steps > 0:
                self._step_mode = "BURST"
                self._target_steps = steps
            else:
                self._step_mode = "CONTINUOUS"
                self._target_steps = 0

            try:
                self.step_timer.timeout.disconnect()
            except TypeError:
                pass

            self.step_timer.timeout.connect(self._toggle_step)
            self.step_timer.start(speed_ms)

            # Bloqueo mutual de la UI según el modo de arranque
            self._update_ui_interlocks(running=True)
            print(f"[THROTTLE] Movimiento INICIADO ({self._step_mode}) -> Timer activo cada {speed_ms} ms.")
        else:
            print("[THROTTLE] Intento de arranque ignorado: El timer ya está activo.")

    def stop_movement(self):
            self.step_timer.stop()
            self.step_state = INACTIVE
            self.hw.digital_set("STEPPER_STEP", INACTIVE)

            self._target_steps = 0
            self._step_mode = "CONTINUOUS"
            self.auto_control_enabled = False  # Apaga lazo automático

            self._save_current_step()
            self._update_ui_interlocks(running=False)
            self.reset_run_button()
            print("[THROTTLE] Movimiento DETENIDO y pin STEP llevado a INACTIVE.")

    def _toggle_step(self):
        if self._check_limits():
            return

        self.step_state = not self.step_state
        self.hw.digital_set("STEPPER_STEP", self.step_state)

        if self.step_state == ACTIVE:
            step_increment = 0.5 if self._is_half_step else 1.0

            if self._closing:
                self.current_step += step_increment
            else:
                self.current_step -= step_increment

            self._update_step_display()

            if self._step_mode == "BURST":
                self._target_steps -= 1
                if self._target_steps <= 0:
                    print("[THROTTLE] Ráfaga de pasos completada con éxito.")
                    self.stop_movement()

    def _update_step_display(self):
        """Actualiza el display LCD con la posición actual fijando 1 decimal."""
        if hasattr(self.ui, "ThrottleMenu_step_counter"):
            self.ui.ThrottleMenu_step_counter.display(f"{float(self.current_step):.1f}")

    # =============================================================================
    #                         MANEJO DE INTERLOCKS DE UI
    # =============================================================================  
    def _update_ui_interlocks(self, running: bool):
        """Maneja la exclusión mutua de controles en la interfaz."""
        btn_run = getattr(self.ui, "ThrottleMenu_btn_toggle_run", None)
        btn_step_set = getattr(self.ui, "ThrottleMenu_step_set", None)
        entry_step = getattr(self.ui, "ThrottleMenu_step_entry", None)

        p_entry = getattr(self.ui, "ThrottleMenu_pressure_entry", None)
        p_set = getattr(self.ui, "ThrottleMenu_pressure_set", None)
        p_stop = getattr(self.ui, "ThrottleMenu_pressure_stop", None)

        if running:
            if self.auto_control_enabled:
                # Si está corriendo control automático de presión:
                if btn_run:
                    btn_run.setEnabled(False)
                if btn_step_set:
                    btn_step_set.setEnabled(False)
                if entry_step:
                    entry_step.setEnabled(False)
                if p_entry:
                    p_entry.setEnabled(False)
                if p_set:
                    p_set.setEnabled(False)
                if p_stop:
                    p_stop.setEnabled(True)
            else:
                # Si está en movimiento manual o ráfaga (BURST/CONTINUOUS):
                if p_entry:
                    p_entry.setEnabled(False)
                if p_set:
                    p_set.setEnabled(False)
                if p_stop:
                    p_stop.setEnabled(False)

                if self._step_mode == "CONTINUOUS":
                    if btn_step_set:
                        btn_step_set.setEnabled(False)
                    if entry_step:
                        entry_step.setEnabled(False)
                elif self._step_mode == "BURST":
                    if btn_run:
                        btn_run.setEnabled(False)
                    if btn_step_set:
                        btn_step_set.setEnabled(False)
                    if entry_step:
                        entry_step.setEnabled(False)
        else:
            # Motor detenido: rehabilitar todos los controles
            if btn_run:
                btn_run.setEnabled(True)
            if btn_step_set:
                btn_step_set.setEnabled(True)
            if entry_step:
                entry_step.setEnabled(True)
            if p_entry:
                p_entry.setEnabled(True)
            if p_set:
                p_set.setEnabled(True)
            if p_stop:
                p_stop.setEnabled(True)

    # =============================================================================
    #            HANDLERS DE EVENTOS DE BOTONES DE MANEJO MANUAL (UI)
    # =============================================================================  

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
            self.start_movement(self.SPEED_MS)
            btn.setText("Detener Motor")
            btn.setStyleSheet("background-color: #ff9800; color: black; font-weight: bold;")
        else:
            self.stop_movement()

    def on_step_set_clicked(self):
        """Handler para el botón 'Ajustar posicion'."""
        try:
            val_text = self.ui.ThrottleMenu_step_entry.text().strip()
            steps = int(val_text)

            if 0 < steps <= 1400:
                self.start_movement(self.SPEED_MS, steps=steps)
            else:
                QMessageBox.warning(
                    self.win,
                    "Rango Inválido",
                    "Ingrese un número de pasos entre 1 y 1400.",
                    QMessageBox.Ok,
                )
                print("[THROTTLE] Valor fuera de rango (debe ser entre 1 y 1400).")

        except ValueError:
            QMessageBox.warning(
                self.win,
                "Entrada Inválida",
                "Ingrese un valor numérico entero para los pasos.",
                QMessageBox.Ok,
            )
            print("[THROTTLE] Valor de pasos inválido en el campo de texto.")

    def reset_run_button(self):
        btn = self.ui.ThrottleMenu_btn_toggle_run
        btn.setText("Girar Motor")
        btn.setStyleSheet("")

    # =============================================================================
    #                        LIMIT SWITCHES Y MONITOREO
    # =============================================================================  

    def is_fully_closed(self) -> bool:
        return self.hw.digital_read("THROTTLE_CLOSED")

    def is_fully_open(self) -> bool:
        return self.hw.digital_read("THROTTLE_OPEN")

    def _check_limits(self) -> bool:
        if self._closing and (self._closed_count >= self._DEBOUNCE_N):
            print("[LÍMITE] Válvula Throttle completamente CERRADA.")
            self.stop_movement()
            return True

        if not self._closing and (self._open_count >= self._DEBOUNCE_N):
            print("[LÍMITE] Válvula Throttle completamente ABIERTA.")
            self.current_step = 0
            self._update_step_display()
            self.stop_movement()
            return True

        return False

    def update_limit_switch_status(self):
        closed_raw = self.is_fully_closed()
        open_raw   = self.is_fully_open()

        # Debounce CLOSED
        if closed_raw:
            self._closed_count = min(self._closed_count + 1, self._DEBOUNCE_N)
        else:
            self._closed_count = max(self._closed_count - 1, 0)

        # Debounce OPEN
        if open_raw:
            self._open_count = min(self._open_count + 1, self._DEBOUNCE_N)
        else:
            self._open_count = max(self._open_count - 1, 0)

        # Solo actualizás UI cuando hay N lecturas consistentes
        closed_confirmed = (self._closed_count >= self._DEBOUNCE_N)
        open_confirmed   = (self._open_count   >= self._DEBOUNCE_N)

        lbl_closed = self.ui.lbl_throttle_closed
        lbl_open   = self.ui.lbl_throttle_open

        if closed_confirmed:
            lbl_closed.setText("CERRADA ✓")
            lbl_closed.setStyleSheet("color: red; font-weight: bold; font-size: 48px;")
        else:
            lbl_closed.setText("Cerrada: —")
            lbl_closed.setStyleSheet("")

        if open_confirmed:
            lbl_open.setText("ABIERTA ✓")
            lbl_open.setStyleSheet("color: green; font-weight: bold; font-size: 48px;")
        else:
            lbl_open.setText("Abierta: —")
            lbl_open.setStyleSheet("")