# logic/maintenance_process.py

from PyQt5 import QtWidgets 
from config.digital_signals import ACTIVE, INACTIVE

# Constantes físicas de los MFCs (Unit UFC-1100A)
MFC1_MAX_SLM = 10.0   
MFC2_MAX_SLM = 1.0    

MFC1_MAX_VOLT = 10.0  
MFC2_MAX_VOLT = 1.0   

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
        win.ui.MenuPrincipal_btn_mfc2_set
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

    # ESTADO INICIAL DE SEGURIDAD: Deshabilitamos el panel de MFCs al arrancar
    set_mfc_controls_enabled(win, False)


# =============================================================================
# HELPER DE BLOQUEO/DESBLOQUEO DE CONTROLES MFC
# =============================================================================

def set_mfc_controls_enabled(win, enabled: bool):
    """
    Habilita o deshabilita en bloque las entradas y botones de control de los MFCs.
    Si se deshabilita (enabled=False), fuerza el cierre de válvulas y setpoints a 0V.
    """
    # 1. Habilitar/Deshabilitar widgets de interfaz
    win.ui.MenuPrincipal_btn_mfc1_open.setEnabled(enabled)
    win.ui.MenuPrincipal_mfc1_setpoint.setEnabled(enabled)
    win.ui.MenuPrincipal_btn_mfc1_set.setEnabled(enabled)

    win.ui.MenuPrincipal_btn_mfc2_open.setEnabled(enabled)
    win.ui.MenuPrincipal_mfc2_setpoint.setEnabled(enabled)
    win.ui.MenuPrincipal_btn_mfc2_set.setEnabled(enabled)

    # 2. Si se están deshabilitando por pérdida de vacío/venteo, apagamos salidas por hardware
    if not enabled:
        # Cierre físico de válvulas de inyección
        win.hw.digital_set("MFC1_OPEN", INACTIVE)
        win.hw.digital_set("MFC2_OPEN", INACTIVE)
        
        # Setpoints analógicos a cero
        win.hw.analog_write("MFC1_SETPOINT", 0.0)
        win.hw.analog_write("MFC2_SETPOINT", 0.0)

        # Reseteo estético de botones
        win.ui.MenuPrincipal_btn_mfc1_open.setText("Abrir Valvula MFC1: O2")
        win.ui.MenuPrincipal_btn_mfc1_open.setStyleSheet("")
        win.ui.MenuPrincipal_btn_mfc2_open.setText("Abrir Valvula MFC2: N2")
        win.ui.MenuPrincipal_btn_mfc2_open.setStyleSheet("")


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
    Bloquea el apagado si el vacío principal (Main Vacuum) sigue encendido.
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
        if btn_main.text() == "Main Vacuum Off":
            QtWidgets.QMessageBox.warning(
                win, 
                "Secuencia Inválida", 
                "No se puede apagar Soft Vacuum mientras Main Vacuum esté encendido.\nApague primero el vacío principal.",
                QtWidgets.QMessageBox.Ok
            )
            return
            
        win.hw.digital_set("SOFT_START_CONTROL", INACTIVE)
        btn_soft.setText("Soft Vacuum On")
        btn_soft.setStyleSheet("")


def toggle_main_vacuum(win):
    """
    Controla la habilitación y deshabilitación de la válvula de vacío principal.
    Habilita los controles de los MFCs al estar en vacío principal y los bloquea al apagarlo.
    """
    btn_main = win.ui.MenuPrincipal_btn_main_vacuum
    btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
    btn_door = win.ui.MenuPrincipal_btn_open_door
    
    if btn_soft.text() == "Soft Vacuum On":
        QtWidgets.QMessageBox.warning(
            win, 
            "Secuencia Inválida", 
            "No se puede activar Main Vacuum si Soft Vacuum no está encendido primero.",
            QtWidgets.QMessageBox.Ok
        )
        return

    if btn_main.text() == "Main Vacuum On":
        win.hw.digital_set("MAIN_VACUUM_CONTROL", ACTIVE)
        btn_main.setText("Main Vacuum Off")
        btn_main.setStyleSheet("background-color: #f44336; color: white;")
        btn_door.setEnabled(False)
        
        # <-- VACÍO ALCANZADO: HABILITAMOS CONTROLES DE MFCs
        set_mfc_controls_enabled(win, True)
    else:
        win.hw.digital_set("MAIN_VACUUM_CONTROL", INACTIVE)
        btn_main.setText("Main Vacuum On")
        btn_main.setStyleSheet("")
        
        # <-- SE CORTÓ VACÍO PRINCIPAL: DESHABILITAMOS CONTROLES DE MFCs
        set_mfc_controls_enabled(win, False)

# =============================================================================
# CONTROL DE VENTEO DE CAMARA
# =============================================================================

def vent_chamber(win):
    """ Controla el inicio y la cancelación manual del proceso de venteo de la cámara. """
    btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
    btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
    btn_main = win.ui.MenuPrincipal_btn_main_vacuum

    if btn_vent.text() == "Vent Chamber":
        if btn_soft.text() == "Soft Vacuum Off" or btn_main.text() == "Main Vacuum Off": 
            QtWidgets.QMessageBox.warning(
                win,
                "Secuencia Inválida",
                "No se puede ventear la cámara si Soft Vacuum o Main Vacuum están encendidos.\n"
                "Cierre las válvulas de vacío primero.",
                QtWidgets.QMessageBox.Ok
            )
            return

        # SI PASÓ LOS FILTROS: INICIA EL VENTEO
        win.hw.digital_set("VENT_VALVE_CONTROL", ACTIVE)
        btn_vent.setText("Venteando...")
        btn_vent.setStyleSheet("background-color: #2ec4b6; color: black; font-weight: bold;")
        
        # Bloqueamos resto de controles y aseguramos MFCs en estado seguro
        btn_soft.setEnabled(False)
        btn_main.setEnabled(False)
        win.ui.MenuPrincipal_btn_open_door.setEnabled(False)
        set_mfc_controls_enabled(win, False)  # <-- SEGURIDAD MFC EN VENTEO
        
    else:
        # CANCELACIÓN MANUAL
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
    set_mfc_controls_enabled(win, False)
    
    print("Secuencia de venteo finalizada con éxito. Cámara segura para apertura.")

# =============================================================================
# CONTROL DE VÁLVULAS SOLENOIDES DE GAS (MFC OPEN / CLOSE)
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


# =============================================================================
# CONTROL DE CONSIGNA DE CAUDAL (SETPOINTS ANALÓGICOS)
# =============================================================================

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