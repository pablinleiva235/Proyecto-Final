# logic/pre_encendido.py
from config.digital_signals import ACTIVE
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
    
<<<<<<< Updated upstream
    # [DESCOMENTAR EN NOTEBOOK DE SALA]
    # win.hw.initialize_AD()  
=======
    # 3. Inicializa USB-2527
    #win.hw.initialize_AD()  
>>>>>>> Stashed changes
    
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

def update_progressBar(win):
    """Callback del timer de startup (cada 100ms)"""
<<<<<<< Updated upstream
    win.startup_progress += 1
    win.ui.PreEncendido_progressBar.setValue(win.startup_progress)
    
    # 100 pasos * 100ms = 10 segundos
    if win.startup_progress >= 100:
=======
    # 100% total / 300 ciclos = 1/3% por cada ciclo de 100ms
    win.startup_progress += 100.0 / 100.0  # incremento exacto (~0.333333)

    # setValue solo acepta int, casteamos la variable float
    win.ui.PreEncendido_progressBar.setValue(int(win.startup_progress))

    # Cuando llegue al 100% (transcurridos los 30s)
    if win.startup_progress >= 100.0:
        win.ui.PreEncendido_progressBar.setValue(100)
>>>>>>> Stashed changes
        win.timer_manager.timers['startup'].stop()
        win.change_state(systemState.MAIN_MENU)