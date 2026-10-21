# `throttle_test.py`

El módulo `throttle_test.py` tiene la clase ThrottleController con metodos integrados en el Menu Throttle de la UI para poder controlar la misma de forma manual, girando el motor paso a paso continuamente, en full o half step, en ambas direcciones, moverlo de a cantidad de pasos deseados y ajustar el setpoint de presion mediante el sistema de control

---

## <span style="color: #4CAF50;">Estructura de la Clase `ThrottleController`</span>

??? note "Constructor e Inicialización: `__init__(self, main_window)`"
    Almacena las referencias de la interfaz de usuario y del hardware. Vincula la generación de pulsos del motor directamente al temporizador `stepper_pulse` registrado en el gestor central de tiempo (`timer_manager`). Inicializa los parámetros de movimiento por pasos (Full/Half step), contadores de posición, frecuencias de trabajo `250HZ`, constantes de zona muerta `+-0.015Torr`, buffers de filtrado por mediana móvil para el sensor Baratron, e impone el enclavamiento inicial de seguridad para los controles de presión.

    ```python
    def __init__(self, main_window):
        self.win = main_window
        self.hw = main_window.hw
        self.ui = main_window.ui

        # Apuntamos directamente al timer en el manager central
        self.step_timer = main_window.timer_manager.timers["stepper_pulse"]
        self.step_state = INACTIVE
        self._closing = False      # True = Cierra, False = Abre
        self._is_half_step = False  # False = Full step, True = Half step

        # Variables para antirrebote en switches de límites
        self._closed_count = 0
        self._open_count   = 0
        self._DEBOUNCE_N   = 3

        # Contador de posición absoluta y control de ráfaga de pasos
        self.current_step = 0
        self._target_steps = 0
        self._step_mode = "CONTINUOUS"

        # Parámetros de Control de Presión 
        self.target_pressure = 0.0
        self.deadband = 0.015
        self.auto_control_enabled = False
        self.THROTTLE_STEP_FREQUENCY = 250
        self.SPEED_MS = int(1000 / self.THROTTLE_STEP_FREQUENCY / 2)
        self.MAX_PRESSURE_LIMIT = 3  # Torr

        # Buffer para filtro de mediana móvil (Baratron)
        self._pressure_buffer = []
        self._PRESSURE_BUFFER_SIZE = 7

        # Listas de registro de datos para graficación
        self._log_time     = []
        self._log_pressure = []
        self._log_setpoint = []
        self._log_start_time = None

        # Posición de reposo para evitar zona muerta
        self._rest_position_reached = False
        self.THROTTLE_REST_POSITION = 400

        self._connect_ui_signals()
        self._update_step_display()
    ```

??? note "Conexión de Señales e Interfaz: `_connect_ui_signals(self)`"
    Enlaza los eventos de clic de los botones del panel de control de la Throttle en la interfaz de usuario con sus respectivos métodos manejadores en la lógica de control. Aplica el bloqueo inicial de seguridad desactivando los controles de ajuste automático de presión al arrancar el módulo.

    ```python
    def _connect_ui_signals(self):
        """Conecta los botones del menú de la Throttle a sus manejadores internos."""
        self.ui.ThrottleMenu_btn_toggle_enable.clicked.connect(self.on_enable_toggled)
        self.ui.ThrottleMenu_btn_toggle_step.clicked.connect(self.on_step_toggled)
        self.ui.ThrottleMenu_btn_toggle_dir.clicked.connect(self.on_dir_toggled)
        self.ui.ThrottleMenu_btn_toggle_run.clicked.connect(self.on_run_toggled)
        self.ui.ThrottleMenu_step_set.clicked.connect(self.on_step_set_clicked)
        self.ui.ThrottleMenu_pressure_set.clicked.connect(self.on_start_auto_control)
        self.ui.ThrottleMenu_pressure_stop.clicked.connect(self.stop_auto_control)

        # Bloqueo de seguridad inicial al arrancar
        self.ui.ThrottleMenu_pressure_set.setEnabled(False)
        self.ui.ThrottleMenu_pressure_stop.setEnabled(False)
        self.ui.ThrottleMenu_pressure_entry.setEnabled(False)
    ```

---

## <span style="color: #4CAF50;">Helper de chequeo de Driver habilitado`</span>

??? note "Chequeo de Driver DRV8825 habilitado: `check_drivers_enabled(self)`"
    Chequea que el driver de la valvula throttle este habilitado

    ```python
    def check_drivers_enabled(self) -> bool:
        """Verifica si los drivers de la placa DIO están habilitados."""
        drivers_active = (self.ui.ThrottleMenu_btn_toggle_enable.text() == "Deshabilitar Driver")
        if not drivers_active:
            QMessageBox.warning(
                self.win,
                "Drivers Deshabilitados",
                "El driver de la valvula throttle esta deshabilitado.\n\n"
                "Presione 'Habilitar Driver' antes de operar con la Throttle.",
                QMessageBox.Ok
            )
        return drivers_active
    ```
---

## <span style="color: #4CAF50;">Secuencias de Calibración y Posicionamiento (*Homing*)</span>

??? note "Búsqueda del Límite de Apertura (*Homing* de Inicio): `home_on_startup(self)`"
    Establece la dirección del motor hacia apertura plena, activa la corriente en las bobinas del driver e inicia la marcha continua para buscar el switch de fin de carrera físico. Esta rutina se ejecuta al arrancar el software para referenciar la escala y calibrar el punto cero de conteo de pasos.

    ```python
    def home_on_startup(self):
        """Busca el límite físico de apertura al arrancar el software para calibrar el paso 0."""
        print("[THROTTLE] Iniciando secuencia de Homing...")
        
        self.set_direction(INACTIVE)  # Apertura
        self.set_enable(ACTIVE)       # Mantiene corriente en las bobinas
        self.set_half_step(INACTIVE)  # Full step para homing
        
        btn_enable = getattr(self.ui, "ThrottleMenu_btn_toggle_enable", None)
        if btn_enable:
            btn_enable.setText("Deshabilitar Driver")
            btn_enable.setStyleSheet("background-color: #f44336; color: white;")

        self.start_movement(self.SPEED_MS)
    ```

??? note "Posicionamiento en Zona de Reposo: `go_to_rest_position(self)`"
    Mueve la válvula a una posición prestablecida de reposo `400 pasos` desde la apertura total. Su objetivo es saltar la zona muerta mecánica previa a la restricción efectiva de flujo. Mientras se realiza el desplazamiento, despliega un cuadro de diálogo modal e ineludible (`QProgressDialog`) para notificar al usuario.

    ```python
    def go_to_rest_position(self):
        """Mueve la válvula a la posición de reposo para superar zona muerta."""
        if self.current_step == self.THROTTLE_REST_POSITION:
            print(f"[THROTTLE] Ya en posición de reposo ({self.THROTTLE_REST_POSITION} pasos). Sin movimiento.")
            return

        self._rest_dialog = QProgressDialog("Espere... Moviendo Throttle a posición inicial", None, 0, 0, self.win)
        self._rest_dialog.setWindowTitle("Posicionando Throttle")
        self._rest_dialog.setCancelButton(None)
        self._rest_dialog.setRange(0, 0)
        self._rest_dialog.setMinimumDuration(0)
        self._rest_dialog.show()

        if self.current_step < self.THROTTLE_REST_POSITION:
            steps_needed = self.THROTTLE_REST_POSITION - self.current_step
            self.set_direction(ACTIVE)    # Cerrar
            self.set_half_step(INACTIVE)  # Full step
            self.start_movement(self.SPEED_MS, steps=int(steps_needed))
        else:
            steps_needed = self.current_step - self.THROTTLE_REST_POSITION
            self.set_direction(INACTIVE)  # Abrir
            self.set_half_step(INACTIVE)  # Full step
            self.start_movement(self.SPEED_MS, steps=int(steps_needed))
    ```

---

## <span style="color: #4CAF50;">Control Automático de Presión en Lazo Cerrado</span>

??? note "Activación y Parada del Control Automático: `start_auto_control` y `stop_auto_control`"
    * **`start_auto_control(self, target_torr)`**: Asigna la consigna de presión deseada, habilita la bandera de lazo cerrado, asegura la alimentación del driver, aplica los enclavamientos de la UI e inicia el logueo de datos temporales.
    * **`stop_auto_control(self)`**: Desactiva la regulación automática, detiene el movimiento del motor, envía la válvula a su posición de reposo y genera automáticamente la gráfica de respuesta temporal en la carpeta `logic/logs`.

    ```python
    def start_auto_control(self, target_torr: float):
        """Activa la regulación automática con el setpoint ingresado."""
        self.target_pressure = max(0.0, target_torr)
        self.auto_control_enabled = True
        self.set_enable(ACTIVE)
        self._update_ui_interlocks(running=True)

        self._log_time     = []
        self._log_pressure = []
        self._log_setpoint = []
        self._log_start_time = time.time()

        print(f"[THROTTLE] Control de presión ACTIVADO. Target: {self.target_pressure:.3f} Torr")
        self.start_movement(self.SPEED_MS)  

    def stop_auto_control(self):
        """Desactiva la regulación automática y detiene el motor."""
        print("[THROTTLE] Control de presión DESACTIVADO manualmente.")
        self.stop_movement()
        self.go_to_rest_position()
        self._generate_pressure_plot()
    ```

??? note "Lazo de Control y Modulación Dinámica: `update_pressure_loop(self, current_pressure)`"
    Ejecuta el algoritmo de control adaptativo de presión en la cámara de vacío:
    
    * **Filtrado de Lectura**: Aplica un filtro de mediana móvil con un búfer de 7 muestras para erradicar el ruido o picos en la señal analógica del sensor Baratron.
    * **Evaluación de Banda Muerta**: Si el error error = self.target_pressure - filtered_pressure se encuentra dentro de la tolerancia de +-0.015 Torr, apaga temporalmente los pulsos del motor para evitar oscilaciones (*hunting*).
    * **Perfilado Adaptativo de Velocidad**: Escala de forma proporcional la frecuencia de paso y el tipo de resolución (Full Step / Half Step) según la magnitud del error, permitiendo aproximaciones rápidas a grandes desviaciones y ajustes de alta precisión (hasta 50 Hz en Half Step) al aproximarse al punto de consigna.

    ```python
    def update_pressure_loop(self, current_pressure: float):
        if not self.auto_control_enabled:
            return

        # 0. Filtro de Mediana Móvil
        if not hasattr(self, "_pressure_buffer"):
            self._pressure_buffer = []
        self._pressure_buffer.append(current_pressure)
        if len(self._pressure_buffer) > self._PRESSURE_BUFFER_SIZE:
            self._pressure_buffer.pop(0)
        filtered_pressure = statistics.median(self._pressure_buffer)
        error = self.target_pressure - filtered_pressure

        # Registrar lectura para generar gráfico
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
                print("[THROTTLE] Presión dentro de tolerancia. Motor pausado.")
            return

        # 2. Velocidad y modo según magnitud y signo del error
        if error > 0:
            if error > 0.3:
                speed_ms = self.SPEED_MS       # 250 Hz - Full Step
                use_half = False
            elif error > 0.15:
                speed_ms = self.SPEED_MS * 2   # 125 Hz - Full Step
                use_half = True
            elif error > 0.05:
                speed_ms = self.SPEED_MS * 3   # 83 Hz - Half Step
                use_half = True
            else:
                speed_ms = self.SPEED_MS * 5   # 50 Hz - Half Step
                use_half = True
        else:
            speed_ms = self.SPEED_MS * 5       # 50 Hz - Half Step (Apertura suave)
            use_half = True

        # 3. Transición de resolución de paso
        if use_half != self._is_half_step:
            was_active = self.step_timer.isActive()
            if was_active:
                self.step_timer.stop()
                self.hw.digital_set("STEPPER_STEP", INACTIVE)
            self.set_half_step(use_half)
            if was_active:
                self.step_timer.start(speed_ms)

        # 4. Asignación de sentido de giro
        should_close = error > 0
        if self._closing != should_close:
            self.set_direction(should_close)

        # 5. Modulación del temporizador
        if not self.step_timer.isActive():
            self.start_movement(speed_ms)
        elif self.step_timer.interval() != speed_ms:
            self.step_timer.setInterval(speed_ms)
    ```

??? note "Validación e Inicio de Lazo Automático: `on_start_auto_control(self)`"
    Manejador invocado al presionar el botón de consigna de presión en la interfaz. Compara la consigna deseada con la presión base actual del sistema (medida en tiempo real) e impone dos enclavamientos de seguridad: prohíbe *setpoints* inalcanzables (menores a la presión base en alto vacío) y bloquea valores superiores al límite máximo de presion de trabajo de 3.0 Torr.

    ```python
    def on_start_auto_control(self):
        """Handler del botón Ajustar Presión (ThrottleMenu_pressure_set)."""
        try:
            val_text = self.ui.ThrottleMenu_pressure_entry.text().strip()
            target = float(val_text)

            current_p = round(self.hw.analog_read("BARATRON"), 2)

            if target < current_p:
                QMessageBox.warning(
                    self.win,
                    "Setpoint Inalcanzable",
                    f"El setpoint ingresado ({target:.2f} Torr) es menor a la presión base actual ({current_p:.2f} Torr).\n\n"
                    "La Throttle Valve solo puede aumentar la presión restringiendo el flujo. "
                    "Elija un setpoint mayor a la presión actual o reduzca el caudal de los MFC.",
                    QMessageBox.Ok
                )
            elif target > self.MAX_PRESSURE_LIMIT:
                QMessageBox.warning(
                    self.win,
                    "Límite Excedido",
                    f"El setpoint ingresado ({target:.2f} Torr) supera el límite máximo de seguridad ({self.MAX_PRESSURE_LIMIT:.1f} Torr).",
                    QMessageBox.Ok
                )
            else:
                self.start_auto_control(target)

        except ValueError:
            QMessageBox.warning(
                self.win,
                "Entrada Inválida",
                "Ingrese un valor numérico válido para el setpoint de presión.",
                QMessageBox.Ok
            )
    ```

---

## <span style="color: #4CAF50;">Métodos de Hardware y Control Manual</span>

??? note "Control Digital de Señales de Salida: `set_enable`, `set_half_step` y `set_direction`"
    Métodos de abstracción de bajo nivel encargados de enviar las órdenes digitales correspondientes a las líneas físicas del driver del motor paso a paso (`STEPPER_OUTPUT_ENABLE`, `STEPPER_HALF_STEP` y `STEPPER_DIR`).

    ```python
    def set_enable(self, state: bool):
        self.hw.digital_set("STEPPER_OUTPUT_ENABLE", state)

    def set_half_step(self, use_half: bool):
        self._is_half_step = use_half
        self.hw.digital_set("STEPPER_HALF_STEP", use_half)

    def set_direction(self, close_direction: bool):
        self._closing = close_direction
        self.hw.digital_set("STEPPER_DIR", close_direction)
    ```

??? note "Gestión de Movimiento del Temporizador: `start_movement` y `stop_movement`"
    * **`start_movement(self, speed_ms, steps=0)`**: Inicia el temporizador `stepper_pulse`. Si se especifica `steps > 0`, configura el modo ráfaga (`BURST`), deteniendo el movimiento al alcanzar el conteo. Si `steps == 0`, opera en modo continuo (`CONTINUOUS`).
    * **`stop_movement(self)`**: Detiene el temporizador del motor paso a paso, fuerza la línea `STEPPER_STEP` al estado inactivo (`INACTIVE`), limpia la bandera de control automático y restablece la interfaz gráfica.

    ```python
    def start_movement(self, speed_ms: int, steps: int = 0):
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

            self._update_ui_interlocks(running=True)
            print(f"[THROTTLE] Movimiento INICIADO ({self._step_mode}) -> Timer activo cada {speed_ms} ms.")

    def stop_movement(self):
        self.step_timer.stop()
        self.step_state = INACTIVE
        self.hw.digital_set("STEPPER_STEP", INACTIVE)

        self._target_steps = 0
        self._step_mode = "CONTINUOUS"
        self.auto_control_enabled = False

        self._update_ui_interlocks(running=False)
        self.reset_run_button()

        print("[THROTTLE] Movimiento DETENIDO y pin STEP llevado a INACTIVE.")
    ```

??? note "Generación del Pulso Físico: `_toggle_step(self)`"
    Manejador conectado a la señal `.timeout` del temporizador de pasos (`stepper_pulse`). Verifica primero los estados de los límites físicos; de no estar bloqueado, conmuta de forma alternada la línea digital `STEPPER_STEP` entre `ACTIVE` e `INACTIVE`. Acumula o descuenta de la posición actual de forma fraccionaria (0.5 en Half Step, 1.0 en Full Step) y decrementa el contador en desplazamientos por ráfaga (*BURST*).

    ```python
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
                    print("[THROTTLE] Ráfaga inicial completada con éxito.")
                    if hasattr(self, "_rest_dialog") and self._rest_dialog is not None:
                        self._rest_dialog.close()
                        self._rest_dialog = None
                    if self.auto_control_enabled:
                        self._step_mode = "CONTINUOUS"
                    else:
                        self.stop_movement()
    ```

??? note "Actualización del Indicador de Pasos: `_update_step_display(self)`"
    Refresca el display numérico de tipo LCD (`ThrottleMenu_step_counter`) en la interfaz gráfica, mostrando la posición acumulada actual con resolución de un decimal.

    ```python
    def _update_step_display(self):
        """Actualiza el display LCD con la posición actual fijando 1 decimal."""
        if hasattr(self.ui, "ThrottleMenu_step_counter"):
            self.ui.ThrottleMenu_step_counter.display(f"{float(self.current_step):.1f}")
    ```

---

## <span style="color: #4CAF50;">Manejo de Interlocks y Handlers de la Interfaz Visual</span>

??? note "Gestión de Exclusión Mutua en la UI: `_update_ui_interlocks` y `update_vacuum_interlocks`"
    * **`_update_ui_interlocks(self, running)`**: Bloquea o habilita los controles manuales o automáticos según el estado actual de operación del motor (detenido, movimiento manual o regulación en lazo cerrado) para prevenir conflictos de comandos.
    * **`update_vacuum_interlocks(self)`**: Bloquea de forma obligatoria los campos de consigna de presión cuando la cámara se encuentra a presión atmosférica, habilitándolos únicamente al detectarse la condición de alto vacío (`is_in_vacuum`).

    ```python
    def _update_ui_interlocks(self, running: bool):
        btn_run = getattr(self.ui, "ThrottleMenu_btn_toggle_run", None)
        btn_step_set = getattr(self.ui, "ThrottleMenu_step_set", None)
        entry_step = getattr(self.ui, "ThrottleMenu_step_entry", None)

        p_entry = getattr(self.ui, "ThrottleMenu_pressure_entry", None)
        p_set   = getattr(self.ui, "ThrottleMenu_pressure_set", None)
        p_stop  = getattr(self.ui, "ThrottleMenu_pressure_stop", None)

        is_vacuum = getattr(self.win, "is_in_vacuum", False)

        if running:
            if self.auto_control_enabled:
                if btn_run:      btn_run.setEnabled(False)
                if btn_step_set: btn_step_set.setEnabled(False)
                if entry_step:   entry_step.setEnabled(False)
                if p_entry:      p_entry.setEnabled(False)
                if p_set:        p_set.setEnabled(False)
                if p_stop:       p_stop.setEnabled(True)
            else:
                if p_entry: p_entry.setEnabled(False)
                if p_set:   p_set.setEnabled(False)
                if p_stop:  p_stop.setEnabled(False)

                if self._step_mode == "CONTINUOUS":
                    if btn_step_set: btn_step_set.setEnabled(False)
                    if entry_step:   entry_step.setEnabled(False)
                elif self._step_mode == "BURST":
                    if btn_run:      btn_run.setEnabled(False)
                    if btn_step_set: btn_step_set.setEnabled(False)
                    if entry_step:   entry_step.setEnabled(False)
        else:
            if btn_run:      btn_run.setEnabled(True)
            if btn_step_set: btn_step_set.setEnabled(True)
            if entry_step:   entry_step.setEnabled(True)

            if is_vacuum:
                if p_entry: p_entry.setEnabled(True)
                if p_set:   p_set.setEnabled(True)
                if p_stop:  p_stop.setEnabled(False)
            else:
                if p_entry: p_entry.setEnabled(False)
                if p_set:   p_set.setEnabled(False)
                if p_stop:  p_stop.setEnabled(False)

    def update_vacuum_interlocks(self):
        """Habilita o deshabilita los controles de presión según si el sistema está en vacío o en atmósfera."""
        is_vacuum = getattr(self.win, "is_in_vacuum", False)

        p_entry = getattr(self.ui, "ThrottleMenu_pressure_entry", None)
        p_set   = getattr(self.ui, "ThrottleMenu_pressure_set", None)
        p_stop  = getattr(self.ui, "ThrottleMenu_pressure_stop", None)

        if is_vacuum:
            if not self.auto_control_enabled:
                if p_entry: p_entry.setEnabled(True)
                if p_set:   p_set.setEnabled(True)
                if p_stop:  p_stop.setEnabled(False)
        else:
            if p_entry: p_entry.setEnabled(False)
            if p_set:   p_set.setEnabled(False)
            if p_stop:  p_stop.setEnabled(False)
    ```

??? note "Handlers de Botones Manuales: `on_enable_toggled`, `on_step_toggled`, `on_dir_toggled`, `on_run_toggled` y `on_step_set_clicked`"
    Conjunto de métodos asociados a los botones de la interfaz gráfica para conmutar el estado del driver, la resolución de paso (Full/Half), la dirección de giro (Apertura/Cierre), el encendido/apagado manual del motor y el ajuste por número de pasos en ráfaga (validando un rango de 1 a 1400 pasos.

    ```python
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
        if not self.check_drivers_enabled():
            return  # Aborta la acción si los drivers están deshabilitados
        btn = self.ui.ThrottleMenu_btn_toggle_step
        if "Full Step" in btn.text():
            self.set_half_step(ACTIVE)
            btn.setText("Modo: Half Step")
        else:
            self.set_half_step(INACTIVE)
            btn.setText("Modo: Full Step")

    def on_dir_toggled(self):
        if not self.check_drivers_enabled():
            return  # Aborta la acción si los drivers están deshabilitados
        btn = self.ui.ThrottleMenu_btn_toggle_dir
        if "Apertura" in btn.text():
            self.set_direction(ACTIVE)
            btn.setText("Dirección: Cierre")
        else:
            self.set_direction(INACTIVE)
            btn.setText("Dirección: Apertura")

    def on_run_toggled(self):
        if not self.check_drivers_enabled():
            return  # Aborta la acción si los drivers están deshabilitados
        btn = self.ui.ThrottleMenu_btn_toggle_run
        if btn.text() == "Girar Motor":
            self._log_time     = []
            self._log_pressure = []
            self._log_setpoint = []
            self._log_start_time = time.time()
            self._is_logging = True
            dir_str = "Cierre" if self._closing else "Apertura"
            self._log_title = f"Movimiento Manual Throttle — Dirección: {dir_str}"

            self.start_movement(self.SPEED_MS)
            btn.setText("Detener Motor")
            btn.setStyleSheet("background-color: #ff9800; color: black; font-weight: bold;")
        else:
            self.stop_movement()

    def on_step_set_clicked(self):
        if not self.check_drivers_enabled():
            return  # Aborta la acción si los drivers están deshabilitados
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
        except ValueError:
            QMessageBox.warning(
                self.win,
                "Entrada Inválida",
                "Ingrese un valor numérico entero para los pasos.",
                QMessageBox.Ok,
            )

    def reset_run_button(self):
        btn = self.ui.ThrottleMenu_btn_toggle_run
        btn.setText("Girar Motor")
        btn.setStyleSheet("")
    ```

---

## <span style="color: #4CAF50;">Monitoreo de Sensores de Límite y Antirrebote</span>

??? note "Lectura y Filtrado por Software de Finales de Carrera: `update_limit_switch_status` y `_check_limits`"
    * **`is_fully_closed(self)` / `is_fully_open(self)`**: Consultan las líneas digitales de entrada física de los finales de carrera (`THROTTLE_CLOSED` y `THROTTLE_OPEN`).
    * **`_check_limits(self)`**: Verifica si la válvula alcanzó un fin de carrera confirmado en el sentido de movimiento actual. Al detectar apertura completa, fuerza la calibración del contador a 0 pasos y detiene la marcha.
    * **`update_limit_switch_status(self)`**: Función de sondeo continuo ejecutada periódicamente desde el lazo central de entrada/salida. Implementa un filtro antirrebote por software que exige N=3 lecturas consecutivas idénticas en los optoacopladores o switches mecánicos antes de confirmar el estado límite y actualizar las etiquetas visuales en la GUI.

    ```python
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

        # Antirrebote para Cierre
        if closed_raw:
            self._closed_count = min(self._closed_count + 1, self._DEBOUNCE_N)
        else:
            self._closed_count = max(self._closed_count - 1, 0)

        # Antirrebote para Apertura
        if open_raw:
            self._open_count = min(self._open_count + 1, self._DEBOUNCE_N)
        else:
            self._open_count = max(self._open_count - 1, 0)

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
            if hasattr(self, "_home_dialog") and self._home_dialog is not None:
                self._home_dialog.close()
                self._home_dialog = None
        else:
            lbl_open.setText("Abierta: —")
            lbl_open.setStyleSheet("")
    ```