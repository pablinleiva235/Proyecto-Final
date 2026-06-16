# logic/pre_encendido.py
from config.digital_signals import ACTIVE

def iniciar_interfaz_pre_encendido(win):
    """Configura el estado visual inicial del Pre-Encendido"""
    win.ui.stackedWidget.setCurrentWidget(win.ui.PreEncendido)
    win.ui.PreEncendido_progressBar.hide()
    win.startup_progress = 0

def ejecutar_secuencia_startup(win):
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
        
    win.timer_manager.timers['startup'].timeout.connect(lambda: avanzar_barra_progreso(win))
    win.timer_manager.timers['startup'].start(100)

def avanzar_barra_progreso(win):
    """Callback del timer de startup (cada 100ms)"""
    win.startup_progress += 1
    win.ui.PreEncendido_progressBar.setValue(win.startup_progress)
    
    # 100 pasos * 100ms = 10 segundos
    if win.startup_progress >= 100:
        win.timer_manager.timers['startup'].stop()
        
        # Le ordena a la ventana cambiar al estado MAIN_MENU
        from services.system_state import SystemState
        win.change_state(SystemState.MAIN_MENU)