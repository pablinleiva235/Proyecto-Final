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

        # Parámetros del Control por Histéresis (°C)
        self.HYSTERESIS_LOW = 5.0  # Encender L2 si T <= target - 5.0 °C
        self.HYSTERESIS_HIGH = 5.0  # Apagar L2 si T >= target + 5.0 °C

        # Filtro de media móvil para suavizar lectura de termocupla
        self._temp_buffer = []
        self._TEMP_BUFFER_SIZE = 5  # Promedio de las últimas 5 lecturas (500ms)

        # Estado interno de la Rampa Inicial
        self.in_preheat_ramp = False
        self.waiting_first_dip = False  # Bandera de amortiguación post-rampa

        # Parámetros de Asistencia de Lámparas 1 y 3 para alta temperatura
        self.ASSIST_DELTA = 10.0  # °C por debajo del setpoint para disparar auxilio
        self.ASSIST_PULSE_TIME_MS = 350  # Pulso corto (350 ms) para evitar sobrepicos bruscos

        # Listas para graficar temperatura en función del tiempo
        self._log_time = []  # timestamps en segundos
        self._log_temp = []  # temperatura medida en °C
        self._log_setpoint = []  # setpoint objetivo
        self._log_start_time = None

        # Timer dedicado al sondeo del lazo y evaluación de la histéresis (100 ms)
        self.temp_timer = QtCore.QTimer()
        self.temp_timer.timeout.connect(self._update_temperature_loop)
        self.TIMER_INTERVAL_MS = 100

        # Conectar botones de la UI
        self._connect_ui_signals()

    def _connect_ui_signals(self):
        """Conecta los botones del Menú de Temperatura a los handlers."""
        if hasattr(self.ui, "MenuPrincipal_btn_temp_set"):
            self.ui.MenuPrincipal_btn_temp_set.clicked.connect(
                self.on_start_auto_control
            )
        if hasattr(self.ui, "MenuPrincipal_btn_temp_stop"):
            self.ui.MenuPrincipal_btn_temp_stop.clicked.connect(
                self.stop_auto_control
            )

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

        # Banda muerta
        ax.axhline(self.target_temp + self.HYSTERESIS_HIGH,
                color="orange", linewidth=0.8,
                linestyle=":", label=f"Deadband (±{self.HYSTERESIS_HIGH} Torr)")
        ax.axhline(self.target_temp - self.HYSTERESIS_LOW,
                color="orange", linewidth=0.8, linestyle=":")

        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Temperatura (°C)")
        ax.set_title(f"Control de Temperatura (Histéresis) — Setpoint: {self.target_temp:.1f} °C")
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
            text_val = (self.ui.MenuPrincipal_temp_setpoint.text().replace(",", "."))
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
        """Inicia la rampa con las 3 lámparas y activa el temporizador del lazo."""
        self.target_temp = target_temp
        self.auto_control_enabled = True
        self.in_preheat_ramp = True
        self._temp_buffer = []

        print(f"[TEMP] Lazo por Histéresis ACTIVADO. Setpoint: {self.target_temp:.1f} °C")

        # 1. Rampa Inicial: Encendemos Lámparas 1, 2 y 3 juntas
        self.hw.digital_set("LAMP1_ON_CMD", ACTIVE)
        self.hw.digital_set("LAMP2_ON_CMD", ACTIVE)
        self.hw.digital_set("LAMP3_ON_CMD", ACTIVE)
        self.win.state_lamps13_pulsing = True
        self.win.lamp2_on = True

        # 2. Bloquear controles manuales de UI
        self._update_ui_interlocks(running=True)

        # 3. Reiniciar búferes de logueo
        self._log_time = []
        self._log_temp = []
        self._log_setpoint = []
        self._log_start_time = time.time()

        # 4. Arrancar timer del lazo de control (100 ms)
        self.temp_timer.start(self.TIMER_INTERVAL_MS)

    def stop_auto_control(self):
        """Apaga el lazo automático, desactiva comandos y libera la UI."""
        print("[TEMP] Lazo de Temperatura DESACTIVADO.")
        self.auto_control_enabled = False
        self.in_preheat_ramp = False
        self.waiting_first_dip = False

        if self.temp_timer.isActive():
            self.temp_timer.stop()

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
    #                   LAZO CERRADO Y CONTROL POR HISTÉRESIS
    # =============================================================================
    def _update_temperature_loop(self):
        """Monitorea la temperatura y conmuta la Lámpara Central (SSR2) según histéresis."""
        if not self.auto_control_enabled:
            return

        # 1. Lectura de temperatura actual, que se guarda en last_chamber_temp en la funcion de lectura de termocupla de analog_update
        current_temp = getattr(self.win, "last_chamber_temp", None)
        if current_temp is None:
            return

        # 2. Filtro de media móvil para suavizar ruido de termocupla
        self._temp_buffer.append(current_temp)
        if len(self._temp_buffer) > self._TEMP_BUFFER_SIZE:
            self._temp_buffer.pop(0)
        filtered_temp = sum(self._temp_buffer) / len(self._temp_buffer)

        # ── REGISTRO DE DATOS PARA EL GRÁFICO (temperatura real) ──
        if self._log_start_time is not None:
            elapsed = time.time() - self._log_start_time
            self._log_time.append(elapsed)
            self._log_temp.append(current_temp)
            self._log_setpoint.append(self.target_temp)

        # 3. FASE DE RAMPA INICIAL (3 Lámparas al 100%)
        if self.in_preheat_ramp:
            preheat_threshold = self.target_temp * 1.01  # Corta al tocar el Setpoint (+1%)
            if filtered_temp >= preheat_threshold:
                print(
                    f"[TEMP] Rampa completada ({filtered_temp:.1f} °C). Apagando Lámparas 1 y 3. "
                    f"Pasando a Mantenimiento por Histéresis con L2."
                )
                self.hw.digital_set("LAMP1_ON_CMD", INACTIVE)
                self.hw.digital_set("LAMP3_ON_CMD", INACTIVE)
                self.win.state_lamps13_pulsing = False
                self.in_preheat_ramp = False
                self.waiting_first_dip = True # Flag para no apagar lampara 2 apenas termina la rampa  

                # L2 se mantiene activa para el inicio del mantenimiento
                self.hw.digital_set("LAMP2_ON_CMD", ACTIVE)
                self.win.lamp2_on = True
            else:
                return

        else:
            # 4. FASE DE MANTENIMIENTO: Histéresis + Amortiguación + Asistencia L1/L3
            low_threshold = self.target_temp - self.HYSTERESIS_LOW
            high_threshold = self.target_temp + self.HYSTERESIS_HIGH

            # ── A. AMORTIGUACIÓN POST-RAMPA INICIAL ──
            # Evita apagar L2 en la primera subida 
            if self.waiting_first_dip:
                if filtered_temp <= high_threshold:
                    print(f"[TEMP] Inercia de rampa disipada ({filtered_temp:.1f} °C). Histéresis activa.")
                    self.waiting_first_dip = False
                else:
                    return  # Mantiene L2 encendida tal como venía de la rampa

            # ── B. PULSO DE ASISTENCIA SIMÉTRICO L1 + L3 ──
            # Umbral de caída crítica (10 °C por debajo del setpoint)
            assist_threshold = self.target_temp - self.ASSIST_DELTA

            if (filtered_temp <= assist_threshold and not self.win.state_lamps13_pulsing):
                print(f"[TEMP] Caída crítica ({filtered_temp:.1f} °C). Disparando pulso de asistencia L1+L3.")
                self.hw.digital_set("LAMP1_ON_CMD", ACTIVE)
                self.hw.digital_set("LAMP3_ON_CMD", ACTIVE)
                self.win.state_lamps13_pulsing = True

                QtCore.QTimer.singleShot(self.ASSIST_PULSE_TIME_MS, self._stop_assist_pulse)

            # ── C. CONTROL POR HISTÉRESIS ESTÁNDAR (LÁMPARA CENTRAL L2) ──
            if filtered_temp <= low_threshold:
                if not self.win.lamp2_on:
                    self.hw.digital_set("LAMP2_ON_CMD", ACTIVE)
                    self.win.lamp2_on = True
                    print(f"[TEMP] T_filt={filtered_temp:.1f}°C <= {low_threshold:.1f}°C. Encendiendo L2.")

            elif filtered_temp >= high_threshold:
                if self.win.lamp2_on:
                    self.hw.digital_set("LAMP2_ON_CMD", INACTIVE)
                    self.win.lamp2_on = False
                    print(f"[TEMP] T_filt={filtered_temp:.1f}°C >= {high_threshold:.1f}°C. Apagando L2.")

    def _stop_assist_pulse(self):
        """Apaga el pulso de auxilio de las lámparas externas."""
        if self.auto_control_enabled:
            self.hw.digital_set("LAMP1_ON_CMD", INACTIVE)
            self.hw.digital_set("LAMP3_ON_CMD", INACTIVE)
            self.win.state_lamps13_pulsing = False
            print("[TEMP] Pulso de asistencia L1+L3 completado.")

            # Nota: Si filtered_temp está entre low_threshold y high_threshold,
            # no se ejecuta ningún digital_set y la Lámpara 2 mantiene su estado anterior.

    # =============================================================================
    #                           INTERLOCKS DE INTERFAZ
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