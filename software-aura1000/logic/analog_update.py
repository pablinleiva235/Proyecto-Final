# logic/analog_update.py
from PyQt5 import QtWidgets
from config.digital_signals import ACTIVE, INACTIVE

BARATRON_FULL_SCALE = 10

# =================================================================================
# MÉTODO HELPER PARA INDICADORES LED
# =================================================================================
def update_led_indicator(label_widget, state_active: bool, text_active: str, text_inactive: str):
    """Actualiza dinámicamente el estilo de un QLabel para simular un indicador LED."""
    if state_active:
        label_widget.setText(text_active)
        label_widget.setStyleSheet("""
            background-color: #2ec4b6; color: black; font-weight: bold; 
            border: 1px solid #0f625a; border-radius: 4px; padding: 4px;
        """)
    else:
        label_widget.setText(text_inactive)
        label_widget.setStyleSheet("""
            background-color: #e0e0e0; color: #757575; font-weight: bold; 
            border: 1px solid #9e9e9e; border-radius: 4px; padding: 4px;
        """)


# ===================================================================
# LECTURA DEL BARATRON Y ESTADO DEL ATM SWITCH
# ===================================================================
def update_pressure_display(win) -> bool:
    """Lee el Baratron y el ATM_SWITCH, actualiza la GUI y retorna el estado de ATM."""
    try:
        voltage = win.hw.analog_read("BARATRON")
        pressure_torr = max(0.0, voltage * (BARATRON_FULL_SCALE / 10.0))
        # Indicacion de presion en menu Mantenimiento
        win.ui.MenuPrincipal_chamber_pressure.display(f"{pressure_torr:.3f}")
        # Indicacion de presion en menu Throttle
        win.ui.ThrottleMenu_chamber_pressure.display(f"{pressure_torr:.3f}")
        # Llamada para ajuste de setpoint de throttle
        win.throttle.update_pressure_loop(pressure_torr)

        # Lectura del switch de presión atmosférica
        atm_active = win.hw.digital_read("ATM_SWITCH")
        update_led_indicator(
            win.ui.MenuPrincipal_lbl_status_atm,
            atm_active,
            "PRESION ATM",
            "VACIO / CAMARA",
        )
        return atm_active

    except Exception as e:
        print(f"[ERROR] Al actualizar la presión en la GUI: {e}")
        return False


# ===================================================================
# LECTURA DE TEMPERATURA DE OBLEA / CÁMARA
# ===================================================================
def update_temp_display(win):
    """Lee la termocupla de temperatura de la cámara y actualiza el QLCDNumber."""
    try:
        temp_c = win.hw.analog_read_temperature("CHAMBER_TEMP")

        if temp_c is not None:
            win.ui.MenuPrincipal_chamber_temp.display(f"{temp_c:.1f}")
        else:
            win.ui.MenuPrincipal_chamber_temp.display("---")
    except Exception as e:
        print(f"[ERROR] Error al leer la temperatura de la cámara: {e}")
        win.ui.MenuPrincipal_chamber_temp.display("ERR")


# ===================================================================================================
# LECTURA DE CAUDALES DE MFCs (O2 / N2) y METODOS EN CASO DE FALLA POR IRSE EL SETPOINT DE TOLERANCIA
# ===================================================================================================
def update_mfc_displays(win):
    """Lee el caudal real de los sensores analógicos MFC1_FLOW y MFC2_FLOW

    y actualiza los LCDs de la GUI.
    """
    try:
        # --- 1. Lectura de MFC1 (O2) ---
        v_mfc1 = win.hw.analog_read("MFC1_FLOW")
        slm_mfc1 = max(0.0, v_mfc1)
        win.ui.MenuPrincipal_mfc1_readout.display(f"{slm_mfc1:.2f}")
        win.mfc1_flow_history.append(slm_mfc1)  # Se agrega al buffer de 3s

        # --- 2. Lectura de MFC2 (N2) ---
        v_mfc2 = win.hw.analog_read("MFC2_FLOW")
        slm_mfc2 = max(0.0, v_mfc2)
        win.ui.MenuPrincipal_mfc2_readout.display(f"{slm_mfc2:.2f}")
        win.mfc2_flow_history.append(slm_mfc2)  # Se agrega al buffer de 3s

        # --- 3. Evaluación de seguridad de caudal ---
        _check_mfc_faults(win)

    except Exception as e:
        print(f"[ERROR] Error al leer flujo de MFCs: {e}")

def _check_mfc_faults(win):
    """Verifica si el promedio de lecturas de los últimos 3s difiere en más del 5% del target."""
    has_target_mfc1 = getattr(win, "mfc1_target_slm", 0.0) > 0
    has_target_mfc2 = getattr(win, "mfc2_target_slm", 0.0) > 0

    fault_detected = False
    failed_gases = []

    # 1. Evaluar MFC1 (Solo si hay target activo y el buffer acumuló los 3s)
    if (has_target_mfc1 and len(win.mfc1_flow_history) == win.MFC_WINDOW_SAMPLES):
        avg_mfc1 = sum(win.mfc1_flow_history) / len(win.mfc1_flow_history)
        deviation1 = (abs(avg_mfc1 - win.mfc1_target_slm) / win.mfc1_target_slm)
        if deviation1 > win.MFC1_FLOW_TOLERANCE_PCT:
            print(f"[WARN] MFC1 fuera de tolerancia! Target: {win.mfc1_target_slm}, Avg: {avg_mfc1:.2f}")
            fault_detected = True
            failed_gases.append("O2 (MFC1)")

    # 2. Evaluar MFC2 (Solo si hay target activo y el buffer acumuló los 3s)
    if (has_target_mfc2 and len(win.mfc2_flow_history) == win.MFC_WINDOW_SAMPLES):
        avg_mfc2 = sum(win.mfc2_flow_history) / len(win.mfc2_flow_history)
        deviation2 = (abs(avg_mfc2 - win.mfc2_target_slm) / win.mfc2_target_slm)
        if deviation2 > win.MFC2_FLOW_TOLERANCE_PCT:
            print(f"[WARN] MFC2 fuera de tolerancia! Target: {win.mfc2_target_slm}, Avg: {avg_mfc2:.2f}")
            fault_detected = True
            failed_gases.append("N2 (MFC2)")

    # 3. Disparar corte si falló o rehabilitar si el caudal es correcto
    if fault_detected:
        _trigger_mfc_safety_shutdown(win, failed_gases)
    else:
        if not getattr(win, "alarm_active", False):
            win.ui.MenuPrincipal_btn_plasma.setEnabled(True)
            win.ui.MenuPrincipal_btn_outerLamps.setEnabled(True)
            win.ui.MenuPrincipal_btn_centralLamp.setEnabled(True)

def _trigger_mfc_safety_shutdown(win, failed_gases):
    """Ejecuta las acciones de seguridad al detectar desvío de caudal."""
    # A. Deshabilitar botón de Plasma y lamparas
    win.ui.MenuPrincipal_btn_plasma.setEnabled(False)
    win.ui.MenuPrincipal_btn_outerLamps.setEnabled(False)
    win.ui.MenuPrincipal_btn_centralLamp.setEnabled(False)

    # B. Si el Plasma está encendido, apagarlo
    if getattr(win, "rf_on", False):
        win.hw.digital_set("RF_ON_CMD", INACTIVE)
        win.rf_on = False
        win.ui.MenuPrincipal_btn_plasma.setText("Plasma On")
        win.ui.MenuPrincipal_btn_plasma.setStyleSheet("")
        print("[CORTE DE SEGURIDAD] Plasma apaga por desviación en MFC.")

    # C. Apagar Lámparas 1 y 3 si están en pulso
    if getattr(win, "state_lamps13_pulsing", False):
        win.hw.digital_set("LAMP1_ON_CMD", INACTIVE)
        win.hw.digital_set("LAMP3_ON_CMD", INACTIVE)
        win.state_lamps13_pulsing = False
        win.ui.MenuPrincipal_btn_outerLamps.setEnabled(True)
        win.ui.MenuPrincipal_btn_outerLamps.setStyleSheet("")
        print("[CORTE DE SEGURIDAD] Lámparas 1 y 3 apagadas por desviación en MFC.")

    # D. Apagar Lámpara 2 si está encendida
    if getattr(win, "lamp2_on", False):
        win.hw.digital_set("LAMP2_ON_CMD", INACTIVE)
        win.lamp2_on = False
        win.ui.MenuPrincipal_btn_centralLamp.setText("Lamp 2 On")
        win.ui.MenuPrincipal_btn_centralLamp.setStyleSheet("")
        print("[CORTE DE SEGURIDAD] Lámpara 2 apagada por desviación en MFC.")

    # E. Cierre de seguridad y reseteo de MFC1 (O2)
    win.hw.digital_set("MFC1_OPEN", INACTIVE)
    win.hw.analog_write("MFC1_SETPOINT", 0.0)
    win.mfc1_target_slm = 0.0
    win.mfc1_flow_history.clear()
    win.ui.MenuPrincipal_btn_mfc1_open.setText("Abrir Valvula MFC1: O2")
    win.ui.MenuPrincipal_btn_mfc1_open.setStyleSheet("")
    win.ui.MenuPrincipal_btn_mfc1_set.setStyleSheet("")

    # F. Cierre de seguridad y reseteo de MFC2 (N2)
    win.hw.digital_set("MFC2_OPEN", INACTIVE)
    win.hw.analog_write("MFC2_SETPOINT", 0.0)
    win.mfc2_target_slm = 0.0
    win.mfc2_flow_history.clear()
    win.ui.MenuPrincipal_btn_mfc2_open.setText("Abrir Valvula MFC2: N2")
    win.ui.MenuPrincipal_btn_mfc2_open.setStyleSheet("")
    win.ui.MenuPrincipal_btn_mfc2_set.setStyleSheet("")

    # G. Mostrar Pop-up modal de advertencia al usuario
    gas_list_str = " y ".join(failed_gases)
    msg_box = QtWidgets.QMessageBox(win)
    msg_box.setIcon(QtWidgets.QMessageBox.Warning)
    msg_box.setWindowTitle("Alerta de Caudal - MFC")
    msg_box.setText(
        f"<b>Desviación de caudal detectada en: {gas_list_str}</b>"
    )
    msg_box.setInformativeText(
        "El flujo de gas se encuentra fuera del rango de tolerancia permitido.\n\n"
        "Se han cerrado las válvulas de gas, y se han apagado y deshabilitado por seguridad las lámparas y el sistema de plasma."
    )
    msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg_box.button(QtWidgets.QMessageBox.Ok).setText("Aceptar")
    msg_box.exec_()

# ===================================================================
# LECTURA DEL SENSOR DE END OF PROCESS (EOP)
# ===================================================================
def update_eop_displays(win):
    """Lee el sensor analógico de End of Process (EOP) y actualiza el LCD."""
    try:
        eop_volts = win.hw.analog_read("EOP")
        win.ui.MenuPrincipal_eop_voltage.display(f"{eop_volts:.2f}")
    except Exception as e:
        print(f"[ERROR] No se pudo leer el canal EOP: {e}")