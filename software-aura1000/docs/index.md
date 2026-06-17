# Revamping del Gasonics Aura 1000 Plasma Asher

Bienvenido a la documentación técnica del software de control para revamping del equipo **Gasonics Aura 1000 Plasma Asher**, ubicado en el **Departamento de Micro y Nano Tecnología** de la **CNEA**. 

El proyecto no solo apunta a recuperar las funcionalidades originales del equipo, sino también a mejorarlas mediante la automatización completa del proceso, la implementación de recetas programables y el rediseño de subsistemas críticos como el control de presión, mediante un software robusto, portable y compatible con sistemas operativos modernos.

Esto permitirá extender la vida útil del equipo, optimizar su desempeño, garantizar condiciones de operación seguras para los usuarios y permitir a futuro su escalabilidad y mantenimiento

---

## <span style="color: #2196F3;">¿Qué es el Aura 1000?</span>

El Gasonics Aura 1000 es un sistema de procesamiento por plasma (Asher) utilizado principalmente en salas limpias para la **remoción de fotoresina (photoresist stripping)** y limpieza de obleas de silicio mediante plasma de oxígeno (O2). El equipo controla variables críticas de proceso como:

* **Vacío y Presión:** Control de la bomba de vacío y lectura del sensor capacitivo Baratron.
* **Gases de Proceso:** Inyección precisa de gases mediante controladores de flujo de masa (MFC).
* **Potencia de RF:** Habilitación y sintonía del generador de radiofrecuencia para la ignición del plasma.
* **Temperatura:** Monitoreo térmico de la cámara mediante termocuplas de proceso.

---

## <span style="color: #2196F3;">Tecnologías Utilizadas</span>

La nueva arquitectura de software fue diseñada de forma modular utilizando las siguientes herramientas:

* **Lenguaje Principal:** Python 3 (elegido por su flexibilidad para interactuar con librerías nativas y desarrollo rápido de scripts).
* **Interfaz Gráfica (GUI):** **PyQt5**, estructurando un entorno visual multi-página (`QStackedWidget`) intuitivo para el operador y un lazo síncrono de control de alta prioridad de 100 ms.
* **Adquisición de Datos (I/O):** Interfaz de bajo nivel con la *Universal Library* (`cbw32.dll`) mediante el módulo nativo `ctypes`, interactuando con las placas industriales **USBDIO96H** (96 canales digitales) y **USB-2527** (canales analógicos y DAC).

---

## <span style="color: #2196F3;">Guía de Navegación de la Documentación</span>

Para facilitar el análisis del código y el mantenimiento en el laboratorio, podés acceder directamente a cada sección desde los siguientes enlaces:

1. **[Estructura de Carpetas](arquitectura/carpetas.md)**
2. **[Tablas de Configuración <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/config)</span>](config/index.md)**
    * **[Señales Digitales <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/config/digital_signals.py)</span>](config/digital_signals.md)**
    * **[Señales Analógicas <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/config/analog_signals.py)</span>](config/analog_signals.md)**
3. **[Drivers de Hardware <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/drivers)</span>](drivers/index.md)**
    * **[Driver Digital <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/drivers/dio_driver.py)</span>](drivers/digital.md)**
    * **[Driver Analógico <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/drivers/analog_driver.py)</span>](drivers/analogico.md)**
4. **[Entorno Gráfico <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/gui)</span>](gui/index.md)**
    * **[Ventana Principal <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/gui/main_window.py)</span>](gui/main_window.md)**
    * **[Interfaz de PyQt5Designer <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/gui/pyqt_gui.py)</span>](gui/pyqt_gui.md)**
5. **[Logica <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/logic)</span>](logic/index.md)**
    * **[Pre Encendido <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/logic/pre_encendido.py)</span>](logic/pre_encendido.md)**
    * **[Gestion de timers y entradas digitales<span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/logic/timers_io.py)</span>](logic/timers_io.md)**    
6. **[Intermediario entre GUI y Hardware <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/services)</span>](services/index.md)**
    * **[Abstracción de Hardware <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/services/hardware.py)</span>](services/hardware.md)**
    * **[Estados de máquina de estados <span style="color: #9e9e9e; font-weight: normal; font-size: 0.9em;">(/services/system_state.py)</span>](services/system_state.md)**



