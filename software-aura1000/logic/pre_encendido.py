# logic/pre_encendido.py
from config.digital_signals import ACTIVE, INACTIVE
from services.system_state import systemState

def init(win):
    """Configura el estado visual inicial del Pre-Encendido"""
    win.ui.stackedWidget.setCurrentWidget(win.ui.PreEncendido)
    win.ui.PreEncendido_progressBar.hide()
    win.startup_progress = 0

def startup(win):
    """Lógica pesada al detectar el flanco de ON"""
    # 1. Activar retención en hardware digital
    win.hw.digital_set("POWER_ON", ACTIVE)

    # 2. Activa el filamento del magnetron, para asegurar que va a precalentar por 30s minimo
    win.hw.digital_set("FILAMENT_ENABLE", ACTIVE)
    
    # 3. Inicializa USB-2527
    win.hw.initialize_AD()  
    
    # 4. Modificar la interfaz gráfica directamente
    win.ui.PreEncendido_label2.setText("Iniciando, espere ...")
    win.ui.PreEncendido_progressBar.show()
    win.ui.PreEncendido_progressBar.setValue(0)
    win.startup_progress = 0
    
    # 5. Vincular y arrancar el timer de progress bar
    try:
        win.timer_manager.timers['startup'].timeout.disconnect()
    except TypeError:
        pass # No estaba conectado antes
        
    win.timer_manager.timers['startup'].timeout.connect(lambda: update_progressBar(win))
    win.timer_manager.timers['startup'].start(100)

def update_progressBar(win):
    """Callback del timer de startup (cada 100ms)"""
    win.startup_progress += 1
    win.ui.PreEncendido_progressBar.setValue(win.startup_progress)
    
    # 300 pasos * 100ms = 30 segundos
    if win.startup_progress >= 300:
        win.timer_manager.timers['startup'].stop()
        # Deja de accionar el SSR pues el contactor queda autoretenido
        win.hw.digital_set("POWER_ON", INACTIVE)
        win.change_state(systemState.MAIN_MENU)