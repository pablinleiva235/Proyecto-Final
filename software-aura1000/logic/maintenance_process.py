# logic/maintenance_process.py
import time
from PyQt5 import QtWidgets 
from PyQt5.QtCore import QEventLoop, QTimer
from config.digital_signals import ACTIVE, INACTIVE

# Constantes físicas de los MFCs (Unit UFC-1100A)
MFC1_MAX_SLM = 10.0   
MFC2_MAX_SLM = 1.0    

MFC1_MAX_VOLT = 10.0  
MFC2_MAX_VOLT = 1.0

# =============================================================================
# HELPERS DE SEGURIDAD Y ESTADO DE VENTEO
# =============================================================================

def check_active_power(win) -> bool:
    """Comprueba si hay alguna lámpara o el plasma activados."""
    l13_active = win.state_lamps13_pulsing
    l2_active = win.ui.MenuPrincipal_btn_centralLamp.text() == "Lamp 2 Off"
    rf_active = win.ui.MenuPrincipal_btn_plasma.text() == "Plasma Off"
    return l13_active or l2_active or rf_active


def update_vent_button_state(win):
    """
    Habilita el botón de venteo SOLO si no hay sistemas térmicos/RF encendidos
    y ambas válvulas de vacío (Soft y Main) se encuentran cerradas.
    """
    if check_active_power(win):
        win.ui.MenuPrincipal_btn_vent_chamber.setEnabled(False)
        return

    soft_off = win.ui.MenuPrincipal_btn_soft_vacuum.text() == "Soft Vacuum On"
    main_off = win.ui.MenuPrincipal_btn_main_vacuum.text() == "Main Vacuum On"

    if soft_off and main_off:
        win.ui.MenuPrincipal_btn_vent_chamber.setEnabled(True)
    else:
        win.ui.MenuPrincipal_btn_vent_chamber.setEnabled(False)

def set_throttle_pressure_controls_enabled(win, enabled: bool):
    """Habilita o deshabilita las entradas y botones de control de presión de la Throttle."""
    if hasattr(win.ui, "ThrottleMenu_pressure_set"):
        win.ui.ThrottleMenu_pressure_set.setEnabled(enabled)
        win.ui.ThrottleMenu_pressure_stop.setEnabled(enabled)
        win.ui.ThrottleMenu_pressure_entry.setEnabled(enabled)

# =============================================================================
# INICIALIZACION
# =============================================================================

def init(win):
    """
    Inicializa las conexiones de los botones del Menú Principal (Mantenimiento).
    """

    # Flag para el encendido de lamparas 1 y 3 que usara luego el chequeo de si el pulsador de venteo se puede habilitar
    win.state_lamps13_pulsing = False

    # Desconexión de seguridad previa...
    buttons = [
        win.ui.MenuPrincipal_btn_enable_driver,
        win.ui.MenuPrincipal_btn_open_door,
        win.ui.MenuPrincipal_btn_soft_vacuum,
        win.ui.MenuPrincipal_btn_main_vacuum,
        win.ui.MenuPrincipal_btn_vent_chamber,
        win.ui.MenuPrincipal_btn_mfc1_open,
        win.ui.MenuPrincipal_btn_mfc2_open,
        win.ui.MenuPrincipal_btn_mfc1_set,
        win.ui.MenuPrincipal_btn_mfc2_set,
        win.ui.MenuPrincipal_btn_outerLamps,
        win.ui.MenuPrincipal_btn_centralLamp,
        win.ui.MenuPrincipal_btn_plasma
    ]
    for btn in buttons:
        try:
            btn.clicked.disconnect()
        except (TypeError, AttributeError):
            pass

    # Conexiones de push buttons a metodos
    win.ui.MenuPrincipal_btn_enable_driver.clicked.connect(lambda: toggle_drivers(win))
    win.ui.MenuPrincipal_btn_open_door.clicked.connect(lambda: toggle_door(win))
    win.ui.MenuPrincipal_btn_soft_vacuum.clicked.connect(lambda: toggle_soft_vacuum(win))
    win.ui.MenuPrincipal_btn_main_vacuum.clicked.connect(lambda: toggle_main_vacuum(win))
    win.ui.MenuPrincipal_btn_vent_chamber.clicked.connect(lambda: vent_chamber(win))
    win.ui.MenuPrincipal_btn_mfc1_open.clicked.connect(lambda: toggle_mfc1_valve(win))
    win.ui.MenuPrincipal_btn_mfc2_open.clicked.connect(lambda: toggle_mfc2_valve(win))
    win.ui.MenuPrincipal_btn_mfc1_set.clicked.connect(lambda: set_mfc1_flow(win))
    win.ui.MenuPrincipal_btn_mfc2_set.clicked.connect(lambda: set_mfc2_flow(win))
    win.ui.MenuPrincipal_btn_outerLamps.clicked.connect(lambda: trigger_lamps_1_3(win))
    win.ui.MenuPrincipal_btn_centralLamp.clicked.connect(lambda: toggle_lamp_2(win))
    win.ui.MenuPrincipal_btn_plasma.clicked.connect(lambda: toggle_plasma(win))

    # ESTADO INICIAL DE SEGURIDAD: Deshabilitamos el panel de MFCs y lamparas al arrancar
    set_mfc_lamps_controls_enabled(win, False)

# =============================================================================
# HELPER DE BLOQUEO/DESBLOQUEO DE CONTROLES MFC
# =============================================================================

def set_mfc_lamps_controls_enabled(win, enabled: bool):
    """
    Habilita o deshabilita en bloque las entradas y botones de control
    de los MFCs y del Sistema de Lámparas.
    Si se deshabilita (enabled=False), fuerza el cierre de válvulas,
    setpoints a 0V y apagado de comandos de lámparas y plasma.
    """
    # -------------------------------------------------------------------------
    # 1. Habilitar/Deshabilitar widgets de interfaz (MFCs)
    # -------------------------------------------------------------------------
    win.ui.MenuPrincipal_btn_mfc1_open.setEnabled(enabled)
    win.ui.MenuPrincipal_mfc1_setpoint.setEnabled(enabled)
    win.ui.MenuPrincipal_btn_mfc1_set.setEnabled(enabled)

    win.ui.MenuPrincipal_btn_mfc2_open.setEnabled(enabled)
    win.ui.MenuPrincipal_mfc2_setpoint.setEnabled(enabled)
    win.ui.MenuPrincipal_btn_mfc2_set.setEnabled(enabled)

    # -------------------------------------------------------------------------
    # 2. Habilitar/Deshabilitar widgets de interfaz (Lámparas y Plasma)
    # -------------------------------------------------------------------------
    win.ui.MenuPrincipal_btn_outerLamps.setEnabled(enabled) 
    win.ui.MenuPrincipal_btn_centralLamp.setEnabled(enabled)
    win.ui.MenuPrincipal_outerLamps_pulseTime.setEnabled(enabled)
    win.ui.MenuPrincipal_btn_plasma.setEnabled(enabled)

    # -------------------------------------------------------------------------
    # 3. Deshabilitar control de Presión (Menú Throttle)
    # -------------------------------------------------------------------------
    set_throttle_pressure_controls_enabled(win, enabled)

    # -------------------------------------------------------------------------
    # 3. Si se deshabilitan por pérdida de vacío / venteo:
    # -------------------------------------------------------------------------
    if not enabled:
        win.state_lamps13_pulsing = False
        # A. Cierre físico de válvulas de inyección y setpoints de MFCs
        win.hw.digital_set("MFC1_OPEN", INACTIVE)
        win.hw.digital_set("MFC2_OPEN", INACTIVE)
        win.hw.analog_write("MFC1_SETPOINT", 0.0)
        win.hw.analog_write("MFC2_SETPOINT", 0.0)

        # Reseteo del texto de los QLineEdit a "0"
        win.ui.MenuPrincipal_mfc1_setpoint.setText("0")
        win.ui.MenuPrincipal_mfc2_setpoint.setText("0")

        # Reseteo estético de botones de MFCs
        win.ui.MenuPrincipal_btn_mfc1_open.setText("Abrir Valvula MFC1: O2")
        win.ui.MenuPrincipal_btn_mfc1_open.setStyleSheet("")
        win.ui.MenuPrincipal_btn_mfc2_open.setText("Abrir Valvula MFC2: N2")
        win.ui.MenuPrincipal_btn_mfc2_open.setStyleSheet("")

        # B. Apagado físico de comandos de Lámparas y RF Plasma
        win.hw.digital_set("LAMP1_ON_CMD", INACTIVE)  # Reposo del monoestable
        win.hw.digital_set("LAMP3_ON_CMD", INACTIVE)  # Reposo del monoestable
        win.hw.digital_set("LAMP2_ON_CMD", INACTIVE)  # Lámpara 2 apagada
        win.hw.digital_set("RF_ON_CMD", INACTIVE)     # RF Plasma apagado

        # limpiar flag y estilo del pulso de lámparas 1&3, por si el
        # apagado ocurre a mitad de un qt_sleep en trigger_lamps_1_3
        win.state_lamps13_pulsing = False
        win.ui.MenuPrincipal_btn_outerLamps.setStyleSheet("")

        # Reseteo estético del botón de Lámpara 2 y Plasma
        win.ui.MenuPrincipal_btn_centralLamp.setText("Lamp 2 On")
        win.ui.MenuPrincipal_btn_centralLamp.setStyleSheet("")

        win.ui.MenuPrincipal_btn_plasma.setText("Plasma On")
        win.ui.MenuPrincipal_btn_plasma.setStyleSheet("")

    update_vent_button_state(win)

# =============================================================================
# HABILITACION DE DRIVERS SN75436 DE LA AURA 1000 DIO
# =============================================================================

def toggle_drivers(win):
    """ Controla la habilitación y deshabilitación de los drivers de la placa DIO. """
    btn = win.ui.MenuPrincipal_btn_enable_driver
    
    if btn.text() == "Habilitar Drivers":
        win.hw.digital_set("DRIVER_ENABLE", ACTIVE)
        btn.setText("Deshabilitar Drivers")
        btn.setStyleSheet("background-color: #f44336; color: white;")
    else:
        win.hw.digital_set("DRIVER_ENABLE", INACTIVE)
        btn.setText("Habilitar Drivers")
        btn.setStyleSheet("")

# =============================================================================
# APERTURA/CIERRE DE PUERTA
# =============================================================================

def toggle_door(win):
    """ Controla la apertura y el cierre seguro de la puerta de la cámara. """
    btn = win.ui.MenuPrincipal_btn_open_door
    btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
    btn_main = win.ui.MenuPrincipal_btn_main_vacuum
    btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
    
    if btn.text() == "Abrir Puerta":
        win.hw.digital_set("DOOR_CLOSE_CMD", INACTIVE)
        win.hw.digital_set("DOOR_OPEN_CMD", ACTIVE)
        btn_soft.setEnabled(False)
        btn_main.setEnabled(False)
        btn_vent.setEnabled(False)
        btn.setText("Cerrar Puerta")
        btn.setStyleSheet("background-color: #f44336; color: white;")
    else:
        win.hw.digital_set("DOOR_OPEN_CMD", INACTIVE)
        win.hw.digital_set("DOOR_CLOSE_CMD", ACTIVE)
        btn_soft.setEnabled(True)
        btn_main.setEnabled(True)
        btn.setText("Abrir Puerta")
        btn.setStyleSheet("")
        update_vent_button_state(win)

# =============================================================================
# CONTROL DE VALVULAS DE VACIO
# =============================================================================

def toggle_soft_vacuum(win):
    """
    Controla la habilitación y deshabilitación de la válvula neumática de soft vacuum.
    """
    btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
    btn_main = win.ui.MenuPrincipal_btn_main_vacuum
    btn_door = win.ui.MenuPrincipal_btn_open_door
    
    if btn_soft.text() == "Soft Vacuum On":
        win.hw.digital_set("SOFT_START_CONTROL", ACTIVE)
        btn_soft.setText("Soft Vacuum Off")
        btn_soft.setStyleSheet("background-color: #f44336; color: white;")
        btn_door.setEnabled(False)
    else:
        win.hw.digital_set("SOFT_START_CONTROL", INACTIVE)
        btn_soft.setText("Soft Vacuum On")
        btn_soft.setStyleSheet("")

    update_vent_button_state(win)

def toggle_main_vacuum(win):
    """
    Controla la activación de Main Vacuum.
    Al encenderlo, apaga automáticamente Soft Vacuum según el manual del equipo.
    """
    btn_main = win.ui.MenuPrincipal_btn_main_vacuum
    btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
    btn_door = win.ui.MenuPrincipal_btn_open_door
    
    # -------------------------------------------------------------------------
    # Impedir apagar el vacío si hay potencia activa
    # -------------------------------------------------------------------------
    is_vacuum_on = (btn_main.text() == "Main Vacuum Off")
    if is_vacuum_on and check_active_power(win):
        QtWidgets.QMessageBox.warning(
            win,
            "Acción Bloqueada por Seguridad",
            "No se puede apagar el Vacío Principal mientras haya Lámparas o Plasma activados.\n"
            "Apague todos los procesos térmicos y de RF primero.",
            QtWidgets.QMessageBox.Ok
        )
        return

    # 1. Validación de prerrequisito para ENCENDER
    if btn_soft.text() == "Soft Vacuum On" and btn_main.text() == "Main Vacuum On":
        QtWidgets.QMessageBox.warning(
            win, 
            "Secuencia Inválida", 
            "No se puede activar Main Vacuum si Soft Vacuum no está encendido primero.",
            QtWidgets.QMessageBox.Ok
        )
        return

    # 2. Encendido / Apagado de Main Vacuum
    if btn_main.text() == "Main Vacuum On":
        win.hw.digital_set("MAIN_VACUUM_CONTROL", ACTIVE)
        btn_main.setText("Main Vacuum Off")
        btn_main.setStyleSheet("background-color: #f44336; color: white;")
        btn_door.setEnabled(False)
        
        # Apagado automático de Soft Vacuum
        if btn_soft.text() == "Soft Vacuum Off":
            win.hw.digital_set("SOFT_START_CONTROL", INACTIVE)
            btn_soft.setText("Soft Vacuum On")
            btn_soft.setStyleSheet("")
            print("[INFO] Soft Vacuum cerrado automáticamente al pasar a Main Vacuum.")
        
        # Habilitación de MFCs al alcanzar vacío principal
        set_mfc_lamps_controls_enabled(win, True)
    else:
        win.hw.digital_set("MAIN_VACUUM_CONTROL", INACTIVE)
        btn_main.setText("Main Vacuum On")
        btn_main.setStyleSheet("")
        
        # Corte de vacío principal: deshabilitamos MFCs
        set_mfc_lamps_controls_enabled(win, False)

    update_vent_button_state(win)

# =============================================================================
# CONTROL DE VENTEO DE CAMARA
# =============================================================================

def vent_chamber(win):
    """ Controla el inicio y la cancelación manual del proceso de venteo. """
    btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
    btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
    btn_main = win.ui.MenuPrincipal_btn_main_vacuum

    if check_active_power(win):
        QtWidgets.QMessageBox.warning(
            win,
            "Secuencia Inválida",
            "No se puede ventear mientras haya Lámparas o Plasma activados.\n"
            "Apague todos los procesos térmicos y de RF primero.",
            QtWidgets.QMessageBox.Ok
        )
        return

    if btn_vent.text() == "Vent Chamber":
        # Verifica que NINGUNA de las dos válvulas de vacío esté abierta
        if btn_soft.text() == "Soft Vacuum Off" or btn_main.text() == "Main Vacuum Off": 
            QtWidgets.QMessageBox.warning(
                win,
                "Secuencia Inválida",
                "No se puede ventear la cámara si alguna válvula de vacío (Soft o Main) está abierta.\n"
                "Cierre las válvulas de vacío primero.",
                QtWidgets.QMessageBox.Ok
            )
            return

        # Inicio de venteo
        win.hw.digital_set("VENT_VALVE_CONTROL", ACTIVE)
        btn_vent.setText("Venteando...")
        btn_vent.setStyleSheet("background-color: #2ec4b6; color: black; font-weight: bold;")
        
        # Bloqueos de seguridad durante el venteo
        btn_soft.setEnabled(False)
        btn_main.setEnabled(False)
        win.ui.MenuPrincipal_btn_open_door.setEnabled(False)
        set_mfc_lamps_controls_enabled(win, False)
        
    else:
        # Cancelación manual
        win.hw.digital_set("VENT_VALVE_CONTROL", INACTIVE)
        btn_vent.setText("Vent Chamber")
        btn_vent.setStyleSheet("")
        
        btn_soft.setEnabled(True)
        btn_main.setEnabled(True)
        print("Venteo cancelado manualmente por el operario.")

def finish_vent_sequence(win):
    """ Se ejecuta automáticamente por timer X segundos después de detectar ATM. """
    btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
    
    if btn_vent.text() != "Presión ATM alcanzada...":
        return

    win.hw.digital_set("VENT_VALVE_CONTROL", INACTIVE)
    btn_vent.setText("Vent Chamber")
    btn_vent.setStyleSheet("")
    
    # Una vez venteado, vuelve a habilitar botones que habian sido deshabilitados en vacio
    win.ui.MenuPrincipal_btn_soft_vacuum.setEnabled(True)
    win.ui.MenuPrincipal_btn_main_vacuum.setEnabled(True)
    win.ui.MenuPrincipal_btn_open_door.setEnabled(True)
    
    # Mantenemos los MFCs deshabilitados hasta que vuelva a hacerse un vacío completo
    set_mfc_lamps_controls_enabled(win, False)
    
    print("Secuencia de venteo finalizada con éxito. Cámara segura para apertura.")

# =============================================================================
# CONTROL DE MFCs
# =============================================================================

def toggle_mfc1_valve(win):
    """ Habilita / Deshabilita la válvula de corte de O2 (MFC1) """
    btn_shutoff = win.ui.MenuPrincipal_btn_mfc1_open
    btn_set = win.ui.MenuPrincipal_btn_mfc1_set
    if btn_shutoff.text() == "Abrir Valvula MFC1: O2":
        win.hw.digital_set("MFC1_OPEN", ACTIVE)
        btn_shutoff.setText("Cerrar Valvula MFC1: O2")
        btn_shutoff.setStyleSheet("background-color: #f44336; color: white;")
    else:
        win.hw.analog_write("MFC1_SETPOINT", 0.0)
        win.hw.digital_set("MFC1_OPEN", INACTIVE)
        win.mfc1_target_slm = 0.0
        win.mfc1_flow_history.clear()
        btn_shutoff.setText("Abrir Valvula MFC1: O2")
        btn_shutoff.setStyleSheet("")
        btn_set.setStyleSheet("")

def toggle_mfc2_valve(win):
    """ Habilita / Deshabilita la válvula de corte de N2 (MFC2) """
    btn_shutoff = win.ui.MenuPrincipal_btn_mfc2_open
    btn_set = win.ui.MenuPrincipal_btn_mfc2_set
    if btn_shutoff.text() == "Abrir Valvula MFC2: N2":
        win.hw.digital_set("MFC2_OPEN", ACTIVE)
        btn_shutoff.setText("Cerrar Valvula MFC2: N2")
        btn_shutoff.setStyleSheet("background-color: #f44336; color: white;")
    else:
        win.hw.analog_write("MFC2_SETPOINT", 0.0)
        win.hw.digital_set("MFC2_OPEN", INACTIVE)
        win.mfc2_target_slm = 0.0
        win.mfc2_flow_history.clear()
        btn_shutoff.setText("Abrir Valvula MFC2: N2")
        btn_shutoff.setStyleSheet("")
        btn_set.setStyleSheet("")
        
def set_mfc1_flow(win):
    """ Lee el QLineEdit, valida el valor e ingresa la tensión a la DAQ para O2 """
    text_val = win.ui.MenuPrincipal_mfc1_setpoint.text().replace(',', '.')
    btn_set = win.ui.MenuPrincipal_btn_mfc1_set
    try:
        slm_target = float(text_val)
        if 0.0 <= slm_target <= MFC1_MAX_SLM:
            voltage = (slm_target / MFC1_MAX_SLM) * MFC1_MAX_VOLT
            win.hw.analog_write("MFC1_SETPOINT", voltage)
            # Guardar target y limpiar historial para nuevo promedio
            win.mfc1_target_slm = slm_target
            win.mfc1_flow_history.clear()
            print(f"[MFC1 O2] Setpoint cargado: {slm_target:.2f} SLM ({voltage:.2f} V)")
            btn_set.setStyleSheet("background-color: #4CAF50; color: white;")
        else:
            btn_set.setStyleSheet("background-color: #f44336; color: white;")
            QtWidgets.QMessageBox.warning(
                win, "Rango Inválido",
                f"El caudal de O2 debe estar entre 0.0 y {MFC1_MAX_SLM} SLM."
            )
    except ValueError:
        btn_set.setStyleSheet("background-color: #f44336; color: white;")
        QtWidgets.QMessageBox.warning(
            win, "Entrada Inválida",
            "Por favor ingrese un número válido para el setpoint de O2."
        )

def set_mfc2_flow(win):
    """ Lee el QLineEdit, valida el valor e ingresa la tensión a la DAQ para N2 """
    text_val = win.ui.MenuPrincipal_mfc2_setpoint.text().replace(',', '.')
    btn_set = win.ui.MenuPrincipal_btn_mfc2_set
    try:
        slm_target = float(text_val)
        if 0.0 <= slm_target <= MFC2_MAX_SLM:
            voltage = (slm_target / MFC2_MAX_SLM) * MFC2_MAX_VOLT
            win.hw.analog_write("MFC2_SETPOINT", voltage)
            # Guardar target y limpiar historial para nuevo promedio
            win.mfc2_target_slm = slm_target
            win.mfc2_flow_history.clear()
            print(f"[MFC2 N2] Setpoint cargado: {slm_target:.2f} SLM ({voltage:.2f} V)")
            btn_set.setStyleSheet("background-color: #4CAF50; color: white;")
        else:
            btn_set.setStyleSheet("background-color: #f44336; color: white;")
            QtWidgets.QMessageBox.warning(
                win, "Rango Inválido",
                f"El caudal de N2 debe estar entre 0.0 y {MFC2_MAX_SLM} SLM."
            )
    except ValueError:
        btn_set.setStyleSheet("background-color: #f44336; color: white;")
        QtWidgets.QMessageBox.warning(
            win, "Entrada Inválida",
            "Por favor ingrese un número válido para el setpoint de N2."
        )

# =============================================================================
# CONTROL DE ENCENDIDO DE LAMPARAS
# =============================================================================

def trigger_lamps_1_3(win):
    """Envía la señal de activación a las lámparas 1 y 3 durante el tiempo
    ingresado en el Text Entry (máx 28s). Usando QTimer asíncrono.
    """
    btn = win.ui.MenuPrincipal_btn_outerLamps
    input_field = win.ui.MenuPrincipal_outerLamps_pulseTime

    # 1. Obtener y validar el tiempo ingresado
    try:
        seconds = float(input_field.text().strip())
        if seconds <= 0 or seconds > 28:
            raise ValueError("Fuera de rango")
    except ValueError:
        print("[WARN] Tiempo de pulso inválido. Ingrese un valor entre 0 y 28 segundos.")
        return

    duration_ms = int(seconds * 1000)

    # 2. Bloquear UI del botón, marcar estado real y activar salidas
    win.state_lamps13_pulsing = True
    btn.setEnabled(False)
    btn.setStyleSheet("background-color: #ff9800; color: black; font-weight: bold;")
    update_vent_button_state(win)

    win.hw.digital_set("LAMP1_ON_CMD", ACTIVE)
    win.hw.digital_set("LAMP3_ON_CMD", ACTIVE)
    print(f"[INFO] Lámparas 1 y 3 ENCENDIDAS por {seconds} segundos.")

    # 3. Definir la función que se ejecutará AL FINALIZAR el tiempo
    def on_pulse_complete():
        # Si durante la espera se cortó el vacío o se deshabilitaron los controles,
        # 'state_lamps13_pulsing' ya habrá sido puesto a False en set_mfc_lamps_controls_enabled
        if not win.state_lamps13_pulsing:
            print("[INFO] El pulso de lámparas fue abortado por seguridad antes de tiempo.")
            return

        win.hw.digital_set("LAMP1_ON_CMD", INACTIVE)
        win.hw.digital_set("LAMP3_ON_CMD", INACTIVE)
        win.state_lamps13_pulsing = False
        btn.setStyleSheet("")
        print("[INFO] Lámparas 1 y 3 APAGADAS (Fin de pulso). Precalentamiento completo.")

        """# Habilita Plasma solo si el vacío principal se mantuvo encendido
        if win.ui.MenuPrincipal_btn_main_vacuum.text() == "Main Vacuum Off":
            win.ui.MenuPrincipal_btn_plasma.setEnabled(True)
        else:
            print("[WARN] Vacío no activo al finalizar el pulso; Plasma no habilitado.")
        """
        update_vent_button_state(win)

    # 4. Programar el apagado automático (sin congelar ni crear reentrancia)
    QTimer.singleShot(duration_ms, on_pulse_complete)

def toggle_lamp_2(win):
    """
    Controla el encendido y apagado de la Lámpara 2 (Central) mediante un estado ON/OFF.
    """
    btn = win.ui.MenuPrincipal_btn_centralLamp  

    if btn.text() == "Lamp 2 On":
        win.hw.digital_set("LAMP2_ON_CMD", ACTIVE)
        win.lamp2_on = True # Flag para la funcion de deteccion de fallas, que solamente detecta al estar activas
        btn.setText("Lamp 2 Off")
        btn.setStyleSheet("background-color: #ff9800; color: black; font-weight: bold;")
        print("[INFO] Lámpara 2 (Central) Encendida.")
    else:
        win.hw.digital_set("LAMP2_ON_CMD", INACTIVE)
        win.lamp2_on = False # Vuelvo el flag a False una vez apagada para que no detecte fallas
        btn.setText("Lamp 2 On")
        btn.setStyleSheet("")
        print("[INFO] Lámpara 2 (Central) Apagada.")

    update_vent_button_state(win)

# =============================================================================
# CONTROL DE ENCENDIDO DE PLASMA
# =============================================================================

def toggle_plasma(win):
    """Controla la señal RF_ON_CMD para encender y apagar la alta tensión del magnetrón."""
    btn = win.ui.MenuPrincipal_btn_plasma

    if btn.text() == "Plasma On":
        win.hw.digital_set("RF_ON_CMD", ACTIVE)
        win.rf_on = True
        win.rf_on_time = time.time()  # Marca de tiempo de encendido
        btn.setText("Plasma Off")
        btn.setStyleSheet("background-color: #ff9800; color: black; font-weight: bold;")
        print("[INFO] Plasma Encendido.")
    else:
        win.hw.digital_set("RF_ON_CMD", INACTIVE)
        win.rf_on = False
        btn.setText("Plasma On")
        btn.setStyleSheet("")
        print("[INFO] Plasma Apagado.")

        # Habilitar boton de Lámparas 1 y 3 solo si el Vacío Principal está activo
        if (win.ui.MenuPrincipal_btn_main_vacuum.text() == "Main Vacuum Off"):  # Estado encendido
            win.ui.MenuPrincipal_btn_outerLamps.setEnabled(True)

        update_vent_button_state(win)