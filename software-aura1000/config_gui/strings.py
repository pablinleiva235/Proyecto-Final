"""
Textos visibles de la interfaz gráfica.

Las variables y constantes del código se mantienen en inglés, mientras que
todos los textos mostrados al usuario se escriben en español y se centralizan
en este archivo.
"""

# =============================================================================
# Aplicación
# =============================================================================

APP_TITLE = "Plasma Asher AURA 1000"
APP_SUBTITLE = "Software de control"


# =============================================================================
# Pantalla de inicio
# =============================================================================

STARTUP_TITLE = "PLASMA ASHER AURA 1000"

STARTUP_WAITING_MESSAGE = (
    "Presione el botón de encendido para iniciar el equipo."
)

STARTUP_RUNNING_MESSAGE = (
    "Iniciando equipo. Espere..."
)

STARTUP_ERROR_MESSAGE = (
    "Ocurrió un error durante el inicio del equipo."
)


# =============================================================================
# Pantalla Principal
# =============================================================================

WELCOME_TITLE = "PLASMA ASHER AURA 1000"

NORMAL_OPERATION_BUTTON_TEXT = "Operación normal"
MAINTAINER_BUTTON_TEXT = "Mantenimiento"
STATISTICS_BUTTON_TEXT = "Estadísticas"

# =============================================================================
# Operación normal (prototipo visual simulado)
# =============================================================================

NORMAL_OPERATION_TITLE = "OPERACIÓN NORMAL"
SIMULATION_MODE_LABEL = "MODO SIMULADO"
SIMULATION_MODE_DESCRIPTION = "Los controles de esta pantalla solo modifican la demostración visual."
EQUIPMENT_STATUS_TITLE = "Estado del equipo"
EQUIPMENT_STATUS_READY = "Listo para operación (simulado)"
VACUUM_PRESSURE_TITLE = "Vacío y presión"
VACUUM_STATE_LABEL = "Bomba de vacío"
CHAMBER_PRESSURE_LABEL = "Presión de cámara"
GAS_FLOWS_TITLE = "Flujo de gases"
OXYGEN_FLOW_LABEL = "Oxígeno (O₂)"
NITROGEN_FLOW_LABEL = "Nitrógeno (N₂)"
CHAMBER_TEMPERATURE_TITLE = "Temperatura de cámara"
PLASMA_STATUS_TITLE = "Plasma"
PLASMA_STATE_LABEL = "Estado del plasma"
MODULE_CONTROLS_TITLE = "Módulos · demostración"
FLOW_SETPOINT_LABEL = "Flujo deseado"
PRESSURE_SETPOINT_LABEL = "Presión deseada"
TEMPERATURE_SETPOINT_LABEL = "Temperatura deseada"
MEASURED_VALUE_PREFIX = "Medido"
APPLY_DEMO_BUTTON = "Aplicar"
SETPOINT_APPLIED = "Guardado en demo."
SETPOINT_INVALID = "Valor no válido (rango indicado)."
DIGITAL_STATUS_TITLE = "Estados digitales (simulados)"
ATMOSPHERE_STATUS_LABEL = "Presión ATM"
DOOR_STATUS_LABEL = "Puerta"
AIR_FLOW_STATUS_LABEL = "Aire"
LAMP_FAILURE_STATUS_LABEL = "Lámparas"
PLASMA_FAILURE_STATUS_LABEL = "Plasma"
MAGNETRON_WARNING_STATUS_LABEL = "Aviso magnetrón"
MAGNETRON_OVERHEAT_STATUS_LABEL = "Sobretemperatura"
DEMO_STATUS_ATMOSPHERE = "VACÍO"
DEMO_STATUS_DOOR = "CERRADA"
DEMO_STATUS_OK = "OK"
DEMO_STATUS_NO_FAILURE = "SIN FALLA"
DEMO_STATUS_NORMAL = "NORMAL"
MFC1_RANGE_LABEL = "0–10 SLPM · ±0,05"
MFC2_RANGE_LABEL = "0–1 SLPM · ±0,05"
SIMULATED_ON = "ACTIVO"
SIMULATED_OFF = "INACTIVO"
SIMULATED_START_BUTTON = "Iniciar"
SIMULATED_STOP_BUTTON = "Detener"
SAVE_RECIPE_BUTTON = "Guardar receta"
LOAD_RECIPE_BUTTON = "Cargar receta"
START_PROCESS_BUTTON = "Iniciar proceso"
RECIPE_FEATURE_PENDING_TITLE = "Función pendiente"
RECIPE_FEATURE_PENDING_MESSAGE = (
    "La gestión de recetas estará disponible en una próxima etapa."
)
START_PROCESS_PENDING_TOOLTIP = (
    "Pendiente de integrar la secuencia real del proceso."
)


# =============================================================================
# Barra superior
# =============================================================================

EXIT_BUTTON_TEXT = "X"


# =============================================================================
# Confirmación de salida
# =============================================================================

EXIT_CONFIRMATION_TITLE = "Confirmar salida"
EXIT_CONFIRMATION_MESSAGE = (
    "¿Está seguro de que desea salir de la aplicación?"
)


# =============================================================================
# Login de mantenimiento
# =============================================================================

LOGIN_WINDOW_TITLE = "Acceso de mantenimiento"
LOGIN_TITLE = "Acceso de mantenimiento"

USERNAME_LABEL = "Usuario"
USERNAME_PLACEHOLDER = "Ingrese el usuario"

PASSWORD_LABEL = "Contraseña"
PASSWORD_PLACEHOLDER = "Ingrese la contraseña"

LOGIN_BUTTON_TEXT = "Ingresar"
CANCEL_BUTTON_TEXT = "Cancelar"

INVALID_CREDENTIALS_MESSAGE = "Usuario o contraseña inválidos."


# =============================================================================
# Pantalla de mantenimiento
# =============================================================================

MAINTAINER_TITLE = "MODO MANTENIMIENTO"
MAINTAINER_PLACEHOLDER = "Pantalla temporal de mantenimiento"

DIGITAL_INPUTS_TITLE = "Entradas digitales"
DIGITAL_OUTPUTS_TITLE = "Salidas digitales"

# =============================================================================
# Pantalla de estadísticas
# =============================================================================

STATISTICS_TITLE = "ESTADÍSTICAS"
STATISTICS_PLACEHOLDER = "Pantalla temporal de estadísticas"


# =============================================================================
# Navegación
# =============================================================================

BACK_BUTTON_TEXT = "Volver"


# =============================================================================
# Pantalla de mantenimiento
# =============================================================================

MAINTAINER_SECUENCES_TAB = "Modulos"
MAINTAINER_SIGNALS_TAB = "DIO - Digital Input Output"
MAINTAINER_ANALOG_TAB = "ADC - Lecturas analógicas"
MAINTAINER_MFC_TITLE = "Control de MFC"
MAINTAINER_APPLY_FLOW = "Aplicar flujo"
MAINTAINER_OPEN_VALVE = "Abrir válvula"
MAINTAINER_CLOSE_VALVE = "Cerrar válvula"
MAINTAINER_THROTTLE_TITLE = "Throttle · movimiento manual"
MAINTAINER_THROTTLE_OPEN = "Abrir throttle"
MAINTAINER_THROTTLE_CLOSE = "Cerrar throttle"
MAINTAINER_PROCESS_TITLE = "Lámparas y plasma"
MAINTAINER_PULSE_SECONDS = "Pulso (s):"
MAINTAINER_LAMPS_PULSE = "Pulso lámparas 1 y 3"
MAINTAINER_LAMP2_ON = "Encender lámpara 2"
MAINTAINER_LAMP2_OFF = "Apagar lámpara 2"
MAINTAINER_PLASMA_ON = "Encender plasma"
MAINTAINER_PLASMA_OFF = "Apagar plasma"

DOOR_SEQUENCE_OPEN_BUTTON = "Abrir Puerta"
DOOR_SEQUENCE_CLOSE_BUTTON = "Cerrar Puerta"

DOOR_SEQUENCE_OPENING_BUTTON = "Abriendo..."
DOOR_SEQUENCE_CLOSING_BUTTON = "Cerrando..."
DOOR_SEQUENCE_ERROR_BUTTON = "Error de Puerta"

SOFT_VACUUM_ON_BUTTON = "Soft Vacuum ON"
SOFT_VACUUM_OFF_BUTTON = "Soft Vacuum OFF"
SOFT_VACUUM_ERROR_BUTTON = "Error Soft Vacuum"

MAIN_VACUUM_ON_BUTTON = "Main Vacuum ON"
MAIN_VACUUM_OFF_BUTTON = "Main Vacuum OFF"
MAIN_VACUUM_ERROR_BUTTON = "Error Main Vacuum"

VENT_ON_BUTTON = "Vent ON"
VENT_OFF_BUTTON = "Vent OFF"
VENT_ERROR_BUTTON = "Error de Venteo"

# =============================================================================
# SEÑALES
# =============================================================================

SIGNAL_DIRECTION_INPUT = "ENTRADA"
SIGNAL_DIRECTION_OUTPUT = "SALIDA"
SIGNAL_OUTPUT_MODULE_CONTROL = "Salida · control del módulo"
MFC_VALVE_INTERLOCK_ERROR = (
    "Para abrir una válvula MFC, el vacío principal debe estar activo "
    "y la puerta debe estar cerrada."
)

SIGNAL_STATE_ACTIVE = "ACTIVA"
SIGNAL_STATE_INACTIVE = "INACTIVA"
SIGNAL_STATE_PROCESSING = "PROCESANDO..."
SIGNAL_STATE_UNAVAILABLE = "SIN DATOS"

# Preferencias de idioma y tema.
SETTINGS_TITLE = "Configuración"
SETTINGS_LANGUAGE_LABEL = "Idioma"
SETTINGS_THEME_LABEL = "Tema"
SETTINGS_LANGUAGE_SPANISH = "Español"
SETTINGS_LANGUAGE_ENGLISH = "Inglés"
SETTINGS_THEME_DARK = "Oscuro"
SETTINGS_THEME_LIGHT = "Claro"
SETTINGS_DEVELOPERS_TITLE = "Desarrolladores"
SETTINGS_TUTORS_TITLE = "Tutores"
SETTINGS_CLOSE_BUTTON = "Cerrar"
SETTINGS_BUTTON_TOOLTIP = "Configuración de idioma y tema"

# Marcadores provisionales para completar con los nombres confirmados.
DEVELOPER_NAMES = ("Nombre del desarrollador 1", "Nombre del desarrollador 2")
TUTOR_NAMES = ("Nombre del tutor 1", "Nombre del tutor 2")

_ACTIVE_LANGUAGE = "es"
_SPANISH_TO_ENGLISH = {
    "Software de control": "Control software",
    "Operación normal": "Normal operation",
    "Mantenimiento": "Maintenance",
    "Estadísticas": "Statistics",
    "OPERACIÓN NORMAL": "NORMAL OPERATION",
    "MODO SIMULADO": "SIMULATION MODE",
    "Los controles de esta pantalla solo modifican la demostración visual.": "Controls on this screen only change the visual demo.",
    "Estado del equipo": "Equipment status",
    "Listo para operación (simulado)": "Ready for operation (simulated)",
    "Vacío y presión": "Vacuum and pressure",
    "Bomba de vacío": "Vacuum pump",
    "Presión de cámara": "Chamber pressure",
    "Flujo de gases": "Gas flow",
    "Oxígeno (O₂)": "Oxygen (O₂)",
    "Nitrógeno (N₂)": "Nitrogen (N₂)",
    "Oxígeno (O₂) · Flujo deseado": "Oxygen (O₂) · Flow setpoint",
    "Nitrógeno (N₂) · Flujo deseado": "Nitrogen (N₂) · Flow setpoint",
    "Nombre del desarrollador 1": "Developer name 1",
    "Nombre del desarrollador 2": "Developer name 2",
    "Nombre del tutor 1": "Advisor name 1",
    "Nombre del tutor 2": "Advisor name 2",
    "Temperatura de cámara": "Chamber temperature",
    "Estado del plasma": "Plasma status",
    "Módulos · demostración": "Modules · demonstration",
    "Flujo deseado": "Flow setpoint",
    "Presión deseada": "Pressure setpoint",
    "Temperatura deseada": "Temperature setpoint",
    "Medido": "Measured",
    "Aplicar": "Apply",
    "Guardado en demo.": "Saved in demo.",
    "Valor no válido (rango indicado).": "Invalid value (see range).",
    "Estados digitales (simulados)": "Digital states (simulated)",
    "Presión ATM": "Atmosphere",
    "Puerta": "Door",
    "Aire": "Air flow",
    "Lámparas": "Lamps",
    "Aviso magnetrón": "Magnetron warning",
    "Sobretemperatura": "Overheat",
    "VACÍO": "VACUUM",
    "CERRADA": "CLOSED",
    "SIN FALLA": "NO FAULT",
    "NORMAL": "NORMAL",
    "0–10 SLPM · ±0,05": "0–10 SLPM · ±0.05",
    "0–1 SLPM · ±0,05": "0–1 SLPM · ±0.05",
    "ACTIVO": "ON",
    "INACTIVO": "OFF",
    "Iniciar": "Start",
    "Detener": "Stop",
    "Guardar receta": "Save recipe",
    "Cargar receta": "Load recipe",
    "Iniciar proceso": "Start process",
    "Función pendiente": "Feature pending",
    "La gestión de recetas estará disponible en una próxima etapa.": "Recipe management will be available in a future stage.",
    "Pendiente de integrar la secuencia real del proceso.": "The real process sequence has not been integrated yet.",
    "Confirmar salida": "Confirm exit",
    "Sí": "Yes",
    "No": "No",
    "¿Está seguro de que desea salir de la aplicación?": "Are you sure you want to exit the application?",
    "Acceso de mantenimiento": "Maintenance access",
    "Ingrese el usuario": "Enter username",
    "Ingrese la contraseña": "Enter password",
    "Usuario": "Username",
    "Contraseña": "Password",
    "Ingresar": "Log in",
    "Cancelar": "Cancel",
    "Usuario o contraseña inválidos.": "Invalid username or password.",
    "MODO MANTENIMIENTO": "MAINTENANCE MODE",
    "Pantalla temporal de mantenimiento": "Temporary maintenance screen",
    "Entradas digitales": "Digital inputs",
    "Salidas digitales": "Digital outputs",
    "ESTADÍSTICAS": "STATISTICS",
    "Pantalla temporal de estadísticas": "Temporary statistics screen",
    "Volver": "Back",
    "Modulos": "Modules",
    "DIO - Digital Input Output": "DIO - Digital input/output",
    "ADC - Lecturas analógicas": "ADC - Analog readings",
    "Control de MFC": "MFC control",
    "Aplicar flujo": "Apply flow",
    "Abrir válvula": "Open valve",
    "Cerrar válvula": "Close valve",
    "Throttle · movimiento manual": "Throttle · manual movement",
    "Abrir throttle": "Open throttle",
    "Cerrar throttle": "Close throttle",
    "Lámparas y plasma": "Lamps and plasma",
    "Pulso (s):": "Pulse (s):",
    "Pulso lámparas 1 y 3": "Pulse lamps 1 and 3",
    "Encender lámpara 2": "Turn lamp 2 on",
    "Apagar lámpara 2": "Turn lamp 2 off",
    "Encender plasma": "Turn plasma on",
    "Apagar plasma": "Turn plasma off",
    "Abrir Puerta": "Open door",
    "Cerrar Puerta": "Close door",
    "Abriendo...": "Opening...",
    "Cerrando...": "Closing...",
    "Error de Puerta": "Door error",
    "Soft Vacuum ON": "Soft vacuum ON",
    "Soft Vacuum OFF": "Soft vacuum OFF",
    "Error Soft Vacuum": "Soft vacuum error",
    "Main Vacuum ON": "Main vacuum ON",
    "Main Vacuum OFF": "Main vacuum OFF",
    "Error Main Vacuum": "Main vacuum error",
    "Vent ON": "Vent ON",
    "Vent OFF": "Vent OFF",
    "Error de Venteo": "Vent error",
    "ACTIVA": "ACTIVE",
    "INACTIVA": "INACTIVE",
    "PROCESANDO...": "PROCESSING...",
    "ABRIENDO": "OPENING",
    "CERRANDO": "CLOSING",
    "SIN DATOS": "NO DATA",
    "Presione el botón de encendido para iniciar el equipo.": "Press the power button to start the equipment.",
    "Iniciando equipo. Espere...": "Starting equipment. Please wait...",
    "Ocurrió un error durante el inicio del equipo.": "An error occurred while starting the equipment.",
    "Configuración": "Settings",
    "Idioma": "Language",
    "Tema": "Theme",
    "Español": "Spanish",
    "Inglés": "English",
    "Oscuro": "Dark",
    "Claro": "Light",
    "Desarrolladores": "Developers",
    "Tutores": "Advisors",
    "Cerrar": "Close",
    "Configuración de idioma y tema": "Language and theme settings",
    "Errores durante el apagado": "Shutdown errors",
    "Se encontraron errores durante el apagado. Revise el registro:": "Errors occurred during shutdown. Please review the log:",
    "Alarma de seguridad": "Safety alarm",
    "Advertencia del magnetrón": "Magnetron warning",
    "Se detuvieron lámparas y plasma por una falla:": "Lamps and plasma were stopped due to a fault:",
    "El vacío principal debe estar activo para controlar los MFC.": "Main vacuum must be active to control the MFCs.",
    "El flujo debe estar entre 0 y 10 SLPM.": "Flow must be between 0 and 10 SLPM.",
    "El flujo debe estar entre 0 y 1 SLPM.": "Flow must be between 0 and 1 SLPM.",
    "El movimiento manual requiere el vacío principal activo.": "Manual movement requires main vacuum to be active.",
    "El magnetrón alcanzó la señal de advertencia de temperatura.": "The magnetron reached its temperature warning threshold.",
    "Entrada digital": "Digital input",
    "Salida · solo lectura": "Output · read only",
    "Salida · control del módulo": "Output · controlled by module",
    "Para abrir una válvula MFC, el vacío principal debe estar activo y la puerta debe estar cerrada.": "To open an MFC valve, main vacuum must be active and the door must be closed.",
    "Salida · tocar para alternar": "Output · click to toggle",
    "DETENIDO": "STOPPED",
    "LISTAS": "READY",
    "PULSO ACTIVO": "PULSE ACTIVE",
    "ENCENDIDA": "ON",
    "APAGADA": "OFF",
    "APAGADO": "OFF",
    "ABIERTA": "OPEN",
    "Baratron · Presión": "Baratron · Pressure",
    "MFC3 · Lectura": "MFC3 · Readout",
    "MFC4 · Lectura": "MFC4 · Readout",
    "Lectura analógica": "Analog reading",
    "SLPM medidos": "SLPM measured",
    "MFC1 (O₂) · 0–10 SLPM": "MFC1 (O₂) · 0–10 SLPM",
    "MFC2 (N₂) · 0–1 SLPM": "MFC2 (N₂) · 0–1 SLPM",
    "MFC1 · SLPM": "MFC1 · SLPM",
    "MFC2 · SLPM": "MFC2 · SLPM",
    "MFC3 · V": "MFC3 · V",
    "MFC4 · V": "MFC4 · V",
    "Presión · Torr": "Pressure · Torr",
    "Temperatura · °C": "Temperature · °C",
    "EOP · V": "EOP · V",
    "Falla en lámpara 1 (pérdida de corriente).": "Lamp 1 fault (current loss).",
    "Falla en lámpara 2 (pérdida de corriente).": "Lamp 2 fault (current loss).",
    "Falla en lámpara 3 (pérdida de corriente).": "Lamp 3 fault (current loss).",
    "Falla en plasma (no encendió o se interrumpió la RF).": "Plasma fault (RF failed to ignite or was interrupted).",
    "Sobretemperatura del magnetrón.": "Magnetron overheat.",
}
_ENGLISH_TO_SPANISH = {translated: original for original, translated in _SPANISH_TO_ENGLISH.items()}


def set_language(language):
    global _ACTIVE_LANGUAGE
    if language not in ("es", "en"):
        raise ValueError("El idioma debe ser 'es' o 'en'.")
    _ACTIVE_LANGUAGE = language


def get_language():
    return _ACTIVE_LANGUAGE


def tr(value):
    if not isinstance(value, str) or _ACTIVE_LANGUAGE == "es":
        return value
    if value in _SPANISH_TO_ENGLISH:
        return _SPANISH_TO_ENGLISH[value]
    if value.startswith("Medido: "):
        return "Measured: " + value[len("Medido: "):]
    if value.startswith("Disminuir de a "):
        return "Decrease by " + value[len("Disminuir de a "):]
    if value.startswith("Aumentar de a "):
        return "Increase by " + value[len("Aumentar de a "):]
    if value.startswith("Se detuvieron lámparas y plasma por una falla:"):
        return "Lamps and plasma were stopped due to a fault:" + value[len("Se detuvieron lámparas y plasma por una falla:"):]
    if value == "Abrir throttle (abriendo)":
        return "Open throttle (opening)"
    if value == "Cerrar throttle (cerrando)":
        return "Close throttle (closing)"
    for prefix in (
        "MFC1", "MFC2", "MFC", "Throttle", "Lámparas 1 y 3", "Plasma",
        "lamp2", "Monitoreo de fallas", "Apagado seguro",
    ):
        if value.startswith(prefix + ": "):
            return prefix + ": " + tr(value[len(prefix) + 2:])
    if "\n" in value:
        return "\n".join(tr(line) for line in value.split("\n"))
    for source, translated in _SPANISH_TO_ENGLISH.items():
        if value.startswith(source + ": "):
            return translated + value[len(source):]
    return value


def source_text(value):
    if not isinstance(value, str):
        return value
    return _ENGLISH_TO_SPANISH.get(value, value)


