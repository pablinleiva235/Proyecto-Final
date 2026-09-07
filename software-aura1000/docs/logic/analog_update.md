# `analog_update.py`

El módulo `analog_update.py` tiene los metodos llamados en el timer general cada 100ms de lectura de señales analogicas (presion, temperatura, flujo de MFCs y señal del EOP) y actualizacion de los displays de la interfaz

---

## <span style="color: #4CAF50;">Adquisición de Datos y Monitoreo Analógico</span>

??? note "Helper de Indicadores Visuales: `update_led_indicator(...)`"
    Función auxiliar que aplica de forma dinámica hojas de estilo CSS (`setStyleSheet`) sobre un widget `QLabel`. Modifica el color de fondo, bordes y texto para emular visualmente el comportamiento de un indicador LED según el estado lógico (Activo/Inactivo) de un subsistema.

    ```python
    def update_led_indicator(label_widget, state_active: bool, text_active: str, text_inactive: str):
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
    ```

??? note "Lectura de Presión de Cámara y Estado ATM: `update_pressure_display(win)`"
    Realiza la adquisición de tensión analógica del manómetro Baratron, escala linealmente la lectura a Torr (basado en `BARATRON_FULL_SCALE`) y la proyecta en el visor LCD de la cámara. Adicionalmente, evalúa el interruptor digital de presión atmosférica (`ATM_SWITCH`), actualiza la etiqueta LED visual correspondiente y retorna el estado booleano de la cámara.

    ```python
    def update_pressure_display(win) -> bool:
        try:
            voltage = win.hw.analog_read("BARATRON")
            pressure_torr = max(0.0, voltage * (BARATRON_FULL_SCALE / 10.0))
            win.ui.MenuPrincipal_chamber_pressure.display(f"{pressure_torr:.3f}")

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
    ```

??? note "Monitoreo de Temperatura de Cámara: `update_temp_display(win)`"
    Adquiere el valor analógico escalado de la termocupla ubicada en la cámara de proceso (`CHAMBER_TEMP`) y actualiza el visor térmico en grados Celsius. Contempla excepciones y lecturas nulas para prevenir colapsos en la interfaz, mostrando indicadores de error visuales (`---` o `ERR`).

    ```python
    def update_temp_display(win):
        try:
            temp_c = win.hw.analog_read_temperature("CHAMBER_TEMP")

            if temp_c is not None:
                win.ui.MenuPrincipal_chamber_temp.display(f"{temp_c:.1f}")
            else:
                win.ui.MenuPrincipal_chamber_temp.display("---")
        except Exception as e:
            print(f"[ERROR] Error al leer la temperatura de la cámara: {e}")
            win.ui.MenuPrincipal_chamber_temp.display("ERR")
    ```

??? note "Lectura de readouts de flujo de MFCs: `update_mfc_displays(win)`"
    Interroga en tiempo real las entradas analógicas de retorno de flujo de los controladores masivos de caudal `MFC1_FLOW` (Oxígeno) y `MFC2_FLOW` (Nitrógeno). Sanitiza los valores leídos para evitar números negativos y actualiza los indicadores LCD de realimentación de caudal en la pantalla. Agrega cada medicion al buffer circular de 30 muestras (`MFC_WINDOW_SAMPLES`) y chequea que el promedio de estas lecturas del buffer no se salga de la tolerancia dada por `MFC_FLOW_TOLERANCE_PCT`.

    ```python
    def update_mfc_displays(win):
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
    ```

??? note "Lectura de señal del Sensor End of Process (EOP): `update_eop_displays(win)`"
    Monitorea el canal analógico del sensor óptico de fin de proceso (`EOP`). Presenta la tensión instantánea medida en el visor visual correspondiente para permitir el seguimiento del avance del stripping/ataque por plasma.

    ```python
    def update_eop_displays(win):
        """Lee el sensor analógico de End of Process (EOP) y actualiza el LCD."""
        try:
            eop_volts = win.hw.analog_read("EOP")
            win.ui.MenuPrincipal_eop_voltage.display(f"{eop_volts:.2f}")
        except Exception as e:
            print(f"[ERROR] No se pudo leer el canal EOP: {e}")
    ```

---

## <span style="color: #4CAF50;">Metodos auxiliares para deteccion de fallas en caso de MFCs fuera de rango</span>

??? note "Chequeo de readout de MFCs fuera de rango": `_check_mfc_faults(win)`"
    Verifica si el promedio de lecturas de los últimos 3s difiere en más del 5% del target, si es asi llama a `_trigger_mfc_safety_shutdown`

    ```python
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
            main_vacuum_on = (win.ui.MenuPrincipal_btn_main_vacuum.text() == "Main Vacuum Off")
            alarm_active = getattr(win, "alarm_active", False)

            is_safe = main_vacuum_on and not alarm_active

            win.ui.MenuPrincipal_btn_plasma.setEnabled(is_safe)
            win.ui.MenuPrincipal_btn_outerLamps.setEnabled(is_safe)
            win.ui.MenuPrincipal_btn_centralLamp.setEnabled(is_safe)

            if hasattr(win.ui, "ThrottleMenu_pressure_set"):
                win.ui.ThrottleMenu_pressure_set.setEnabled(is_safe)
                win.ui.ThrottleMenu_pressure_stop.setEnabled(is_safe)
                win.ui.ThrottleMenu_pressure_entry.setEnabled(is_safe)
    ```

??? note " Apagado de plasma y lamparas en caso de falla de MFCs: `_trigger_mfc_safety_shutdown(win)`"
    Ejecuta las acciones de seguridad al detectar desvío de caudal de los MFCs y da aviso en una ventana de Warning al usuario

    ```python
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
    ```