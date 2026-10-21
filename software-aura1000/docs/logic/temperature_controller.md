# `temperature_controller.py`

El módulo `temperature_controller.py` tiene la clase `TempController` con metodos integrados en el Menu Principal de la UI en la seccion de lamparas para poder ajustar un setpoint de temperatura al ejecutar un proceso manual, posterior al ajuste de presion y previo al encendido de plasma. La idea es generar una rampa de subida hasta el setpoint con las 3 lamparas, y luego dejar solamente encendida la lampara central controlando la misma mediante histeresis para lograr mantener la temperatura lo mas estable posible durante el proceso

---

## <span style="color: #4CAF50;">Estructura de la Clase `TempController`</span>

??? note "Constructor y Parámetros del Lazo: `__init__(self, main_window)`"
    Almacena las referencias de la interfaz de usuario (`ui`), abstracción de hardware (`hw`) y ventana principal (`win`). Define los rangos válidos de receta (130 °C a 190 °C), los umbrales de histéresis (7°C), el tamaño del filtro de mediana móvil (11 muestras), y configura el temporizador dedicado (`temp_timer`) a un intervalo de sondeo de 100 ms.

    ```python
    def __init__(self, main_window):
        self.win = main_window
        self.hw = main_window.hw
        self.ui = main_window.ui

        # Parámetros del Lazo de Control
        self.target_temp = 0.0  # Setpoint (°C)
        self.auto_control_enabled = False

        # Rangos permitidos de receta
        self.MIN_TEMP_SETPOINT = 130.0
        self.MAX_TEMP_SETPOINT = 190.0

        # Parámetros del Control por Histéresis (°C)
        self.HYSTERESIS_LOW = 7.0   # Encender L2 si T <= target - 7.0 °C
        self.HYSTERESIS_HIGH = 7.0  # Apagar L2 si T >= target + 7.0 °C

        # Filtro de mediana móvil para suavizar lectura de termocupla
        self._temp_buffer = []
        self._TEMP_BUFFER_SIZE = 11  # Mediana de las últimas 11 lecturas (1.1s)

        # Estado interno de la Rampa Inicial
        self.in_preheat_ramp = False
        self.waiting_first_dip = False

        # Umbral para cambio de estrategia de rango (Bajo: 130-160 °C, Alto: 160-190 °C)
        self.HIGH_TEMP_CUTOFF = 160.0

        # Parámetros de Asistencia de Lámparas 1 y 3 para caída crítica
        self.ASSIST_DELTA = 10.0  # °C por debajo del setpoint para disparar auxilio
        self.ASSIST_PULSE_TIME_MS = 250  # Pulso corto (250 ms) para evitar sobrepicos bruscos

        # Listas para graficar temperatura en función del tiempo
        self._log_time = []      # timestamps en segundos
        self._log_temp = []      # temperatura medida en °C
        self._log_setpoint = []  # setpoint objetivo
        self._log_start_time = None

        # Timer dedicado al sondeo del lazo y evaluación de la histéresis (100 ms)
        self.temp_timer = QtCore.QTimer()
        self.temp_timer.timeout.connect(self._update_temperature_loop)
        self.TIMER_INTERVAL_MS = 100

        # Conectar botones de la UI
        self._connect_ui_signals()
    ```

??? note "Conexión de Señales con la UI: `_connect_ui_signals(self)`"
    Enlaza los eventos de clic de los botones de encendido (`MenuPrincipal_btn_temp_set`) y detención (`MenuPrincipal_btn_temp_stop`) de la interfaz de usuario con sus respectivos métodos controladores.

    ```python
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
    ```

---

## <span style="color: #4CAF50;">Inicio y Parada del Lazo de Control</span>

??? note "Handler de Validación de Setpoint: `on_start_auto_control(self)`"
    Captura el valor ingresado en la interfaz de usuario, valida que sea un número flotante dentro de los límites seguros configurados (`MIN_TEMP_SETPOINT` a `MAX_TEMP_SETPOINT`) y gatilla el inicio del control automático o despliega una advertencia en pantalla (`QMessageBox`).

    ```python
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
    ```

??? note "Arranque del Lazo y Rampa Inicial: `start_auto_control(self, target_temp)`"
    Registra el setpoint objetivo, la temperatura inicial de la cámara (`start_temp`) para aplicar la corrección por precalentamiento, enciende las 3 lámparas al 100% para la rampa de velocidad, bloquea los botones manuales en la GUI mediante interlocks, reinicia los arreglos de logueo y arranca el temporizador `temp_timer` cada 100 ms.

    ```python
    def start_auto_control(self, target_temp: float):
        """Inicia la rampa con las 3 lámparas y activa el temporizador del lazo."""
        self.target_temp = target_temp
        self.auto_control_enabled = True
        self.in_preheat_ramp = True
        self._temp_buffer = []

        # Capturar la temperatura inicial real de la cámara
        initial_temp = getattr(self.win, "last_chamber_temp", 35.0)
        self.start_temp = initial_temp if initial_temp is not None else 35.0

        print(f"[TEMP] Lazo por Histéresis ACTIVADO. Setpoint: {self.target_temp:.1f} °C")

        # 1. Rampa Inicial: Encendemos Lámparas 1, 2 y 3 juntas
        self.hw.digital_set("LAMP1_ON_CMD", ACTIVE)
        self.hw.digital_set("LAMP2_ON_CMD", ACTIVE)
        self.hw.digital_set("LAMP3_ON_CMD", ACTIVE)
        self.win.state_lamps13_pulsing = False
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
    ```

??? note "Apagado de Seguridad y Generación de Gráfico: `stop_auto_control(self)`"
    Rutina de apagado seguro que desactiva el lazo automático, detiene el temporizador, fuerce la desconexión inmediata de todas las señales de lámparas (`INACTIVE`), libera los controles interactivos de la interfaz de usuario y dispara la generación del gráfico de desempeño térmico.

    ```python
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
    ```

---

## <span style="color: #4CAF50;">Lazo Cerrado y Algoritmo de Control</span>

??? note "Evaluación del Lazo de Control: `_update_temperature_loop(self)`"
    Corazón del controlador que se ejecuta periódicamente cada 100 ms:

    * **Filtrado de Mediana Móvil**: Aplica `statistics.median` sobre las últimas 11 muestras para eliminar picos de ruido e interferencias electromagnéticas (RF/ADC).
    * **Fase Rampa Inicial**: Calcula un offset dinámico (`ramp_offset`) combinando la temperatura objetivo y la compensación por cámara precalentada (`start_temp`). Al superar el umbral, apaga L1 y L3, retiene L2 encendida y activa la bandera `waiting_first_dip`.
    * **Amortiguación Post-Rampa**: Mantiene L2 activa en la cresta del sobrepico hasta que la temperatura se enfría y cruza por debajo del límite superior (`high_threshold`), liberando el control a la histéresis.
    * **Pulso de Asistencia L1+L3**: En la zona de alta temperatura (160°C), si la temperatura cae 10°C por debajo del setpoint, dispara un pulso auxiliar corto (250 ms) con las lámparas externas.
    * **Histéresis Estándar**: Conmuta la lámpara central L2 encendiéndola cuando T_filt <= T_set - 7°C y apagándola cuando T_filt >= T_set + 7°C.

    ```python
    def _update_temperature_loop(self):
        if not self.auto_control_enabled:
            return

        current_temp = getattr(self.win, "last_chamber_temp", None)
        if current_temp is None:
            return

        # 1. Filtro de Mediana Móvil
        self._temp_buffer.append(current_temp)
        if len(self._temp_buffer) > self._TEMP_BUFFER_SIZE:
            self._temp_buffer.pop(0)
        filtered_temp = statistics.median(self._temp_buffer)

        # Registro de datos para el gráfico
        if self._log_start_time is not None:
            elapsed = time.time() - self._log_start_time
            self._log_time.append(elapsed)
            self._log_temp.append(filtered_temp)
            self._log_setpoint.append(self.target_temp)

        # 2. FASE DE RAMPA INICIAL (3 Lámparas al 100%)
        if self.in_preheat_ramp:
            # A) Offset base según setpoint objetivo
            if self.target_temp <= self.HIGH_TEMP_CUTOFF:
                base_offset = 5.0 + 0.15 * (self.target_temp - self.MIN_TEMP_SETPOINT)
            else:
                base_offset = 5.0 + 0.15 * (self.target_temp - self.HIGH_TEMP_CUTOFF)

            start_correction = max(0.0, 0.15 * (self.start_temp - 35.0))
            ramp_offset = base_offset + start_correction
            preheat_threshold = self.target_temp - ramp_offset

            if filtered_temp >= preheat_threshold:
                self.in_preheat_ramp = False

                print(
                    f"[TEMP] Rampa completada ({filtered_temp:.1f} °C). "
                    f"Apagando L1 y L3. Manteniendo L2 encendida hasta caer a high_threshold (Offset: {ramp_offset:.1f} °C)."
                )
                self.hw.digital_set("LAMP1_ON_CMD", INACTIVE)
                self.hw.digital_set("LAMP3_ON_CMD", INACTIVE)
                self.hw.digital_set("LAMP2_ON_CMD", ACTIVE)

                self.win.state_lamps13_pulsing = False
                self.win.lamp2_on = True
                self.waiting_first_dip = True  # Retiene L2 encendida hasta que T <= target + HYSTERESIS_HIGH

            return

        # 3. FASE DE MANTENIMIENTO
        low_threshold = self.target_temp - self.HYSTERESIS_LOW
        high_threshold = self.target_temp + self.HYSTERESIS_HIGH

        # ── A. AMORTIGUACIÓN POST-RAMPA PARA RANGO ALTO ──
        # Mantiene L2 encendida en la cresta del sobrepico hasta que T cae por debajo de high_threshold
        if self.waiting_first_dip:
            if filtered_temp <= high_threshold:
                print(f"[TEMP] Caída post-rampa detectada ({filtered_temp:.1f} °C <= {high_threshold:.1f} °C). Histéresis liberada.")
                self.waiting_first_dip = False
            else:
                return  # Retiene L2 encendida omitiendo la evaluación de apagado

        # ── B. PULSO DE ASISTENCIA L1+L3 (SOLO PARA RANGO ALTO >= 160.0 °C) ──
        assist_threshold = self.target_temp - self.ASSIST_DELTA  # ej. target - 10.0 °C

        if (self.target_temp >= self.HIGH_TEMP_CUTOFF and filtered_temp <= assist_threshold and not self.win.state_lamps13_pulsing):
            print(f"[TEMP] Caída crítica en alta temperatura ({filtered_temp:.1f} °C). Disparando pulso L1+L3.")
            self.hw.digital_set("LAMP1_ON_CMD", ACTIVE)
            self.hw.digital_set("LAMP3_ON_CMD", ACTIVE)
            self.win.state_lamps13_pulsing = True
            QtCore.QTimer.singleShot(250, self._stop_assist_pulse)

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
    ```

??? note "Corte de Pulso Auxiliar: `_stop_assist_pulse(self)`"
    Callback ejecutado mediante un `QTimer.singleShot` al finalizar los 250 ms del pulso de asistencia, apagando nuevamente las lámparas externas L1 y L3 sin alterar el estado actual de la lámpara central L2.

    ```python
    def _stop_assist_pulse(self):
        """Apaga el pulso de auxilio de las lámparas externas."""
        if self.auto_control_enabled:
            self.hw.digital_set("LAMP1_ON_CMD", INACTIVE)
            self.hw.digital_set("LAMP3_ON_CMD", INACTIVE)
            self.win.state_lamps13_pulsing = False
            print("[TEMP] Pulso de asistencia L1+L3 completado.")
    ```

---

## <span style="color: #4CAF50;">Reportes Gráficos e Interlocks de Interfaz</span>

??? note "Generación y Guardado de Gráficos: `_generate_temperature_plot(self)`"
    Construye con `matplotlib` una gráfica temporal mostrando la temperatura filtrada medida, la curva de setpoint y las líneas de puntos representando la banda muerta de histéresis. Guarda el archivo `.png` resultante dentro del directorio `logic/logs/` etiquetado con la fecha y hora exacta.

    ```python
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

        # Banda muerta de histéresis
        ax.axhline(self.target_temp + self.HYSTERESIS_HIGH,
                   color="orange", linewidth=0.8,
                   linestyle=":", label=f"Banda Muerta (±{self.HYSTERESIS_HIGH} °C)")
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
    ```

??? note "Gestión de Interlocks de UI: `_update_ui_interlocks(self, running)`"
    Mantiene la exclusión mutua entre el control automático de temperatura y la operación manual de lámparas. Deshabilita las entradas manuales mientras el lazo automático esté en marcha y las restaura al finalizar únicamente si la cámara se encuentra en condiciones seguras de vacío.

    ```python
    def _update_ui_interlocks(self, running: bool):
        """Maneja la exclusión mutua entre el control automático y los botones manuales de lámparas."""
        btn_l13 = getattr(self.ui, "MenuPrincipal_btn_outerLamps", None)
        btn_l2 = getattr(self.ui, "MenuPrincipal_btn_centralLamp", None)
        entry_l13 = getattr(self.ui, "MenuPrincipal_outerLamps_pulseTime", None)

        entry_temp = getattr(self.ui, "MenuPrincipal_temp_setpoint", None)
        btn_temp_set = getattr(self.ui, "MenuPrincipal_btn_temp_set", None)
        btn_temp_stop = getattr(self.ui, "MenuPrincipal_btn_temp_stop", None)

        if running:
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
    ```