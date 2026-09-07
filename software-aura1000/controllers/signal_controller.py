"""
Controlador de señales digitales.

SignalController actúa como intermediario entre MaintainerScreen y la capa
de servicios de hardware.

Responsabilidades:
- Leer periódicamente las señales digitales configuradas.
- Mantener el último estado confirmado de cada señal.
- Procesar solicitudes de cambio sobre señales de salida.
- Informar a la GUI cuando cambia el estado de una señal.
- Informar cuando una salida se encuentra en procesamiento.
- Capturar errores de lectura o escritura.

SignalController no:
- Crea ni modifica widgets directamente.
- Conoce colores, textos o estilos visuales.
- Accede a puertos, bits, ctypes o DLL.
- Utiliza directamente el driver de la placa.

La comunicación con el hardware se realiza exclusivamente mediante:
- hardware.digital_read(signal_name)
- hardware.digital_set(signal_name, active)
"""

from functools import partial
from typing import Dict, Iterable, Optional, Set

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
import time

class SignalController(QObject):
    """Gestiona el monitoreo y control lógico de señales digitales."""

    # Estado confirmado de una señal.
    # Argumentos: signal_name, active
    signal_state_changed = pyqtSignal(str, bool)

    # Informa que comenzó el procesamiento de una salida.
    # Argumento: signal_name
    signal_processing = pyqtSignal(str)

    # Informa un error asociado con una señal.
    # Argumentos: signal_name, error_message
    signal_error = pyqtSignal(str, str)

    def __init__(
        self,
        hardware,
        monitored_signals: Iterable[str],
        output_signals: Iterable[str],
        poll_interval_ms: int = 500,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        self._hardware = hardware

        self._monitored_signals = self._normalize_signals(
            monitored_signals
        )

        self._output_signals = self._normalize_signals(
            output_signals
        )

        self._poll_interval_ms = self._validate_poll_interval(
            poll_interval_ms
        )

        # Último estado confirmado de cada señal.
        self._signal_states: Dict[str, bool] = {}

        # Salidas que están siendo procesadas actualmente.
        self._processing_signals: Set[str] = set()

        self._validate_output_signals()

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(
            self._poll_interval_ms
        )

        self._poll_timer.timeout.connect(
            self._poll_signals
        )

    # =========================================================================
    # Control del monitoreo
    # =========================================================================

    def start_monitoring(self) -> None:
        """Inicia la lectura periódica de las señales.

        Se realiza una primera lectura inmediatamente para que la GUI no deba
        esperar al primer timeout del temporizador.
        """

        if self._poll_timer.isActive():
            return

        self._poll_signals()
        self._poll_timer.start()

    def stop_monitoring(self) -> None:
        """Detiene la lectura periódica de las señales."""

        self._poll_timer.stop()

    def refresh_signals(self) -> None:
        """Realiza una lectura inmediata de todas las señales."""

        self._poll_signals()

    @property
    def is_monitoring(self) -> bool:
        """Indica si el monitoreo periódico se encuentra activo."""

        return self._poll_timer.isActive()

    # =========================================================================
    # Solicitudes sobre salidas
    # =========================================================================

    def request_toggle(
        self,
        signal_name: str,
    ) -> None:
        """Solicita invertir el estado actual de una salida digital.

        El widget no cambia su estado directamente. El controlador:

        1. Obtiene el último estado confirmado.
        2. Emite signal_processing.
        3. Solicita el nuevo estado al Hardware Service.
        4. Lee nuevamente la señal.
        5. Emite signal_state_changed con el estado confirmado.
        """

        self._validate_signal_name(signal_name)

        if signal_name not in self._output_signals:
            self.signal_error.emit(
                signal_name,
                "La señal no está configurada como salida.",
            )
            return

        # Ignora solicitudes repetidas mientras la salida está procesándose.
        if signal_name in self._processing_signals:
            return

        try:
            current_state = self._get_current_state(
                signal_name
            )

        except Exception as error:
            self._emit_error(
                signal_name,
                "No fue posible obtener el estado actual",
                error,
            )
            return

        requested_state = not current_state

        self._processing_signals.add(signal_name)

        # MaintainerScreen utilizará esta señal para mostrar PROCESANDO...
        self.signal_processing.emit(signal_name)

        # La operación se ejecuta en el siguiente ciclo del event loop.
        # Esto permite que Qt tenga oportunidad de repintar PROCESSING
        # antes de iniciar la escritura.
        operation = partial(
            self._execute_output_change,
            signal_name,
            requested_state,
        )

        QTimer.singleShot(0, operation)  #cambiar 1000 a 0 - testing

    def _execute_output_change(
        self,
        signal_name: str,
        requested_state: bool,
    ) -> None:
        """Ejecuta y confirma el cambio solicitado sobre una salida."""
        
        try:
            self._hardware.digital_set(
                signal_name,
                requested_state,
            )
            
            # La escritura no se considera confirmada únicamente porque
            # digital_set() terminó. Se realiza una lectura posterior.
            confirmed_state = self._hardware.digital_read(
                signal_name
            )

            confirmed_state = self._validate_read_value(
                signal_name,
                confirmed_state,
            )

            self._update_confirmed_state(
                signal_name,
                confirmed_state,
                force_emit=True,
            )

        except Exception as error:
            self._emit_error(
                signal_name,
                "No fue posible modificar la salida",
                error,
            )

            # Si ya existía un estado válido, se vuelve a emitir para que
            # SignalWidget abandone PROCESSING y muestre el último estado
            # confirmado.
            if signal_name in self._signal_states:
                self.signal_state_changed.emit(
                    signal_name,
                    self._signal_states[signal_name],
                )

        finally:
            self._processing_signals.discard(
                signal_name
            )

    # =========================================================================
    # Lectura periódica
    # =========================================================================

    def _poll_signals(self) -> None:
        """Lee todas las señales configuradas para monitoreo."""
        for signal_name in self._monitored_signals:

            # Una salida en procesamiento se actualiza mediante
            # _execute_output_change(), por lo que el polling la ignora
            # temporalmente.
            if signal_name in self._processing_signals:
                continue

            try:
                active = self._hardware.digital_read(
                    signal_name
                )

                active = self._validate_read_value(
                    signal_name,
                    active,
                )

                self._update_confirmed_state(
                    signal_name,
                    active,
                )

            except Exception as error:
                self._emit_error(
                    signal_name,
                    "Error durante la lectura",
                    error,
                )

            active = self._hardware.digital_read(
                signal_name
            )

            """ print(
                f"[SignalController] READ "
                f"{signal_name}: {active}"
            ) """
        
    # =========================================================================
    # Gestión de estados
    # =========================================================================

    def _get_current_state(
        self,
        signal_name: str,
    ) -> bool:
        """Obtiene el último estado confirmado de una señal.

        Si todavía no existe un valor almacenado, realiza una lectura
        inmediata del hardware.
        """

        if signal_name in self._signal_states:
            return self._signal_states[signal_name]

        active = self._hardware.digital_read(
            signal_name
        )

        active = self._validate_read_value(
            signal_name,
            active,
        )

        self._update_confirmed_state(
            signal_name,
            active,
        )

        return active

    def _update_confirmed_state(
        self,
        signal_name: str,
        active: bool,
        force_emit: bool = False,
    ) -> None:
        """Almacena y comunica un estado confirmado.

        Normalmente solo se emite signal_state_changed si el valor cambió.

        ``force_emit`` se utiliza después de una escritura para asegurar que
        la GUI abandone el estado PROCESSING incluso si el valor confirmado
        coincide con el anterior.
        """

        previous_state = self._signal_states.get(
            signal_name
        )

        self._signal_states[signal_name] = active

        state_changed = (
            previous_state is None
            or previous_state != active
        )

        if state_changed or force_emit:
            self.signal_state_changed.emit(
                signal_name,
                active,
            )

    def get_last_state(
        self,
        signal_name: str,
    ) -> Optional[bool]:
        """Devuelve el último estado confirmado disponible."""

        self._validate_signal_name(signal_name)

        return self._signal_states.get(
            signal_name
        )

    def is_processing(
        self,
        signal_name: str,
    ) -> bool:
        """Indica si una salida está siendo procesada."""

        self._validate_signal_name(signal_name)

        return (
            signal_name
            in self._processing_signals
        )

    # =========================================================================
    # Manejo de errores
    # =========================================================================

    def _emit_error(
        self,
        signal_name: str,
        context: str,
        error: Exception,
    ) -> None:
        """Emite un mensaje de error asociado con una señal."""

        detail = str(error).strip()

        if detail:
            message = f"{context}: {detail}"
        else:
            message = context

        self.signal_error.emit(
            signal_name,
            message,
        )

    # =========================================================================
    # Validaciones
    # =========================================================================

    def _validate_signal_name(
        self,
        signal_name: str,
    ) -> None:
        """Verifica que una señal pertenezca al conjunto monitoreado."""

        if signal_name not in self._monitored_signals:
            raise KeyError(
                f"La señal '{signal_name}' no está registrada "
                "en SignalController."
            )

    def _validate_output_signals(self) -> None:
        """Verifica que todas las salidas sean también monitoreadas."""

        unknown_outputs = (
            self._output_signals
            - self._monitored_signals
        )

        if not unknown_outputs:
            return

        signal_names = ", ".join(
            sorted(unknown_outputs)
        )

        raise ValueError(
            "Las siguientes salidas no están incluidas en "
            f"monitored_signals: {signal_names}"
        )

    @staticmethod
    def _normalize_signals(
        signals: Iterable[str],
    ) -> Set[str]:
        """Normaliza una colección de nombres de señales."""

        if isinstance(signals, str):
            raise TypeError(
                "Se esperaba una colección de señales, "
                "no una cadena individual."
            )

        normalized = set()

        for signal_name in signals:
            if not isinstance(signal_name, str):
                raise TypeError(
                    "Los nombres de señal deben ser cadenas."
                )

            clean_name = signal_name.strip()

            if not clean_name:
                raise ValueError(
                    "El nombre de una señal no puede estar vacío."
                )

            normalized.add(clean_name)

        if not normalized:
            raise ValueError(
                "La colección de señales no puede estar vacía."
            )

        return normalized

    @staticmethod
    def _validate_poll_interval(
        poll_interval_ms: int,
    ) -> int:
        """Valida el intervalo utilizado por el QTimer."""

        if not isinstance(poll_interval_ms, int):
            raise TypeError(
                "'poll_interval_ms' debe ser un entero."
            )

        if poll_interval_ms <= 0:
            raise ValueError(
                "'poll_interval_ms' debe ser mayor que cero."
            )

        return poll_interval_ms

    @staticmethod
    def _validate_read_value(
        signal_name: str,
        value,
    ) -> bool:
        """Verifica el contrato de Hardware.digital_read()."""

        if not isinstance(value, bool):
            raise TypeError(
                f"digital_read('{signal_name}') debe devolver bool, "
                f"pero devolvió {type(value).__name__}."
            )

        return value