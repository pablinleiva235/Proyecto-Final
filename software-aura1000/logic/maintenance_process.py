# logic/maintenance_process.py

from PyQt5 import QtWidgets 
from config.digital_signals import ACTIVE, INACTIVE

def init(win):
    """
    Inicializa las conexiones de los botones del Menú Principal (Mantenimiento).
    """
    # Desconectamos señales previas de manera segura para evitar ejecuciones duplicadas
    buttons = [
        win.ui.MenuPrincipal_btn_enable_driver,
        win.ui.MenuPrincipal_btn_open_door,
        win.ui.MenuPrincipal_btn_soft_vacuum,
        win.ui.MenuPrincipal_btn_main_vacuum,
        win.ui.MenuPrincipal_btn_vent_chamber
    ]
    for btn in buttons:
        try:
            btn.clicked.disconnect()
        except TypeError:
            pass

    # Conectamos las señales a las funciones de lógica localizadas en este archivo
    win.ui.MenuPrincipal_btn_enable_driver.clicked.connect(lambda: toggle_drivers(win))
    win.ui.MenuPrincipal_btn_open_door.clicked.connect(lambda: toggle_door(win))
    win.ui.MenuPrincipal_btn_soft_vacuum.clicked.connect(lambda: toggle_soft_vacuum(win))
    win.ui.MenuPrincipal_btn_main_vacuum.clicked.connect(lambda: toggle_main_vacuum(win))
    win.ui.MenuPrincipal_btn_vent_chamber.clicked.connect(lambda: vent_chamber(win))


def toggle_drivers(win):
    """
    Controla la habilitación y deshabilitación de los drivers de la placa DIO.
    """
    btn = win.ui.MenuPrincipal_btn_enable_driver
    
    if btn.text() == "Habilitar Drivers":
        win.hw.digital_set("DRIVER_ENABLE", ACTIVE)
        btn.setText("Deshabilitar Drivers")
        btn.setStyleSheet("background-color: #f44336; color: white;")
    else:
        win.hw.digital_set("DRIVER_ENABLE", INACTIVE)
        btn.setText("Habilitar Drivers")
        btn.setStyleSheet("")


def toggle_door(win):
    """
    Controla la apertura y el cierre seguro de la puerta de la cámara.
    """
    btn = win.ui.MenuPrincipal_btn_open_door
    
    if btn.text() == "Abrir Puerta":
        # Secuenciación segura de señales para el solenoide/pistón de la puerta
        win.hw.digital_set("DOOR_CLOSE_CMD", INACTIVE)
        win.hw.digital_set("DOOR_OPEN_CMD", ACTIVE)
        btn.setText("Cerrar Puerta")
        btn.setStyleSheet("background-color: #f44336; color: white;")
    else:
        win.hw.digital_set("DOOR_OPEN_CMD", INACTIVE)
        win.hw.digital_set("DOOR_CLOSE_CMD", ACTIVE)
        btn.setText("Abrir Puerta")
        btn.setStyleSheet("")


def toggle_soft_vacuum(win):
    """
    Controla la habilitación y deshabilitación de la válvula neumática de soft vacuum.
    Bloquea el apagado si el vacío principal (Main Vacuum) sigue encendido.
    """
    btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
    btn_main = win.ui.MenuPrincipal_btn_main_vacuum
    btn_door = win.ui.MenuPrincipal_btn_open_door
    
    if btn_soft.text() == "Soft Vacuum On":
        # Encendido: Bloqueamos inmediatamente la apertura de la puerta
        win.hw.digital_set("SOFT_START_CONTROL", ACTIVE)
        btn_soft.setText("Soft Vacuum Off")
        btn_soft.setStyleSheet("background-color: #f44336; color: white;")
        
        btn_door.setEnabled(False)  # <-- BLOQUEO DE SEGURIDAD
    else:
        # Intento de Apagado: Validamos condición de seguridad
        if btn_main.text() == "Main Vacuum Off":
            QtWidgets.QMessageBox.warning(
                win, 
                "Secuencia Inválida", 
                "No se puede apagar Soft Vacuum mientras Main Vacuum esté encendido.\nApague primero el vacío principal.",
                QtWidgets.QMessageBox.Ok
            )
            return
            
        # Si Main Vacuum está apagado, permitimos el cierre seguro
        win.hw.digital_set("SOFT_START_CONTROL", INACTIVE)
        btn_soft.setText("Soft Vacuum On")
        btn_soft.setStyleSheet("")


def toggle_main_vacuum(win):
    """
    Controla la habilitación y deshabilitación de la válvula de vacío principal,
    permitiendo la acción SOLO si Soft Vacuum está activo.
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
        
        btn_door.setEnabled(False)  # <-- BLOQUEO DE SEGURIDAD
    else:
        win.hw.digital_set("MAIN_VACUUM_CONTROL", INACTIVE)
        btn_main.setText("Main Vacuum On")
        btn_main.setStyleSheet("")


def vent_chamber(win):
    """
    Controla el inicio y la cancelación manual del proceso de venteo de la cámara.
    """
    btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
    btn_soft = win.ui.MenuPrincipal_btn_soft_vacuum
    btn_main = win.ui.MenuPrincipal_btn_main_vacuum

    # 1. INTERBLOQUEOS DE SEGURIDAD (Solo para cuando se quiere arrancar el venteo)
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
        
        # Bloqueamos los otros controles para que no hagan desastres en el medio
        btn_soft.setEnabled(False)
        btn_main.setEnabled(False)
        win.ui.MenuPrincipal_btn_open_door.setEnabled(False)
        
    else:
        # =====================================================================
        # CANCELACIÓN MANUAL (Si vuelven a presionar "Venteando...")
        # =====================================================================
        win.hw.digital_set("VENT_VALVE_CONTROL", INACTIVE)
        
        btn_vent.setText("Vent Chamber")
        btn_vent.setStyleSheet("")
        
        # Devolvemos el control normal a los botones
        btn_soft.setEnabled(True)
        btn_main.setEnabled(True)
        win.ui.MenuPrincipal_btn_open_door.setEnabled(True)
        print("Venteo cancelado manualmente por el operario.")


def finish_vent_sequence(win):
    """
    Se ejecuta automáticamente por timer X segundos después de detectar ATM.
    Cierra la válvula de venteo de forma segura y habilita la apertura de puerta.
    """
    btn_vent = win.ui.MenuPrincipal_btn_vent_chamber
    
    # MEJORA DE SEGURIDAD: Si el operario canceló a mano durante los 4s de espera,
    # el texto ya no dirá "Presión ATM alcanzada...". Si es el caso, ignoramos el timeout.
    if btn_vent.text() != "Presión ATM alcanzada...":
        return

    # 1. Apagamos físicamente la válvula de venteo
    win.hw.digital_set("VENT_VALVE_CONTROL", INACTIVE)
    
    # 2. Restauramos el botón de venteo a su estado inicial
    btn_vent.setText("Vent Chamber")
    btn_vent.setStyleSheet("")
    
    # 3. Rehabilitamos el resto de los botones para el vacío
    win.ui.MenuPrincipal_btn_soft_vacuum.setEnabled(True)
    win.ui.MenuPrincipal_btn_main_vacuum.setEnabled(True)
    
    # 4. HABILITACIÓN SEGURA DE LA PUERTA
    win.ui.MenuPrincipal_btn_open_door.setEnabled(True)
    
    print("Secuencia de venteo finalizada con éxito. Cámara segura para apertura.")
    