# logic/maintenance_process.py

from PyQt5 import QtWidgets 
from PyQt5.QtCore import QEventLoop, QTimer
from config.digital_signals import ACTIVE, INACTIVE

# Constantes físicas de los MFCs (Unit UFC-1100A)
MFC1_MAX_SLM = 10.0   
MFC2_MAX_SLM = 1.0    

MFC1_MAX_VOLT = 10.0  
MFC2_MAX_VOLT = 1.0

# =============================================================================
# PAUSA TEMPORAL PARA PULSO DE ENCENDIDO DE LAMPS 1 Y 3
# =============================================================================

def qt_sleep(ms: int):
    """Pausa no bloqueante para la interfaz de PyQt."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec_()

# =============================================================================
# INICIALIZACION
# =============================================================================

def init(win):
    """
    Inicializa las conexiones de los botones del Menú Principal (Mantenimiento).
    """
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
        win.ui.MenuPrincipal_btn_centralLamp
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

    # ESTADO INICIAL DE SEGURIDAD: Deshabilitamos el panel de MFCs al arrancar
    set_mfc_lamps_controls_enabled(win, False)


# =============================================================================
# HELPER DE BLOQUEO/DESBLOQUEO DE CONTROLES MFC
# =============================================================================

def set_mfc_lamps_controls_enabled(win, enabled: bool):
    """
    Habilita o deshabilita en bloque las entradas y botones de control
    de los MFCs y del Sistema de Lámparas.
    Si se deshabilita (enabled=False), fuerza el cierre de válvulas,
    setpoints a 0V y apagado de comandos de lámparas.
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
    # 2. Habilitar/Deshabilitar widgets de interfaz (Lámparas)
    # -------------------------------------------------------------------------
    win.ui.MenuPrincipal_btn_outerLamps.setEnabled(enabled) 
    win.ui.MenuPrincipal_btn_centralLamp.setEnabled(enabled)

    # -------------------------------------------------------------------------
    # 3. Si se deshabilitan por pérdida de vacío / venteo:
    # -------------------------------------------------------------------------
    if not enabled:
        # A. Cierre físico de válvulas de inyección y setpoints de MFCs
        win.hw.digital_set("MFC1_OPEN", INACTIVE)
        win.hw.digital_set("MFC2_OPEN", INACTIVE)
        win.hw.analog_write("MFC1_SETPOINT", 0.0)
        win.hw.analog_write("MFC2_SETPOINT", 0.0)

        # Reseteo estético de botones de MFCs
        win.ui.MenuPrincipal_btn_mfc1_open.setText("Abrir Valvula MFC1: O2")
        win.ui.MenuPrincipal_btn_mfc1_open.setStyleSheet("")
        win.ui.MenuPrincipal_btn_mfc2_open.setText("Abrir Valvula MFC2: N2")
        win.ui.MenuPrincipal_btn_mfc2_open.setStyleSheet("")

        # B. Apagado físico de comandos de Lámparas
        win.hw.digital_set("LAMP1_ON_CMD", INACTIVE)  # Reposo del monoestable
        win.hw.digital_set("LAMP3_ON_CMD", INACTIVE)  # Reposo del monoestable
        win.hw.digital_set("LAMP2_ON_CMD", INACTIVE)  # Lámpara 2 apagada

        # Reseteo estético del botón de Lámpara 2
        win.ui.MenuPrincipal_btn_centralLamp.setText("Lamp 2 On")
        win.ui.MenuPrincipal_btn_centralLamp.setStyleSheet("")


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
    
    if btn.text() == "Abrir Puerta":
        win.hw.digital_set("DOOR_CLOSE_CMD", INACTIVE)
        win.hw.digital_set("DOOR_OPEN_CMD", ACTIVE)
        btn.setText("Cerrar Puerta")
        btn.setStyleSheet("background-color: #f44336; color: white;")
    else:
        win.hw.digital_set("DOOR_OPEN_CMD", INACTIVE)
        win.hw.digital_set("DOOR_CLOSE_CMD", ACTIVE)
        btn.setText("Abrir Puerta")
        btn.setStyleSheet("")

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
        
        # Habilita la puerta solo si Main Vacuum tampoco está activo
        if btn_main.text() == "Main Vacuum On":
            btn_door.setEnabled(True)

def toggle_main_vacuum(win):
    """
    Controla la activación de Main Vacuum.
    Al encenderlo, apaga automáticamente Soft Vacuum según el manual del equipo.
    """
    btn_main = win.ui.MenuPrincipal_btn_main_vacuum
    btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
    btn_door = win.ui.MenuPrincipal_btn_open_door
    
    # 1. Validación de prerrequisito
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
        
        # <-- APAGADO AUTOMÁTICO DE SOFT VACUUM
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

# =============================================================================
# CONTROL DE VENTEO DE CAMARA
# =============================================================================

def vent_chamber(win):
    """ Controla el inicio y la cancelación manual del proceso de venteo. """
    btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
    btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
    btn_main = win.ui.MenuPrincipal_btn_main_vacuum

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
        win.ui.MenuPrincipal_btn_open_door.setEnabled(True)
        print("Venteo cancelado manualmente por el operario.")

def finish_vent_sequence(win):
    """ Se ejecuta automáticamente por timer X segundos después de detectar ATM. """
    btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
    
    if btn_vent.text() != "Presión ATM alcanzada...":
        return

    win.hw.digital_set("VENT_VALVE_CONTROL", INACTIVE)
    btn_vent.setText("Vent Chamber")
    btn_vent.setStyleSheet("")
    
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
    btn = win.ui.MenuPrincipal_btn_mfc1_open
    if btn.text() == "Abrir Valvula MFC1: O2":
        win.hw.digital_set("MFC1_OPEN", ACTIVE)
        btn.setText("Cerrar Valvula MFC1: O2")
        btn.setStyleSheet("background-color: #f44336; color: white;")
    else:
        win.hw.digital_set("MFC1_OPEN", INACTIVE)
        win.hw.analog_write("MFC1_SETPOINT", 0.0)
        btn.setText("Abrir Valvula MFC1: O2")
        btn.setStyleSheet("")

def toggle_mfc2_valve(win):
    """ Habilita / Deshabilita la válvula de corte de N2 (MFC2) """
    btn = win.ui.MenuPrincipal_btn_mfc2_open
    if btn.text() == "Abrir Valvula MFC2: N2":
        win.hw.digital_set("MFC2_OPEN", ACTIVE)
        btn.setText("Cerrar Valvula MFC2: N2")
        btn.setStyleSheet("background-color: #f44336; color: white;")
    else:
        win.hw.digital_set("MFC2_OPEN", INACTIVE)
        win.hw.analog_write("MFC2_SETPOINT", 0.0)
        btn.setText("Abrir Valvula MFC2: N2")
        btn.setStyleSheet("")

def set_mfc1_flow(win):
    """ Lee el QLineEdit, valida el valor e ingresa la tensión a la DAQ para O2 """
    text_val = win.ui.MenuPrincipal_mfc1_setpoint.text().replace(',', '.')
    btn_set = win.ui.MenuPrincipal_btn_mfc1_set
    try:
        slm_target = float(text_val)
        if 0.0 <= slm_target <= MFC1_MAX_SLM:
            voltage = (slm_target / MFC1_MAX_SLM) * MFC1_MAX_VOLT
            win.hw.analog_write("MFC1_SETPOINT", voltage)
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
    """
    Envía la señal de activación (ACTIVE) a las lámparas 1 y 3 para disparar 
    el monoestable y vuelve a poner la línea en reposo (INACTIVE).
    """
    try:
        # 1. Pulso de activación (ACTIVE)
        win.hw.digital_set("LAMP1_ON_CMD", ACTIVE)
        win.hw.digital_set("LAMP3_ON_CMD", ACTIVE)
        
        # 2. Mantener el pulso unos milisegundos para asegurar el trigger
        qt_sleep(15)

        # 3. Retorno al estado de reposo (INACTIVE)
        win.hw.digital_set("LAMP1_ON_CMD", INACTIVE)
        win.hw.digital_set("LAMP3_ON_CMD", INACTIVE)

        print("[INFO] Pulso enviado a Lámparas 1 y 3 (Monoestable disparado).")

    except Exception as e:
        print(f"[ERROR] Fallo al enviar pulso a Lámparas 1 y 3: {e}")

def toggle_lamp_2(win):
    """
    Controla el encendido y apagado de la Lámpara 2 (Central) mediante un estado ON/OFF.
    """
    btn = win.ui.MenuPrincipal_btn_centralLamp  

    if btn.text() == "Lamp 2 On":
        win.hw.digital_set("LAMP2_ON_CMD", ACTIVE)
        btn.setText("Lamp 2 Off")
        btn.setStyleSheet("background-color: #ff9800; color: black; font-weight: bold;")
        print("[INFO] Lámpara 2 (Central) Encendida.")
    else:
        win.hw.digital_set("LAMP2_ON_CMD", INACTIVE)
        btn.setText("Lamp 2 On")
        btn.setStyleSheet("")
        print("[INFO] Lámpara 2 (Central) Apagada.")