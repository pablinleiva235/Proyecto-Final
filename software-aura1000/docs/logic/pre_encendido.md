# `pre_encendido.py`

El módulo `pre_encendido.py` encapsula la lógica secuencial y algorítmica de la fase inicial del equipo. Aislando las funciones de control del hilo de la interfaz de usuario, este módulo se encarga del enclavamiento eléctrico por software, la inicialización de periféricos analógicos y la gestión de la temporización crítica de 30 segundos necesaria para la estabilización del Gasonics Aura 1000, principalmente para el precalentado del filamento del magnetron

---

## <span style="color: #4CAF50;">Funciones del pre encendido</span>

??? note "Configuración del Entorno Inicial: `init(win)`"
    Se ejecuta de forma síncrona en el flanco de entrada al estado `PRE_ENCENDIDO`. Configura los parámetros iniciales de la pantalla, forzando la visualización de la solapa indexada correspondiente en el `stackedWidget`, ocultando de forma preventiva la barra de progreso y reseteando a cero el acumulador del ciclo de vida de la secuencia.

    ```python
    def init(win):
        """Configura el estado visual inicial del Pre-Encendido"""
        win.ui.stackedWidget.setCurrentWidget(win.ui.PreEncendido)
        win.ui.PreEncendido_progressBar.hide()
        win.startup_progress = 0
    ```

??? note "Orquestador de Arranque Físico y Tiempos: `startup(win)`"
    Es invocado inmediatamente después de que el lazo centralizado de I/O detecta el flanco de subida en el pulsador de marcha. Ejecuta de forma imperativa tres acciones críticas:
    
    1. Activa la retención eléctrica mediante el seteo digital de la línea `POWER_ON`.
    2. Modifica dinámicamente los widgets de texto e interfaz en la ventana.
    3. Protege la conexión del timer `startup` (limpiando conexiones previas mediante un bloque `try-except`), asocia la subrutina de incremento mediante una función `lambda` y arranca el temporizador con un intervalo periódico de **100 ms**.

    ```python
    def startup(win):
        """Lógica pesada al detectar el flanco de ON"""
        # 1. Activar retención en hardware digital
        win.hw.digital_set("POWER_ON", ACTIVE)
        
        # [DESCOMENTAR EN NOTEBOOK DE SALA]
        # win.hw.initialize_AD()  
        
        # 2. Modificar la interfaz gráfica directamente
        win.ui.PreEncendido_label2.setText("Iniciando, espere ...")
        win.ui.PreEncendido_progressBar.show()
        win.ui.PreEncendido_progressBar.setValue(0)
        win.startup_progress = 0
        
        # 3. Vincular y arrancar el timer que vive en el manager
        try:
            win.timer_manager.timers['startup'].timeout.disconnect()
        except TypeError:
            pass # No estaba conectado antes
            
        win.timer_manager.timers['startup'].timeout.connect(lambda: update_progressBar(win))
        win.timer_manager.timers['startup'].start(100)
    ```

??? note "Callback de la Barra de Progreso: `update_progressBar(win)`"
    Rutina cíclica acoplada al desbordamiento (timeout) del temporizador `startup` cada 100 ms. Incrementa linealmente la variable `startup_progress` reflejando el progreso físico en el widget visual. Al alcanzar el límite estricto de 30s que necesita el filamento para precalentar, detiene de forma definitiva el timer para liberar recursos del procesador e instruye a la ventana el avance hacia el estado `MAIN_MENU`. Ademas desenergiza el SSR de encendido ya que el contactor quedo autoretenido por su contacto auxiliar

    ```python
    # 300 pasos * 100ms = 30 segundos de delay de estabilización
    if win.startup_progress >= 300:
        win.timer_manager.timers['startup'].stop()
        # Deja de accionar el SSR pues el contactor queda autoretenido
        win.hw.digital_set("POWER_ON", INACTIVE)
        # Energiza el filamento del magnetron pasado los 30s (especificado en el datasheet)
        win.hw.digital_set("FILAMENT_ENABLE", ACTIVE)
        win.change_state(systemState.MAIN_MENU)
    ```