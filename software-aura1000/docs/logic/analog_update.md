# `analog_update.py`

El módulo `analog_update.py` tiene los metodos llamados en el timer general cada 100ms de lectura de señales analogicas (presion, temperatura, flujo de MFCs y señal del EOP) y actualizacion de los displays de la interfaz

---

## <span style="color: #4CAF50;">Adquisición de Datos y Monitoreo Analógico</span>

??? note "Helper de Indicadores Visuales: `update_led_indicator(...)`"
    Función auxiliar que aplica de forma dinámica hojas de estilo CSS (`setStyleSheet`) sobre un widget `QLabel`. Modifica el color de fondo, bordes y texto para emular visualmente el comportamiento de un indicador LED según el estado lógico (Activo/Inactivo) de un subsistema.

    ```python
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
    ```

??? note "Lectura de Presión de Cámara y Estado ATM: `update_pressure_display(win)`"
    Realiza la adquisición de tensión analógica del manómetro Baratron, escala linealmente la lectura a Torr (basado en `BARATRON_FULL_SCALE`) y la proyecta en el visor LCD de la cámara. Adicionalmente, evalúa el interruptor digital de presión atmosférica (`ATM_SWITCH`), actualiza la etiqueta LED visual correspondiente y retorna el estado booleano de la cámara.

    ```python
    def update_pressure_display(win) -> bool:
        """Lee el Baratron y el ATM_SWITCH, actualiza la GUI y retorna el estado de ATM."""
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
    ```

??? note "Lectura de readouts de flujo de MFCs: `update_mfc_displays(win)`"
    Interroga en tiempo real las entradas analógicas de retorno de flujo de los controladores masivos de caudal `MFC1_FLOW` (Oxígeno) y `MFC2_FLOW` (Nitrógeno). Sanitiza los valores leídos para evitar números negativos y actualiza los indicadores LCD de realimentación de caudal en la pantalla.

    ```python
    def update_mfc_displays(win):
        """Lee el caudal real de los sensores analógicos MFC1_FLOW y MFC2_FLOW y actualiza los LCDs de la GUI."""
        try:
            # --- 1. Lectura de MFC1 (O2) ---
            v_mfc1 = win.hw.analog_read("MFC1_FLOW")
            slm_mfc1 = max(0.0, v_mfc1)
            win.ui.MenuPrincipal_mfc1_readout.display(f"{slm_mfc1:.2f}")

            # --- 2. Lectura de MFC2 (N2) ---
            v_mfc2 = win.hw.analog_read("MFC2_FLOW")
            slm_mfc2 = max(0.0, v_mfc2)
            win.ui.MenuPrincipal_mfc2_readout.display(f"{slm_mfc2:.2f}")

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