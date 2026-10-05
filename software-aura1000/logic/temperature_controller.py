# logic/temperature_controller.py
import os
import time
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox
from config.digital_signals import ACTIVE, INACTIVE


class TempController:

    def __init__(self, main_window):
        self.win = main_window
        self.hw = main_window.hw
        self.ui = main_window.ui

        # Parámetros del Lazo de Control
        self.target_temp = 0.0  # Setpoint (°C)
        self.auto_control_enabled = False

        # Rangos permitidos de receta
        self.MIN_TEMP_SETPOINT = 130.0
        self.MAX_TEMP_SETPOINT = 200.0

        # Lógica PWM de Ventana Fija (200 ms = 10 ciclos de 50 Hz)
        self.CONTROL_PERIOD_MS = 200
        self.TIMER_INTERVAL_MS = 20
        self.duty_cycle = 0.0  # 0.0 a 1.0

        # Filtro de media móvil
        self._temp_buffer = []
        self._TEMP_BUFFER_SIZE = 5  # promedio de últimos 500ms

        # Estado interno de la Rampa Inicial
        self.in_preheat_ramp = False
        self.waiting_first_dip = False  # Bandera de amortiguación post-rampa

        # Listas para graficar temperatura en función del tiempo
        self._log_time = []  # timestamps en segundos
        self._log_temp = []  # temperatura medida en °C
        self._log_setpoint = []  # setpoint objetivo
        self._log_start_time = None

        # Timer dedicado a la modulación PWM y actualización del lazo
        self.pwm_timer = QtCore.QTimer()
        self.pwm_timer.timeout.connect(self._update_temperature_loop)
        self._window_start_time = 0.0

        # Conectar botones de la UI
        self._connect_ui_signals()

    def _connect_ui_signals(self):
        """Conecta los botones del Menú de Temperatura a los handlers."""
        if hasattr(self.ui, "MenuPrincipal_btn_temp_set"):
            self.ui.MenuPrincipal_btn_temp_set.clicked.connect(self.on_start_auto_control)
        if hasattr(self.ui, "MenuPrincipal_btn_temp_stop"):
            self.ui.MenuPrincipal_btn_temp_stop.clicked.connect(self.stop_auto_control)
        # Conexión del Slider para prueba manual de Duty Cycle
        if hasattr(self.ui, "tempSlider"):
            self.ui.tempSlider.valueChanged.connect(self._on_slider_duty_changed)

    # =============================================================================
    #        METODO PARA GENERAR EL PLOT Y GUARDARLO EN logic/logs
    # =============================================================================
    def _generate_temperature_plot(self):
        if len(self._log_time) < 2:
            print("[TEMP] Sin datos suficientes para graficar.")
            return

        from datetime import datetime
        import matplotlib.pyplot as plt

        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(logs_dir, f"temp_log_{timestamp}.png")

        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(
            self._log_time,
            self._log_temp,
            label="Temperatura medida",
            color="crimson",
            linewidth=1.5,
        )
        ax.plot(
            self._log_time,
            self._log_setpoint,
            label="Setpoint",
            color="darkblue",
            linewidth=1.2,
            linestyle="--",
        )

        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Temperatura (°C)")
        ax.set_title(f"Control de Temperatura — Setpoint: {self.target_temp:.1f} °C")
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close(fig)

        print(f"[TEMP] Gráfico de temperatura guardado en: {filename}")

    # =============================================================================
    #                       INICIO Y PARADA DE LAZO AUTOMÁTICO
    # =============================================================================
    def on_start_auto_control(self):
        """Handler del botón de encendido de control automático de temperatura."""
        try:
            text_val = (
                self.ui.MenuPrincipal_temp_setpoint.text().replace(",", ".")
            )
            target = float(text_val)

            if (
                self.MIN_TEMP_SETPOINT
                <= target
                <= self.MAX_TEMP_SETPOINT
            ):
                self.start_auto_control(target)
            else:
                QMessageBox.warning(
                    self.win,
                    "Setpoint Fuera de Rango",
                    f"El setpoint de temperatura debe estar entre {self.MIN_TEMP_SETPOINT:.0f}°C y {self.MAX_TEMP_SETPOINT:.0f}°C.",
                    QMessageBox.Ok,
                )
        except ValueError:
            QMessageBox.warning(
                self.win,
                "Entrada Inválida",
                "Ingrese un número válido para el setpoint de temperatura.",
                QMessageBox.Ok,
            )

    def start_auto_control(self, target_temp: float):
        """Inicia la rampa con las 3 lámparas y activa el temporizador PWM."""
        self.target_temp = target_temp
        self.auto_control_enabled = True
        self.in_preheat_ramp = True

        print(f"[TEMP] Lazo de Temperatura ACTIVADO. Setpoint: {self.target_temp:.1f} °C")

        # 1. Rampa Inicial: Encendemos Lámparas 1, 2 y 3 juntas
        self.hw.digital_set("LAMP1_ON_CMD", ACTIVE)
        self.hw.digital_set("LAMP2_ON_CMD", ACTIVE)
        self.hw.digital_set("LAMP3_ON_CMD", ACTIVE)
        self.win.state_lamps13_pulsing = True
        self.win.lamp2_on = True

        # 2. Bloquear controles manuales de lámparas
        self._update_ui_interlocks(running=True)

        # 3. Reiniciar búferes de logueo
        self._log_time = []
        self._log_temp = []
        self._log_setpoint = []
        self._log_start_time = time.time()

        # 4. Arrancar timer del lazo PWM (evaluación rápida cada 20 ms)
        self.pwm_timer.start(self.TIMER_INTERVAL_MS)

    def stop_auto_control(self):
        """Apaga el lazo automático, desactiva comandos y libera los botones manuales."""
        print("[TEMP] Lazo de Temperatura DESACTIVADO.")
        self.auto_control_enabled = False
        self.in_preheat_ramp = False
        self.waiting_first_dip = False  # Bandera de amortiguación post-rampa
        self.duty_cycle = 0.0

        if self.pwm_timer.isActive():
            self.pwm_timer.stop()

        # Apagado de seguridad de las 3 lámparas
        self.hw.digital_set("LAMP1_ON_CMD", INACTIVE)
        self.hw.digital_set("LAMP2_ON_CMD", INACTIVE)
        self.hw.digital_set("LAMP3_ON_CMD", INACTIVE)

        self.win.state_lamps13_pulsing = False
        self.win.lamp2_on = False

        # Generar gráfico al detener el lazo
        self._generate_temperature_plot()

        # Liberar controles de UI
        self._update_ui_interlocks(running=False)

    # =============================================================================
    #                   LAZO CERRADO Y MODULACIÓN PWM
    # =============================================================================
    def _update_temperature_loop(self):
        """Calcula el Duty Cycle y conmuta el SSR2 (Lámpara Central) con PWM."""
        # ── MODALIDAD PRUEBA MANUAL CON SLIDER ──
        if not self.auto_control_enabled:
            now = time.time()
            elapsed_ms = (now - self._window_start_time) * 1000.0

            # Reiniciar la ventana de 200 ms cuando se cumple el período
            if elapsed_ms >= self.CONTROL_PERIOD_MS:  # 200 ms
                self._window_start_time = now
                elapsed_ms = 0.0

            on_time_ms = self.CONTROL_PERIOD_MS * self.duty_cycle

            # Conmutar L2 solo al cambiar de estado para no saturar el bus
            if elapsed_ms < on_time_ms:
                if not self.win.lamp2_on:
                    self.hw.digital_set("LAMP2_ON_CMD", ACTIVE)
                    self.win.lamp2_on = True
            else:
                if self.win.lamp2_on:
                    self.hw.digital_set("LAMP2_ON_CMD", INACTIVE)
                    self.win.lamp2_on = False
            return

        # ── MODALIDAD CONTROL AUTOMÁTICO DE TEMPERATURA ──
        # 1. Lectura de temperatura centralizada de analog_update.py
        current_temp = getattr(self.win, "last_chamber_temp", None)
        if current_temp is None:
            return

        # 2. Filtro de media móvil para suavizar ruido de termocupla
        self._temp_buffer.append(current_temp)
        if len(self._temp_buffer) > self._TEMP_BUFFER_SIZE:
            self._temp_buffer.pop(0)
        filtered_temp = sum(self._temp_buffer) / len(self._temp_buffer)

        # Registro de datos para el gráfico
        if self._log_start_time is not None:
            elapsed = time.time() - self._log_start_time
            self._log_time.append(elapsed)
            self._log_temp.append(filtered_temp)
            self._log_setpoint.append(self.target_temp)

        # 3. FASE DE RAMPA INICIAL
        if self.in_preheat_ramp:
            preheat_threshold = (self.target_temp * 1.05)  # Rampa al 105% para cargar el susceptor
            if filtered_temp >= preheat_threshold:
                print(
                    f"[TEMP] Rampa completada ({filtered_temp:.1f} °C). Apagando L1 y L3. "
                    f"Iniciando sostenimiento post-rampa."
                )
                self.hw.digital_set("LAMP1_ON_CMD", INACTIVE)
                self.hw.digital_set("LAMP3_ON_CMD", INACTIVE)
                self.win.state_lamps13_pulsing = False
                self.in_preheat_ramp = False
                self.waiting_first_dip = True  # Bandera para sostener L2 en el sobrepico inicial
                self._window_start_time = time.time()
            else:
                return

        else:
            # 4. FASE DE MANTENIMIENTO: Amortiguación + Escala gradual
            error = self.target_temp - filtered_temp

            # ── A. AMORTIGUACIÓN POST-RAMPA INICIAL ──
            if self.waiting_first_dip:
                if filtered_temp <= self.target_temp:
                    print(f"[TEMP] Inercia de rampa disipada ({filtered_temp:.1f} °C). Activando tabla PWM gradual.")
                    self.waiting_first_dip = False
                else:
                    self.duty_cycle = 1.0

            # ── B. ESCALA GRADUAL CUANDO YA ESTÁ EN RÉGIMEN ──
            if not self.waiting_first_dip:
                if error > 5.0:
                    self.duty_cycle = 1.0  # > 5 °C abajo -> 100% ON
                elif error > 2.0:
                    self.duty_cycle = 0.90  # 2 °C a 5 °C abajo -> 90% ON
                elif error > 0.0:
                    self.duty_cycle = 0.80  # 0 °C a 2 °C abajo -> 80% ON
                elif error > -2.0:
                    self.duty_cycle = 0.60  # 0 °C a 2 °C sobrepasado -> 60% ON
                elif error > -5.0:
                    self.duty_cycle = 0.40  # 2 °C a 5 °C sobrepasado -> 40% ON
                elif error > -10.0:
                    self.duty_cycle = 0.20  # 5 °C a 10 °C sobrepasado -> 20% ON
                else:
                    self.duty_cycle = 0.0  # > 10 °C sobrepasado -> 0% OFF

            print(
                f"[TEMP] T={current_temp:.1f}°C  T_filt={filtered_temp:.1f}°C  "
                f"error={error:.1f}°C  duty={self.duty_cycle:.0%}"
            )

        # 5. Modulación PWM en ventana de CONTROL_PERIOD_MS (200 ms)
        now = time.time()
        elapsed_ms = (now - self._window_start_time) * 1000.0

        if elapsed_ms >= self.CONTROL_PERIOD_MS:
            self._window_start_time = now
            elapsed_ms = 0.0

        on_time_ms = self.CONTROL_PERIOD_MS * self.duty_cycle

        if elapsed_ms < on_time_ms:
            if not self.win.lamp2_on:
                self.hw.digital_set("LAMP2_ON_CMD", ACTIVE)
                self.win.lamp2_on = True
        else:
            if self.win.lamp2_on:
                self.hw.digital_set("LAMP2_ON_CMD", INACTIVE)
                self.win.lamp2_on = False

    def _on_slider_duty_changed(self, value: int):
        """Maneja el slider manual (0 a 100%). Arranca o detiene el timer PWM según el valor."""
        self.duty_cycle = value / 100.0
        print(f"[MANUAL] Slider Duty Cycle: {value}% ({self.duty_cycle:.2f})")

        # Si el control automático no está activo, controlamos el timer de forma manual
        if not self.auto_control_enabled:
            if value > 0:
                if not self.pwm_timer.isActive():
                    self._window_start_time = time.time()
                    self.pwm_timer.start(self.TIMER_INTERVAL_MS)  # Arranca el timer a 20ms
            else:
                # Si volvió a 0%, apagamos el timer y la lámpara
                if self.pwm_timer.isActive():
                    self.pwm_timer.stop()
                self.hw.digital_set("LAMP2_ON_CMD", INACTIVE)
                self.win.lamp2_on = False

    # =============================================================================
    #                           INTERLOCKS DE INTERFAZ
    # =============================================================================
    def _update_ui_interlocks(self, running: bool):
        """Maneja la exclusión mutua entre el control automático y los botones manuales de lámparas."""
        btn_l13 = getattr(self.ui, "MenuPrincipal_btn_outerLamps", None)
        btn_l2 = getattr(self.ui, "MenuPrincipal_btn_centralLamp", None)
        entry_l13 = getattr(
            self.ui, "MenuPrincipal_outerLamps_pulseTime", None
        )

        entry_temp = getattr(self.ui, "MenuPrincipal_temp_setpoint", None)
        btn_temp_set = getattr(self.ui, "MenuPrincipal_btn_temp_set", None)
        btn_temp_stop = getattr(self.ui, "MenuPrincipal_btn_temp_stop", None)

        if running:
            # Deshabilitar controles manuales
            if btn_l13:
                btn_l13.setEnabled(False)
            if btn_l2:
                btn_l2.setEnabled(False)
            if entry_l13:
                entry_l13.setEnabled(False)
            if entry_temp:
                entry_temp.setEnabled(False)
            if btn_temp_set:
                btn_temp_set.setEnabled(False)
            if btn_temp_stop:
                btn_temp_stop.setEnabled(True)
        else:
            # Habilitar controles manuales si estamos en vacío
            is_vacuum = (
                getattr(self.win.ui, "MenuPrincipal_btn_main_vacuum", None)
                and self.win.ui.MenuPrincipal_btn_main_vacuum.text()
                == "Main Vacuum Off"
            )

            if btn_l13:
                btn_l13.setEnabled(is_vacuum)
            if btn_l2:
                btn_l2.setEnabled(is_vacuum)
            if entry_l13:
                entry_l13.setEnabled(is_vacuum)

            if entry_temp:
                entry_temp.setEnabled(is_vacuum)
            if btn_temp_set:
                btn_temp_set.setEnabled(is_vacuum)
            if btn_temp_stop:
                btn_temp_stop.setEnabled(False)