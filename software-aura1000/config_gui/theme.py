"""
Configuración visual global de la aplicación.

Este archivo centraliza todos los colores y estilos utilizados por la GUI.
El objetivo es evitar valores hardcodeados y facilitar futuros cambios de
apariencia o la incorporación de distintos temas visuales.
"""

# =============================================================================
# Paleta de colores
# =============================================================================

# Colores principales
BACKGROUND_COLOR = "#1E1E1E"
SURFACE_COLOR = "#2B2B2B"
SURFACE_HOVER_COLOR = "#3A3A3A"
TEXTBOX_BACKGROUND_COLOR = "#252525"

PRIMARY_COLOR = "#0094FF"
DANGER_COLOR = "#D32F2F"

# Barra superior
TOP_BAR_COLOR = "#111111"


# Texto
TEXT_COLOR = "#EEEEEE"
TEXT_MUTED_COLOR = "#AAAAAA"

# =============================================================================
# Configuración de Textos
# =============================================================================
FONT_FAMILY = "Segoe UI"
BUTTON_FONT_SIZE = 18
TITLE_FONT_SIZE = 64 
SUBTITLE_FONT_SIZE = 24
TEXT_FONT_SIZE = 16

# =============================================================================
# Configuración de Botones
# =============================================================================
BORDER_W = 2
BORDER_RADIUS = 12

# ============================================================
# SignalWidget
# ============================================================
SIGNAL_ACTIVE_COLOR = "#2ECC71"
SIGNAL_INACTIVE_COLOR = "#707070"
SIGNAL_PROCESSING_COLOR = "#F1C40F"

SIGNAL_WIDGET_BORDER_RADIUS = 10
SIGNAL_LED_SIZE = 18
SIGNAL_LED_BORDER_RADIUS = SIGNAL_LED_SIZE // 2

# =============================================================================
# Hoja de estilos global (QSS)
# =============================================================================

APP_STYLE = f"""
/* -------------------------------------------------------------------------- */
/* Ventana principal                                                          */
/* -------------------------------------------------------------------------- */

QMainWindow {{
    background-color: {BACKGROUND_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Widgets generales                                                          */
/* -------------------------------------------------------------------------- */

QWidget {{
    background-color: {BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    font-family: FONT_FAMILY;
    font-size: {SUBTITLE_FONT_SIZE}px;
}}

/* -------------------------------------------------------------------------- */
/* Títulos                                                                    */
/* -------------------------------------------------------------------------- */

QLabel#TitleLabel {{
    font-size: {TITLE_FONT_SIZE}px;
    font-weight: bold;
    color: {TEXT_COLOR};
}}

QLabel#SubtitleLabel {{
    font-size: {SUBTITLE_FONT_SIZE}px;
    color: {TEXT_MUTED_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Barra superior                                                             */
/* -------------------------------------------------------------------------- */

QWidget#TopBar {{
    background-color: {TOP_BAR_COLOR};
    border-bottom: {BORDER_W}px solid {PRIMARY_COLOR};
}}

QLabel#TopBarTitle {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: {SUBTITLE_FONT_SIZE}px;
    font-weight: bold;
}}

/* -------------------------------------------------------------------------- */
/* Botones                                                                    */
/* -------------------------------------------------------------------------- */

QPushButton {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: {BORDER_W}px solid {PRIMARY_COLOR};
    border-radius: {BORDER_RADIUS}px;
    padding: 18px;   
    font-size: {BUTTON_FONT_SIZE}px;
}}

QPushButton:hover {{
    background-color: {SURFACE_HOVER_COLOR};
}}

QPushButton:pressed {{
    background-color: {PRIMARY_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Botón Exit                                                                 */
/* -------------------------------------------------------------------------- */

QPushButton#ExitButton {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: {BORDER_W}px solid {DANGER_COLOR};
    border-radius: {BORDER_RADIUS}px;
    padding: 8px 20px;
    font-size: {BUTTON_FONT_SIZE}px;
}}

QPushButton#ExitButton:hover {{
    background-color: {DANGER_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Login Dialog                                                               */
/* -------------------------------------------------------------------------- */

QDialog {{
    background-color: {BACKGROUND_COLOR};
}}

QLabel#LoginTitle {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: {SUBTITLE_FONT_SIZE}px;
    font-weight: bold;
}}

QLineEdit#LoginInput {{
    background-color: {TEXTBOX_BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    border: {BORDER_W}px solid {SURFACE_HOVER_COLOR};
    border-radius: {BORDER_RADIUS}px;
    padding: 10px 24px;
    font-size: {TEXT_FONT_SIZE}px;
}}

QLineEdit#LoginInput:focus {{
    border: {BORDER_W}px solid {PRIMARY_COLOR};
}}

QLabel#LoginErrorLabel {{
    background-color: transparent;
    color: {DANGER_COLOR};
    font-size: {TEXT_FONT_SIZE}px;
    font-weight: bold;
}}

QPushButton#LoginButton {{
    padding: 10px 24px;
    font-size: {BUTTON_FONT_SIZE}px;
}}

QPushButton#CancelButton {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: {BORDER_W}px solid {TEXT_MUTED_COLOR};
    border-radius: {BORDER_RADIUS}px;
    padding: 10px 24px;
    font-size: {BUTTON_FONT_SIZE}px;
}}

QPushButton#CancelButton:hover {{
    background-color: {SURFACE_HOVER_COLOR};
}}

/* -------------------------------------------------------------------------- */
/*   SignalWidget                                                             */
/* -------------------------------------------------------------------------- */

QFrame#signalWidget {{
    background-color: {BACKGROUND_COLOR};
    border: {BORDER_W}px solid {PRIMARY_COLOR};
    border-radius: {BORDER_RADIUS}px;
}}

QFrame#signalWidget[interactive="true"]:hover {{
    background-color: {SURFACE_COLOR};
    border-color: {PRIMARY_COLOR};
}}

QFrame#signalWidget[visualState="processing"] {{
    border-color: {SIGNAL_PROCESSING_COLOR};
}}

QLabel#signalNameLabel {{
    color: {TEXT_COLOR};
    background-color: transparent;
    border: none;
    font-size: {SUBTITLE_FONT_SIZE}px;
    font-weight: 600;
}}

QLabel#signalStatusLabel {{
    background-color: transparent;
    border: none;
    font-size: {TEXT_FONT_SIZE}px;
    font-weight: 600;
}}

QLabel#signalLedIndicator {{
    min-width: {SIGNAL_LED_SIZE}px;
    max-width: {SIGNAL_LED_SIZE}px;
    min-height: {SIGNAL_LED_SIZE}px;
    max-height: {SIGNAL_LED_SIZE}px;
    border-radius: {SIGNAL_LED_BORDER_RADIUS}px;
}}


/* ACTIVE */

QLabel#signalLedIndicator[visualState="active"] {{
    background-color: {SIGNAL_ACTIVE_COLOR};
    border: {BORDER_W}px solid {SIGNAL_ACTIVE_COLOR};
}}

QLabel#signalStatusLabel[visualState="active"] {{
    color: {SIGNAL_ACTIVE_COLOR};
}}


/* INACTIVE */

QLabel#signalLedIndicator[visualState="inactive"] {{
    background-color: {SIGNAL_INACTIVE_COLOR};
    border: {BORDER_W}px solid {SIGNAL_INACTIVE_COLOR};
}}

QLabel#signalStatusLabel[visualState="inactive"] {{
    color: {SIGNAL_INACTIVE_COLOR};
}}


/* PROCESSING */

QLabel#signalLedIndicator[visualState="processing"] {{
    background-color: {SIGNAL_PROCESSING_COLOR};
    border: {BORDER_W}px solid {SIGNAL_PROCESSING_COLOR};
}}

QLabel#signalStatusLabel[visualState="processing"] {{
    color: {SIGNAL_PROCESSING_COLOR};
}}


"""