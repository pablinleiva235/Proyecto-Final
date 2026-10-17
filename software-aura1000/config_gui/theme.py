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
SURFACE_DISABLED_COLOR = "#555555"
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

QLabel#TopBarDate {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: {TEXT_FONT_SIZE}px;
    font-weight: 500;
}}

QLabel#TopBarTime {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: {TEXT_FONT_SIZE}px;
    font-weight: bold;
    min-width: 80px;
}}

QFrame#OperationCard {{
    background-color: {SURFACE_COLOR};
    border: 2px solid {SURFACE_HOVER_COLOR};
    border-radius: 12px;
}}

QFrame#OperationCard QLabel {{
    background-color: transparent;
    font-size: 14px;
}}

QFrame#OperationStatusCard {{
    background-color: {SURFACE_COLOR};
    border: 2px solid {SURFACE_HOVER_COLOR};
    border-radius: 10px;
}}

QLabel#OperationStatusTitle {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: 13px;
    font-weight: 600;
}}

QFrame#OperationStatusCard QLabel#DemoStatusGood {{
    font-size: 14px;
}}

QLabel#NormalOperationTitle {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 32px;
    font-weight: bold;
}}

QLabel#OperationCardTitle {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 17px;
    font-weight: bold;
}}

QLabel#SimulationBadge {{
    background-color: #6B4E00;
    color: #FFF2C2;
    border: 2px solid #D9A400;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 16px;
    font-weight: bold;
}}

QLabel#SimulationDescription {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: 14px;
}}

QLabel#DemoValue {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 26px;
    font-weight: bold;
}}

QLabel#DemoValueSmall {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 14px;
    font-weight: 600;
}}

QLabel#SetpointLabel {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 14px;
    font-weight: 600;
}}

QLabel#SetpointUnit {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: 13px;
}}

QLabel#SetpointFeedback {{
    background-color: transparent;
    color: {TEXT_MUTED_COLOR};
    font-size: 12px;
}}

QLabel#SetpointFeedback[valid="true"] {{
    color: {SIGNAL_ACTIVE_COLOR};
}}

QLabel#SetpointFeedback[valid="false"] {{
    color: {DANGER_COLOR};
}}

QLineEdit[objectName^="SetpointInput_"] {{
    background-color: {TEXTBOX_BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    border: 2px solid {SURFACE_HOVER_COLOR};
    border-radius: 8px;
    padding: 8px;
    font-size: 16px;
}}

QLineEdit[objectName^="SetpointInput_"]:focus {{
    border-color: {PRIMARY_COLOR};
}}

QLabel#DigitalStatusLabel {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 13px;
}}

QLabel#DigitalStatusValue {{
    background-color: #173D2B;
    color: {SIGNAL_ACTIVE_COLOR};
    border: 1px solid {SIGNAL_ACTIVE_COLOR};
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    font-weight: bold;
}}

QLabel#DemoStatus {{
    background-color: transparent;
    color: #F1C40F;
    font-size: 14px;
    font-weight: bold;
}}

QLabel#DemoStatusGood {{
    background-color: transparent;
    color: {SIGNAL_ACTIVE_COLOR};
    font-size: 16px;
    font-weight: bold;
}}

QPushButton#DemoActionButton {{
    padding: 6px 12px;
    font-size: 14px;
}}

QPushButton#RecipeActionButton {{
    padding: 10px 20px;
    font-size: 16px;
    min-height: 42px;
}}

QPushButton#SetpointStepButton {{
    padding: 4px;
    font-size: 18px;
    font-weight: bold;
}}

QPushButton#BackButton {{
    padding: 10px 22px;
    font-size: 16px;
}}

/* -------------------------------------------------------------------------- */
/* Botón de configuración                                                     */
/* -------------------------------------------------------------------------- */

QPushButton#SettingsButton {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: 2px solid {PRIMARY_COLOR};
    border-radius: 8px;
    padding: 8px 14px;
    font-size: {BUTTON_FONT_SIZE}px;
}}

QPushButton#SettingsButton:hover {{
    background-color: {SURFACE_HOVER_COLOR};
}}

/* -------------------------------------------------------------------------- */
/* Startup Screen                                                             */
/* -------------------------------------------------------------------------- */

QLabel#StartupTitleLabel {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 42px;
    font-weight: bold;
}}

QLabel#StartupMessageLabel {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 26px;
}}

QLabel#StartupErrorLabel {{
    background-color: transparent;
    color: {DANGER_COLOR};
    font-size: 20px;
    font-weight: bold;
}}

QProgressBar#StartupProgressBar {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_COLOR};
    border: 2px solid {PRIMARY_COLOR};
    border-radius: 8px;
    text-align: center;
    min-height: 28px;
}}

QProgressBar#StartupProgressBar::chunk {{
    background-color: {PRIMARY_COLOR};
    border-radius: 6px;
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

QPushButton:disabled {{
    border: {SURFACE_DISABLED_COLOR};
    color: {TEXT_MUTED_COLOR};
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

/* ========================================================================== */
/* MaintainerScreen - Tabs                                                    */
/* ========================================================================== */

QTabWidget#MaintainerTabs::pane {{
    background-color: {BACKGROUND_COLOR};
    border: 2px solid {SURFACE_HOVER_COLOR};
    border-radius: 8px;
    top: -1px;
}}

QTabWidget#MaintainerTabs QTabBar::tab {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_MUTED_COLOR};

    border: 2px solid {SURFACE_HOVER_COLOR};
    border-bottom: none;

    padding: 12px 28px;
    margin-right: 4px;

    min-width: 180px;

    font-size: 18px;
    font-weight: bold;
}}

QTabWidget#MaintainerTabs QTabBar::tab:selected {{
    background-color: {PRIMARY_COLOR};
    color: {TEXT_COLOR};

    border-color: {PRIMARY_COLOR};
}}

QTabWidget#MaintainerTabs QTabBar::tab:!selected {{
    margin-top: 4px;
}}

QTabWidget#MaintainerTabs QTabBar::tab:hover {{
    background-color: {SURFACE_HOVER_COLOR};
    color: {TEXT_COLOR};
}}

QPushButton#MFCControlButton {{
    padding: 6px 12px;
    font-size: 15px;
}}

/* -------------------------------------------------------------------------- */
/*   SignalWidget                                                             */
/* -------------------------------------------------------------------------- */

QFrame#signalWidget {{
    background-color: #0B0F2A;
    border: 1px solid #26345C;
    border-radius: 18px;
}}

QFrame#signalWidget[interactive="true"]:hover {{
    background-color: {SURFACE_COLOR};
    border-color: {PRIMARY_COLOR};
}}

QFrame#signalWidget[visualState="processing"] {{
    border-color: {SIGNAL_PROCESSING_COLOR};
}}

QFrame#signalWidget[error="true"] {{
    border-color: #FF7B83;
}}

QLabel#signalNameLabel {{
    color: {TEXT_COLOR};
    background-color: transparent;
    border: none;
    font-size: 17px;
    font-weight: 600;
}}

QLabel#signalStatusLabel {{
    background-color: #202B45;
    color: #B8C6E4;
    border-radius: 12px;
    padding: 5px 10px;
    border: none;
    font-size: 12px;
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
    color: #55E0AE;
    background-color: #143B35;
}}


/* INACTIVE */

QLabel#signalLedIndicator[visualState="inactive"] {{
    background-color: {SIGNAL_INACTIVE_COLOR};
    border: {BORDER_W}px solid {SIGNAL_INACTIVE_COLOR};
}}

QLabel#signalStatusLabel[visualState="inactive"] {{
    color: #AAB6D0;
    background-color: #202B45;
}}


/* PROCESSING */

QLabel#signalLedIndicator[visualState="processing"] {{
    background-color: {SIGNAL_PROCESSING_COLOR};
    border: {BORDER_W}px solid {SIGNAL_PROCESSING_COLOR};
}}

QLabel#signalStatusLabel[visualState="processing"] {{
    color: #FFD166;
    background-color: #4A3B1E;
}}

QLabel#signalKindIcon {{
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    border-radius: 18px;
    background-color: #123B4B;
    color: #55DDF0;
    font-size: 11px;
    font-weight: bold;
}}

QLabel#signalFooterLabel, QLabel#MaintenanceCardFooter {{
    background-color: transparent;
    color: #9BA9C7;
    font-size: 12px;
}}

QFrame#MaintenanceCard, QFrame#MFCControlCard {{
    background-color: #0B0F2A;
    border: 1px solid #26345C;
    border-radius: 18px;
}}

QGroupBox#MaintainerCardGroup {{
    background-color: #0B0F2A;
    border: 1px solid #26345C;
    border-radius: 18px;
    margin-top: 20px;
    padding: 18px 12px 12px 12px;
    color: {TEXT_COLOR};
    font-size: 16px;
    font-weight: bold;
}}

QGroupBox#MaintainerCardGroup::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 6px;
    color: {TEXT_COLOR};
}}

QLabel#MaintenanceCardTitle {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 17px;
    font-weight: bold;
}}

QLabel#MaintenanceCardIcon {{
    min-width: 42px;
    max-width: 42px;
    min-height: 42px;
    max-height: 42px;
    border-radius: 21px;
    background-color: #123B4B;
    color: #55DDF0;
    font-size: 13px;
    font-weight: bold;
}}

QLabel#MaintenanceCardValue {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-size: 27px;
    font-weight: bold;
}}

QLabel#MaintenanceCardValue[error="true"] {{
    color: #FF7B83;
}}

QLabel#MaintenanceCardUnit {{
    background-color: transparent;
    color: #C4CCE0;
    font-size: 13px;
}}

QLabel#MaintenancePill, QLabel#MaintenancePill[state="inactive"] {{
    background-color: #202B45;
    color: #B8C6E4;
    border: none;
    border-radius: 12px;
    padding: 5px 10px;
    font-size: 11px;
    font-weight: bold;
}}

QLabel#MaintenancePill[state="active"] {{
    background-color: #143B35;
    color: #55E0AE;
}}

QLabel#MaintenancePill[state="error"] {{
    background-color: #4A202A;
    color: #FF9299;
}}

QLabel#MaintenancePill[state="info"] {{
    background-color: #123B4B;
    color: #55DDF0;
}}

QProgressBar#MFCFlowProgress {{
    min-height: 8px;
    max-height: 8px;
    border: none;
    border-radius: 4px;
    background-color: #202B45;
}}

QProgressBar#MFCFlowProgress::chunk {{
    border-radius: 4px;
    background-color: #35D7E8;
}}

QPushButton#MFCControlButton {{
    background-color: #172342;
    border: 1px solid #35D7E8;
    border-radius: 9px;
    color: {TEXT_COLOR};
    padding: 7px 12px;
    font-size: 14px;
}}

QPushButton#MaintainerSequenceButton {{
    background-color: #111831;
    border: 1px solid #26345C;
    border-radius: 14px;
    color: {TEXT_COLOR};
    padding: 14px 16px;
    font-size: 16px;
    font-weight: 600;
}}

QPushButton#MaintainerSequenceButton:hover {{
    background-color: #172342;
    border-color: #35D7E8;
}}

QPushButton#MaintainerSequenceButton:disabled {{
    background-color: #141A2C;
    color: #8792AC;
    border-color: #30384B;
}}

QPushButton#MaintainerSequenceButton:pressed {{
    background-color: #123B4B;
}}

QPushButton#MaintenanceActionButton {{
    padding: 8px 12px;
    font-size: 14px;
}}

QDoubleSpinBox#MaintenanceSetpointInput {{
    background-color: #111831;
    color: {TEXT_COLOR};
    border: 1px solid #3A4A70;
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 14px;
}}

QDialog#SettingsDialog {{
    background-color: {SURFACE_COLOR};
}}

QComboBox#SettingsCombo {{
    background-color: {TEXTBOX_BACKGROUND_COLOR};
    color: {TEXT_COLOR};
    border: 1px solid {SURFACE_HOVER_COLOR};
    border-radius: 8px;
    padding: 7px 10px;
    min-width: 140px;
}}

QPushButton#SettingsCloseButton {{
    padding: 8px 16px;
    font-size: 15px;
}}


"""


_LIGHT_THEME_REPLACEMENTS = {
    "#1E1E1E": "#F3F6FB",
    "#2B2B2B": "#FFFFFF",
    "#3A3A3A": "#DCE4EF",
    "#555555": "#C8D0DC",
    "#252525": "#FFFFFF",
    "#0094FF": "#087EB5",
    "#D32F2F": "#B42332",
    "#111111": "#E6EBF3",
    "#EEEEEE": "#17233A",
    "#AAAAAA": "#58647A",
    "#0B0F2A": "#FFFFFF",
    "#26345C": "#CFD8E6",
    "#202B45": "#E8EDF5",
    "#B8C6E4": "#3D4960",
    "#55E0AE": "#147D5B",
    "#143B35": "#D9F4E9",
    "#AAB6D0": "#46536B",
    "#FFD166": "#8A5B00",
    "#4A3B1E": "#FFF0C2",
    "#123B4B": "#DDF3FA",
    "#55DDF0": "#08789A",
    "#9BA9C7": "#65728A",
    "#111831": "#F5F8FC",
    "#172342": "#EAF3FB",
    "#8792AC": "#68758C",
    "#141A2C": "#E2E7EF",
    "#30384B": "#AAB5C5",
    "#35D7E8": "#078AAA",
    "#4A202A": "#FDE7E7",
    "#FF9299": "#A4262C",
    "#FF7B83": "#B42332",
    "#3A4A70": "#AEBBD0",
    "#173D2B": "#D9F4E9",
    "#2EC4B6": "#087EB5",
}


def build_app_style(theme="dark"):
    """Devuelve la hoja global para el tema claro u oscuro."""
    if theme == "dark":
        return APP_STYLE
    if theme != "light":
        raise ValueError("El tema debe ser 'light' o 'dark'.")
    stylesheet = APP_STYLE
    for dark_color, light_color in _LIGHT_THEME_REPLACEMENTS.items():
        stylesheet = stylesheet.replace(dark_color, light_color)
    return stylesheet
