# logic/temperature_controller.py
import time
import os
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

        # Lógica PWM de Ventana Fija (2.0 segundos)
        self.CONTROL_PERIOD_MS = 2000
        self.duty_cycle = 0.0  # 0.0 a 1.0

        # Estado interno de la Rampa Inicial
        self.in_preheat_ramp = False

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

    # =============================================================================
    #        METODO PARA GENERAR EL PLOT Y GUARDARLO EN logic/logs
    # =============================================================================  
    def _generate_temperature_plot(self):
        if len(self._log_time) < 2:
            print("[TEMP] Sin datos suficientes para graficar.")
            return

        import os
        from datetime import datetime
        import matplotlib.pyplot as plt

        # Carpeta logs/ al lado de temperature_controller.py
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
            text_val = self.ui.MenuPrincipal_temp_setpoint.text().replace(",", ".")
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

        # 4. Arrancar timer del lazo PWM (evaluación rápida cada 100 ms)
        self._window_start_time = time.time()
        self.pwm_timer.start(100)

    def stop_auto_control(self):
        """Apaga el lazo automático, desactiva comandos y libera los botones manuales."""
        print("[TEMP] Lazo de Temperatura DESACTIVADO.")
        self.auto_control_enabled = False
        self.in_preheat_ramp = False

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
    #                     LAZO CERRADO Y MODULACIÓN PWM
    # =============================================================================
    def _update_temperature_loop(self):
        """Calcula el Duty Cycle y conmuta el SSR2 (Lámpara Central) en la ventana de 2s."""
        if not self.auto_control_enabled:
            return

        # 1. Lectura de temperatura actual
        current_temp = self.hw.analog_read_temperature("CHAMBER_TEMP")
        if current_temp is None:
            return

        # ── REGISTRO DE DATOS PARA EL GRÁFICO ──
        if self._log_start_time is not None:
            elapsed = time.time() - self._log_start_time
            self._log_time.append(elapsed)
            self._log_temp.append(current_temp)
            self._log_setpoint.append(self.target_temp)

        # 2. FASE DE RAMPA INICIAL: Chequear si alcanzamos el 90% del Setpoint
        if self.in_preheat_ramp:
            preheat_threshold = self.target_temp * 0.90
            if current_temp >= preheat_threshold:
                print(f"[TEMP] Rampa completada ({current_temp:.1f} °C). Apagando Lámparas 1 y 3. Mantenimiento exclusivo con Lámpara Central.")
                self.hw.digital_set("LAMP1_ON_CMD", INACTIVE)
                self.hw.digital_set("LAMP3_ON_CMD", INACTIVE)
                self.win.state_lamps13_pulsing = False
                self.in_preheat_ramp = False
            else:
                # Durante la rampa, las 3 lámparas quedan al 100% encendidas
                return

        # 3. FASE DE MANTENIMIENTO: Calculamos el error y asignamos el Duty Cycle
        error = self.target_temp - current_temp

        if error > 30.0:
            self.duty_cycle = 1.0  # 100% ON
        elif error > 10.0:
            self.duty_cycle = 0.7  # 70% ON
        elif error > 5.0:
            self.duty_cycle = 0.4  # 40% ON
        elif error > 0.0:
            self.duty_cycle = 0.2  # 20% ON
        else:
            self.duty_cycle = 0.0  # OFF (Pasado o en Setpoint)

        # 4. Modulación PWM en ventana de 2000 ms
        now = time.time()
        elapsed_ms = (now - self._window_start_time) * 1000.0

        # Reiniciar ventana de 2s si se cumplió el período
        if elapsed_ms >= self.CONTROL_PERIOD_MS:
            self._window_start_time = now
            elapsed_ms = 0.0

        # Tiempo ON correspondiente dentro de la ventana
        on_time_ms = self.CONTROL_PERIOD_MS * self.duty_cycle

        # Conmutar SSR2 de Lámpara Central
        if elapsed_ms < on_time_ms:
            self.hw.digital_set("LAMP2_ON_CMD", ACTIVE)
            self.win.lamp2_on = True
        else:
            self.hw.digital_set("LAMP2_ON_CMD", INACTIVE)
            self.win.lamp2_on = False

    # =============================================================================
    #                          INTERLOCKS DE INTERFAZ
    # =============================================================================
    def _update_ui_interlocks(self, running: bool):
        """Maneja la exclusión mutua entre el control automático y los botones manuales de lámparas."""
        btn_l13 = getattr(self.ui, "MenuPrincipal_btn_outerLamps", None)
        btn_l2 = getattr(self.ui, "MenuPrincipal_btn_centralLamp", None)
        entry_l13 = getattr(self.ui, "MenuPrincipal_outerLamps_pulseTime", None)

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
            # Automaticos tambien asi no se cambia el setpoint mientras ajusta
            if entry_temp:
                entry_temp.setEnabled(False)
            if btn_temp_set:
                btn_temp_set.setEnabled(False)
            if btn_temp_stop:
                btn_temp_stop.setEnabled(True)
        else:
            # Habilitar controles manuales si estamos en vacío
            is_vacuum = (getattr(self.win.ui, "MenuPrincipal_btn_main_vacuum", None) and self.win.ui.MenuPrincipal_btn_main_vacuum.text() == "Main Vacuum Off")

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