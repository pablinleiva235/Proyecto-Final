# Estructura del Proyecto

A continuación se detalla la arquitectura de directorios del software de revamping para el equipo **Gasonics Aura 1000 Plasma Asher**. El repositorio está organizado de forma modular para separar claramente las configuraciones físicas de hardware, las capas de abstracción de los drivers de bajo nivel, los servicios lógicos del sistema y la interfaz gráfica de usuario.

---

## <span style="color: #2196F3;">Árbol de Directorios</span>

Este es el arbol de proyecto con las carpetas y archivos críticos del sistema:

```text
SOFTWARE-AURA1000/
├── config/                  # Archivos de configuración de hardware y constantes
│   ├── analog_signals.py       # Mapeo de canales y rangos del DAC/ADC y termocupla (USB-2527)
│   └── digital_signals.py      # Mapeo de señales digitales (USBDIO96H)
├── docs/                    # Archivos fuente de esta documentación (Markdown)
├── drivers/                 # Capa de abstracción de hardware (Bajo nivel) usando APIs de la UL 'cbw32.dll'
│   ├── analog_driver.py        # Traducción de APIs de USB-2527 a Python mediante ctypes 
│   └── dio_driver.py           # Traducción de APIs de USBDIO96H a Python mediante ctypes
├── gui/                     # Archivos de la interfaz gráfica de usuario (Vista pura)
│   ├── main_window.py          # Coordinador de la GUI, eventos de cierre y máquina de estados principal
│   ├── pyqt_gui.py             # Código Python auto-generado por pyuic5
│   └── pyqt_gui.ui             # Archivo de diseño original de Qt Designer
├── logic/                   # Capa de lógica intermedia y procesos secuenciales
│   ├── maintenance_process.py  # Menu para pruebas de proceso de forma modular secuencial
│   ├── pre_encendido.py        # Secuencia de arranque del equipo (barra de progreso y estados iniciales)
│   └── timers_io.py            # Administrador central de Timers y lazo de lectura de entradas (100ms)
├── services/                # Servicios de hardware de alto nivel
│   ├── hardware.py             # Clase principal de abstracción y control integrado de placas
│   └── system_state.py         # Definición de la enumeración de estados del equipo (Enum)
├── .gitignore               # Archivos excluidos del control de versiones (ej: site/, __pycache__/)
├── main.py                  # Punto de entrada de la aplicación (Instanciación y arranque)
├── mkdocs.yml               # Archivo de configuración principal de MkDocs
└── requirements.txt         # Dependencias del proyecto (PyQt5, etc.)
```

---

## <span style="color: #2196F3;">Descripción de los Componentes</span>

Para entender el flujo de trabajo del software, cada directorio cumple un rol específico dentro de la arquitectura:

??? note "📂 Carpeta `config/`"
    Aloja diccionarios de Python que actúan como "tablas de verdad" o mapas físicos. Centraliza los nombres lógicos de las señales (como `PURGE_VALVE_CONTROL` o `BARATRON`) asociándolos a sus puertos y bits reales. Esto permite realizar cambios en el cableado eléctrico del equipo modificando un solo archivo, sin alterar el código fuente de los drivers o la GUI.

??? note "📂 Carpeta `drivers/`"
    Contiene la lógica encargada de realizar llamadas dinámicas a la API de C de la *Universal Library* (`cbw32.dll`) utilizando `ctypes`. Convierte los tipos de datos de Python a estructuras de bajo nivel para interactuar con las placas **USB-2527** y **USBDIO96H**.

??? note "📂 Carpeta `gui/`"
    Contiene todo lo relacionado con el entorno visual del operador. Aquí se encuentra el archivo `.ui` de diseño, el script generado por el compilador `pyuic5`, y el coordinador de la interfaz (**`main_window.py`**). Este último se encarga de administrar la máquina de estados principal, gestionar el cambio de páginas de la GUI y asegurar el cierre correcto del sistema, delegando las tareas pesadas a la capa de lógica.

??? note "📂 Carpeta `logic/`"
    Aloja la lógica intermedia de control y los procesos secuenciales del equipo. Contiene el administrador central de tiempos (**`timers_io.py`**), encargado de orquestar todos los timers y el lazo periódico de lectura de entradas (100ms), y scripts de lógica específicos por estado (como **`pre_encendido.py`**). Asimismo, incorpora **`maintenance_process.py`**, el cual expone rutinas y código específico para probar de forma secuencial los distintos módulos y actuadores utilizados durante un proceso. Estos módulos interactúan en paralelo tanto con la capa de hardware como con los elementos visuales de la interfaz gráfica.

??? note "📂 Carpeta `services/`"
    Contiene la capa que hace de intermediaria entre la GUI y las funciones de bajo nivel del hardware, y un archivo para enumerar los estados de la maquina de estados:
    
    * **`hardware.py` (Clase `Hardware`):** Es la API interna del software. Se encarga de inicializar físicamente las placas al arrancar el equipo y expone métodos limpios de alto nivel (lecturas/escrituras digitales y analogicas lazos de apagado seguro) traduciendo los nombres de los diccionarios de `config/` hacia las funciones de los `drivers/`. La GUI interactúa exclusivamente con esta clase.
    * **`system_state.py`:** Define la enumeración de los estados del equipo (`PRE_ENCENDIDO`, `MAIN_MENU`, etc.), garantizando que el sistema opere bajo una maquina de estados

---

---

## <span style="color: #2196F3;">Entorno de Desarrollo y Compilación de la GUI</span>

!!! info "Gestión del Entorno Virtual (Python venv)"
    Antes de trabajar con la interfaz gráfica o compilar cualquier cambio, asegurate de tener el entorno virtual aislado con las librerías necesarias instaladas:

    **1. Crear el entorno virtual (Solo la primera vez):**
    ```bash
    python -m venv virt
    ```

    **2. Activar el entorno virtual en la terminal:**
    ```bash
    source virt/Scripts/activate
    ```
    *(Recordá que si usás el CMD clásico de Windows en vez de Git Bash, el comando de activación es `virt\Scripts\activate`)*.

    **3. Instalar dependencias del proyecto (Solo la primera vez con el entorno activo):**
    ```bash
    pip install PyQt5
    pip install PyQt5Designer
    ```

!!! tip "Flujo de Compilación con pyuic5"
    Una vez que el entorno virtual esté activo y las dependencias instaladas, cada vez que modifiques el layout visual desde **Qt Designer**, debés recompilar el archivo `.ui` para transformarlo en el script de Python que lee el orquestador. 
    
    Parate con la terminal dentro de la carpeta `gui/` y ejecutá:
    ```bash
    pyuic5 -x main_window.ui -o pyqt_gui.py
    ```