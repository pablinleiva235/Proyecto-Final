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

WELCOME_TITLE = "PLASMA ASHER\nAURA 1000"

NORMAL_OPERATION_BUTTON_TEXT = "Operación normal"
MAINTAINER_BUTTON_TEXT = "Mantenimiento"
STATISTICS_BUTTON_TEXT = "Estadísticas"

# =============================================================================
# Operación normal (prototipo visual simulado)
# =============================================================================

NORMAL_OPERATION_TITLE = "OPERACIÓN NORMAL"
SIMULATION_MODE_LABEL = "MODO SIMULADO"
SIMULATION_MODE_DESCRIPTION = "Las lecturas provienen del backend activo. El diagrama y la gestión de recetas están pendientes."
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
LOAD_RECIPE_BUTTON = "Cargar receta"
START_PROCESS_BUTTON = "Iniciar proceso"
RECIPE_FEATURE_PENDING_TITLE = "Función pendiente"
RECIPE_FEATURE_PENDING_MESSAGE = (
    "La gestión de recetas estará disponible en una próxima etapa."
)
START_PROCESS_PENDING_TOOLTIP = (
    "Pendiente de integrar la secuencia real del proceso."
)
OPERATION_READINGS_TITLE = "Lecturas de proceso"
OPERATION_TEMPERATURE_LABEL = "T Cámara"
OPERATION_PRESSURE_LABEL = "P Cámara"
OPERATION_MFC1_LABEL = "MFC1 · O₂"
OPERATION_MFC2_LABEL = "MFC2 · N₂"
OPERATION_EOP_LABEL = "End Point"
OPERATION_RF_LABEL = "Nivel de RF"
OPERATION_READING_WAITING = "Esperando lectura"
OPERATION_READING_UNAVAILABLE = "No disponible"
OPERATION_READING_OK = "Lectura recibida"
OPERATION_READING_ERROR = "Error de lectura"
OPERATION_DIAGRAM_TITLE = "Esquema del equipo"
OPERATION_DIAGRAM_LOAD_ERROR = "No se pudo cargar el diagrama del equipo."
OPERATION_RECIPE_ACTIONS_TITLE = "Recetas"
NEW_RECIPE_BUTTON = "Nueva receta"
START_RECIPE_BUTTON = "Iniciar receta"
VIEW_RECIPE_BUTTON = "Visualizar receta"
START_RECIPE_PENDING_TOOLTIP = "Pendiente de integrar las recetas y la secuencia real del proceso."
STOP_RECIPE_BUTTON = "Detener receta"
RECIPE_IDLE_STATUS = "Sin receta en ejecución."
START_RECIPE_CONFIRM_TITLE = "Confirmar inicio de receta"
WAFER_CONFIRM_TITLE = "Carga de oblea"
WAFER_CONFIRM_MESSAGE = "Inserte la oblea en la cámara y confirme para continuar."
WAFER_REMOVAL_CONFIRM_TITLE = "Retiro de oblea"
WAFER_REMOVAL_CONFIRM_MESSAGE = "¿Retiró la oblea de la cámara? Sí cerrará la puerta; No finalizará la receta dejando la puerta abierta."
RECIPE_LOG_SAVED_MESSAGE = "Registro guardado en:\n{path}"
RECIPE_LOG_FAILED_MESSAGE = "No se pudo guardar el registro. Ruta intentada:\n{path}"
RECIPE_DATA_SAVED_MESSAGE = "Datos de presión y temperatura guardados en:\n{path}"
RECIPE_DATA_FAILED_MESSAGE = "No se pudieron guardar los datos de presión y temperatura. Ruta intentada:\n{path}"
RECIPE_STATE_LABELS = {
    "waiting_for_wafer": "Esperando confirmación de carga de oblea.",
    "waiting_for_wafer_removal": "Esperando confirmación de retiro de oblea.",
    "closing_door": "Cerrando puerta.",
    "closing_door_after_recipe": "Cerrando puerta después de retirar la oblea.",
    "verifying_door_closed": "Esperando confirmación de puerta cerrada.",
    "verifying_door_closed_after_recipe": "Verificando el cierre de la puerta para finalizar.",
    "starting_soft_vacuum": "Iniciando Soft Vacuum.",
    "starting_main_vacuum": "Iniciando Main Vacuum.",
    "pumping_to_base": "Esperando presión base.",
    "starting_gas_flow": "Configurando caudales de gases.",
    "controlling_pressure": "Regulando presión de proceso.",
    "controlling_temperature": "Regulando temperatura.",
    "running_plasma": "Proceso de plasma en curso; esperando fin EOP (< 2 V).",
    "stopping_process": "Apagando proceso de forma segura.",
    "venting": "Venteando cámara; esperando ATM estable.",
    "completed": "Receta completada.",
    "error": "Receta finalizada con error.",
}
ACTIVE_RECIPE_LABEL = "Receta activa"
NO_ACTIVE_RECIPE = "Ninguna"
RECIPE_EDITOR_TITLE = "Nueva receta"
RECIPE_VIEW_TITLE = "Visualizar receta"
RECIPE_NAME_LABEL = "Nombre"
RECIPE_DESCRIPTION_LABEL = "Descripción"
RECIPE_O2_FLOW_LABEL = "Flujo de O₂"
RECIPE_N2_FLOW_LABEL = "Flujo de N₂"
RECIPE_BASE_PRESSURE_LABEL = "Presión base"
RECIPE_PROCESS_PRESSURE_LABEL = "Presión de proceso"
RECIPE_PROCESS_TEMPERATURE_LABEL = "Temperatura de proceso"
RECIPE_RF_MAX_ON_TIME_LABEL = "Tiempo máximo de encendido de RF"
RECIPE_SAVE_DIALOG_TITLE = "Guardar receta"
RECIPE_LOAD_DIALOG_TITLE = "Cargar receta"
RECIPE_FILE_FILTER = "Recetas (*.txt)"
RECIPE_SAVE_BUTTON = "Guardar"
RECIPE_CANCEL_BUTTON = "Cancelar"
RECIPE_CLOSE_BUTTON = "Cerrar"
RECIPE_EDIT_BUTTON = "Editar receta"
RECIPE_OVERWRITE_TITLE = "Confirmar sobrescritura"
RECIPE_OVERWRITE_MESSAGE = "Ya existe una receta con ese nombre. ¿Desea reemplazarla?"
RECIPE_NO_ACTIVE_TITLE = "Sin receta activa"
RECIPE_NO_ACTIVE_MESSAGE = "Cree o cargue una receta antes de continuar."
RECIPE_INVALID_TITLE = "Receta no válida"
RECIPE_ERROR_NAME_REQUIRED = "El nombre de la receta es obligatorio."
RECIPE_ERROR_INVALID_VALUES = "Todos los parámetros deben contener números válidos."
RECIPE_ERROR_NONNEGATIVE = "Los parámetros deben ser finitos y no negativos."
RECIPE_ERROR_O2_RANGE = "El flujo de O₂ debe estar entre 0 y 10 SLPM."
RECIPE_ERROR_N2_RANGE = "El flujo de N₂ debe estar entre 0 y 1 SLPM."
RECIPE_ERROR_PROCESS_PRESSURE_RANGE = "La presión de proceso debe estar entre 0 y 3 Torr."
RECIPE_ERROR_BASE_PRESSURE_RANGE = "La presión base debe estar entre 0 y 3 Torr."
RECIPE_ERROR_PROCESS_TEMPERATURE_RANGE = "La temperatura de proceso debe estar entre 130 y 200 °C."
RECIPE_ERROR_RF_TIME_RANGE = "El tiempo máximo de RF debe ser un número entero entre 1 y 120 segundos (2 minutos)."
RECIPE_ERROR_PRESSURE_UNAVAILABLE = "No hay una lectura actual de presión de cámara para definir el mínimo de presión base."
RECIPE_ERROR_BASE_PRESSURE_MINIMUM = "La presión de cámara debe ser de 3 Torr o menos antes de guardar la receta."
RECIPE_VALUES_CLAMPED_MESSAGE = "Estos valores estaban fuera de rango y se ajustaron al límite permitido:\n{details}\nRevise los valores y pulse Guardar nuevamente para guardar la receta."
RECIPE_VALUE_RANGE_DETAIL = "{label}: ingresado {value} {unit}; rango permitido {minimum}–{maximum} {unit}."
RECIPE_ERROR_INVALID_LOCATION = "Las recetas deben estar dentro de la carpeta recipies."
RECIPE_ERROR_FILE_NOT_FOUND = "No se encontró un archivo de receta .txt."
RECIPE_ERROR_READ = "No se pudo leer la receta. Verifique el archivo y sus permisos."
RECIPE_ERROR_SECTIONS = "El archivo debe contener las secciones [RECIPE] y [PARAMETERS]."
RECIPE_ERROR_METADATA = "La receta debe incluir un nombre y una descripción válidos."
RECIPE_ERROR_PARAMETERS = "La receta está incompleta o contiene parámetros no numéricos."
RECIPE_ERROR_FILENAME = "El nombre no permite generar un nombre de archivo válido."
RECIPE_ERROR_TEMPLATE_PROTECTED = "La plantilla está protegida. Guarde la receta con otro nombre."
RECIPE_ERROR_WRITE = "No se pudo guardar la receta. Verifique los permisos de la carpeta."


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
STATISTICS_LOAD_DATA_TEXT = "Cargar datos"
STATISTICS_NO_DATA = "No hay datos guardados de una receta ejecutada."
STATISTICS_LOAD_ERROR = "No se pudo cargar el archivo: {filename}"


# =============================================================================
# Navegación
# =============================================================================

BACK_BUTTON_TEXT = "Volver"


# =============================================================================
# Pantalla de mantenimiento
# =============================================================================

MAINTAINER_SECUENCES_TAB = "Modulos"
MAINTAINER_SIGNALS_TAB = "DIO"
MAINTAINER_MFC_TITLE = "Control de MFC"
MAINTAINER_APPLY_FLOW = "Aplicar flujo"
MAINTAINER_OPEN_VALVE = "Abrir válvula"
MAINTAINER_CLOSE_VALVE = "Cerrar válvula"
MAINTAINER_THROTTLE_TITLE = "Throttle · movimiento manual"
MAINTAINER_THROTTLE_OPEN = "Abrir throttle"
MAINTAINER_THROTTLE_CLOSE = "Cerrar throttle"
MAINTAINER_PRESSURE_TITLE = "Control automático de presión"
MAINTAINER_PRESSURE_SETPOINT = "Setpoint:"
MAINTAINER_PRESSURE_START = "Iniciar control"
MAINTAINER_PRESSURE_STOP = "Detener control"
MAINTAINER_PRESSURE_CURRENT = "Presión actual: {pressure:.3f} Torr"
MAINTAINER_PRESSURE_CURRENT_UNAVAILABLE = "Presión actual: sin lectura"
MAINTAINER_PRESSURE_IDLE = "Control detenido"
MAINTAINER_PRESSURE_POSITIONING = "Posicionando throttle a 400 pasos desde apertura..."
MAINTAINER_PRESSURE_RUNNING = "Control de presión activo"
MAINTAINER_PRESSURE_ERROR = "Control detenido: {message}"
MAINTAINER_TEMPERATURE_TITLE = "Control automático de temperatura"
MAINTAINER_TEMPERATURE_SETPOINT = "Setpoint:"
MAINTAINER_TEMPERATURE_START = "Iniciar control térmico"
MAINTAINER_TEMPERATURE_STOP = "Detener control térmico"
MAINTAINER_TEMPERATURE_CURRENT = "Temperatura actual: {temperature:.1f} °C"
MAINTAINER_TEMPERATURE_CURRENT_UNAVAILABLE = "Temperatura actual: sin lectura"
MAINTAINER_TEMPERATURE_IDLE = "Control térmico detenido"
MAINTAINER_TEMPERATURE_RAMP = "Precalentando con las tres lámparas..."
MAINTAINER_TEMPERATURE_HOLD = "Manteniendo temperatura con histéresis"
MAINTAINER_TEMPERATURE_ERROR = "Control térmico detenido: {message}"
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
SIGNAL_STATE_WARNING = "ADVERTENCIA"
SIGNAL_STATE_FAULT = "FALLA"
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
DEVELOPER_NAMES = ("Pablo M. Leiva", "Carolina V. Kupcevich")
TUTOR_NAMES = ("Ing. Andres L. Di Donato", "Nombre del tutor 2")

_ACTIVE_LANGUAGE = "es"
_SPANISH_TO_ENGLISH = {
    "Software de control": "Control software",
    "Operación normal": "Normal operation",
    "Mantenimiento": "Maintenance",
    "Estadísticas": "Statistics",
    "OPERACIÓN NORMAL": "NORMAL OPERATION",
    "MODO SIMULADO": "SIMULATION MODE",
    "Las lecturas provienen del backend activo. El diagrama y la gestión de recetas están pendientes.": "Readings come from the active backend. The schematic and recipe management are pending.",
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
    "Lecturas analógicas": "Analog readings",
    "T Cámara": "Chamber T",
    "P Cámara": "Chamber P",
    "MFC1 · O₂": "MFC1 · O₂",
    "MFC2 · N₂": "MFC2 · N₂",
    "End Point": "End Point",
    "Nivel de RF": "RF level",
    "Esperando lectura": "Waiting for reading",
    "No disponible": "Unavailable",
    "Lectura recibida": "Reading received",
    "Error de lectura": "Reading error",
    "Esquema del equipo": "Equipment schematic",
    "No se pudo cargar el diagrama del equipo.": "The equipment diagram could not be loaded.",
    "Recetas": "Recipes",
    "Nueva receta": "New recipe",
    "Iniciar receta": "Start recipe",
    "Detener receta": "Stop recipe",
    "Registro guardado en:\n{path}": "Recipe log saved at:\n{path}",
    "No se pudo guardar el registro. Ruta intentada:\n{path}": "Could not save the recipe log. Attempted path:\n{path}",
    "Datos de presión y temperatura guardados en:\n{path}": "Pressure and temperature data saved at:\n{path}",
    "No se pudieron guardar los datos de presión y temperatura. Ruta intentada:\n{path}": "Could not save pressure and temperature data. Attempted path:\n{path}",
    "Sin receta en ejecuciÃ³n.": "No recipe is running.",
    "Confirmar inicio de receta": "Confirm recipe start",
    "Carga de oblea": "Wafer loading",
    "Inserte la oblea en la cÃ¡mara y confirme para continuar.": "Insert the wafer into the chamber and confirm to continue.",
    "Esperando confirmaciÃ³n de carga de oblea.": "Waiting for wafer loading confirmation.",
    "Cerrando puerta.": "Closing door.",
    "Esperando confirmaciÃ³n de puerta cerrada.": "Waiting for door closed confirmation.",
    "Retiro de oblea": "Wafer removal",
    "¿Retiró la oblea de la cámara? Sí cierra la puerta; No finaliza la receta y deja la puerta abierta.": "Have you removed the wafer from the chamber? Yes closes the door; No ends the recipe and leaves the door open.",
    "Esperando confirmación de retiro de oblea.": "Waiting for wafer removal confirmation.",
    "Cerrando puerta después de retirar la oblea.": "Closing the door after wafer removal.",
    "Verificando el cierre de la puerta para finalizar.": "Verifying the door is closed before finishing.",
    "Iniciando Soft Vacuum.": "Starting Soft Vacuum.",
    "Iniciando Main Vacuum.": "Starting Main Vacuum.",
    "Esperando presiÃ³n base.": "Waiting for base pressure.",
    "Configurando caudales de gases.": "Setting gas flows.",
    "Regulando presiÃ³n de proceso.": "Controlling process pressure.",
    "Regulando temperatura.": "Controlling temperature.",
    "Proceso de plasma en curso; esperando fin EOP (< 2 V).": "Plasma process running; waiting for EOP end (< 2 V).",
    "Apagando proceso de forma segura.": "Safely shutting down process.",
    "Venteando cÃ¡mara; esperando ATM estable.": "Venting chamber; waiting for stable ATM.",
    "Receta completada.": "Recipe completed.",
    "Receta finalizada con error.": "Recipe finished with an error.",
    "Visualizar receta": "View recipe",
    "Pendiente de integrar las recetas y la secuencia real del proceso.": "Recipe handling and the real process sequence have not been integrated yet.",
    "Receta activa": "Active recipe",
    "Ninguna": "None",
    "Nueva receta": "New recipe",
    "Visualizar receta": "View recipe",
    "Nombre": "Name",
    "Descripción": "Description",
    "Flujo de O₂": "O₂ flow",
    "Flujo de N₂": "N₂ flow",
    "Presión base": "Base pressure",
    "Presión de proceso": "Process pressure",
    "Temperatura de proceso": "Process temperature",
    "Guardar": "Save",
    "Cancelar": "Cancel",
    "Cerrar": "Close",
    "Editar receta": "Edit recipe",
    "Recetas (*.txt)": "Recipes (*.txt)",
    "Confirmar sobrescritura": "Confirm overwrite",
    "Ya existe una receta con ese nombre. ¿Desea reemplazarla?": "A recipe with that name already exists. Do you want to replace it?",
    "Sin receta activa": "No active recipe",
    "Cree o cargue una receta antes de continuar.": "Create or load a recipe before continuing.",
    "Receta no válida": "Invalid recipe",
    "El nombre de la receta es obligatorio.": "Recipe name is required.",
    "Todos los parámetros deben contener números válidos.": "All parameters must contain valid numbers.",
    "Los parámetros deben ser finitos y no negativos.": "Parameters must be finite and non-negative.",
    "El flujo de O₂ debe estar entre 0 y 10 SLPM.": "O₂ flow must be between 0 and 10 SLPM.",
    "El flujo de N₂ debe estar entre 0 y 1 SLPM.": "N₂ flow must be between 0 and 1 SLPM.",
    "No hay una lectura actual de presión de cámara para definir el mínimo de presión base.": "A current chamber pressure reading is required to set the minimum base pressure.",
    "La presión de cámara debe ser de 3 Torr o menos antes de guardar la receta.": "Chamber pressure must be 3 Torr or less before saving the recipe.",
    "Estos valores estaban fuera de rango y se ajustaron al límite permitido:\n{details}\nRevise los valores y pulse Guardar nuevamente para guardar la receta.": "These values were out of range and have been adjusted to the allowed limit:\n{details}\nReview them and click Save again to save the recipe.",
    "{label}: ingresado {value} {unit}; rango permitido {minimum}–{maximum} {unit}.": "{label}: entered {value} {unit}; allowed range {minimum}–{maximum} {unit}.",
    "Las recetas deben estar dentro de la carpeta recipies.": "Recipes must be inside the recipies folder.",
    "No se encontró un archivo de receta .txt.": "Recipe .txt file was not found.",
    "No se pudo leer la receta. Verifique el archivo y sus permisos.": "Could not read the recipe. Check the file and permissions.",
    "El archivo debe contener las secciones [RECIPE] y [PARAMETERS].": "The file must contain [RECIPE] and [PARAMETERS] sections.",
    "La receta debe incluir un nombre y una descripción válidos.": "The recipe must include a valid name and description.",
    "La receta está incompleta o contiene parámetros no numéricos.": "The recipe is incomplete or contains non-numeric parameters.",
    "El nombre no permite generar un nombre de archivo válido.": "The name cannot be converted to a valid filename.",
    "La plantilla está protegida. Guarde la receta con otro nombre.": "The template is protected. Save the recipe with another name.",
    "No se pudo guardar la receta. Verifique los permisos de la carpeta.": "Could not save the recipe. Check folder permissions.",
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
    "Control automático de presión": "Automatic pressure control",
    "Setpoint:": "Setpoint:",
    "Iniciar control": "Start control",
    "Detener control": "Stop control",
    "Presión actual: sin lectura": "Current pressure: no reading",
    "Control detenido": "Control stopped",
    "Posicionando throttle a 400 pasos desde apertura...": "Positioning throttle 400 steps from open...",
    "Control de presión activo": "Pressure control active",
    "Control automático de temperatura": "Automatic temperature control",
    "Iniciar control térmico": "Start temperature control",
    "Detener control térmico": "Stop temperature control",
    "Temperatura actual: sin lectura": "Current temperature: no reading",
    "Control térmico detenido": "Temperature control stopped",
    "Precalentando con las tres lámparas...": "Preheating with all three lamps...",
    "Manteniendo temperatura con histéresis": "Maintaining temperature with hysteresis",
    "La presión de proceso debe estar entre 0 y 3 Torr.": "Process pressure must be between 0 and 3 Torr.",
    "La presión base debe estar entre 0 y 3 Torr.": "Base pressure must be between 0 and 3 Torr.",
    "La temperatura de proceso debe estar entre 130 y 200 °C.": "Process temperature must be between 130 and 200 °C.",
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
    "ADVERTENCIA": "WARNING",
    "FALLA": "FAULT",
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
    if value.startswith("Presión actual: "):
        return "Current pressure: " + value[len("Presión actual: "):]
    if value.startswith("Control detenido: "):
        return "Control stopped: " + value[len("Control detenido: "):]
    if value.startswith("Temperatura actual: "):
        return "Current temperature: " + value[len("Temperatura actual: "):]
    if value.startswith("Control térmico detenido: "):
        return "Temperature control stopped: " + value[len("Control térmico detenido: "):]
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


