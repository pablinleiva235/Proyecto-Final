from logic.door_sequence import DoorState
from logic.soft_vacuum_sequence import SoftVacuumState
from logic.main_vacuum_sequence import MainVacuumState
from logic.vent_sequence import VentState


class InterlockController:
    """
    Gestiona los interlocks de seguridad entre secuencias.
    """

    def __init__(
        self,
        door_sequence,
        soft_vacuum_sequence,
        main_vacuum_sequence,
        vent_sequence,
    ):
        self._vent_required = False
        self._door_sequence = door_sequence
        self._soft_vacuum_sequence = soft_vacuum_sequence
        self._main_vacuum_sequence = main_vacuum_sequence
        self._vent_sequence = vent_sequence

    # =====================================================================
    # Permisos de acciones
    # =====================================================================
    def can_open_door(self):
        """
        La puerta puede abrirse únicamente si:
        - Soft Vacuum está detenido.
        - Main Vacuum está detenido.
        - El venteo está detenido.
        """
        return (
            not self._vent_required
            and
            self._soft_vacuum_sequence.state == SoftVacuumState.IDLE
            and
            self._main_vacuum_sequence.state == MainVacuumState.IDLE
            and
            self._vent_sequence.state == VentState.IDLE
        )

    def can_start_soft_vacuum(self):
        """
        Soft Vacuum puede iniciarse únicamente si:
        - La puerta está cerrada.
        - Main Vacuum está detenido.
        - El venteo está detenido.
        """
        return (
            self._door_sequence.state == DoorState.CLOSED
            and
            self._main_vacuum_sequence.state == MainVacuumState.IDLE
            and
            self._vent_sequence.state == VentState.IDLE
        )

    def can_start_main_vacuum(self):
        """
        Main Vacuum puede iniciarse únicamente si:
        - La puerta está cerrada.
        - Soft Vacuum está funcionando.
        - El venteo está detenido.
        """
        return (
            self._door_sequence.state == DoorState.CLOSED
            and
            self._soft_vacuum_sequence.state == SoftVacuumState.RUNNING
            and
            self._vent_sequence.state == VentState.IDLE
        )

    def can_stop_main_vacuum(self):
        """
        Determina si Main Vacuum puede detenerse.
        Por el momento siempre está permitido.
        Más adelante se agregarán los interlocks correspondientes a plasma y lámparas.
        """
        return True

    def can_start_vent(self):
        """
        El venteo puede iniciarse únicamente si:
        - Soft Vacuum está detenido.
        - Main Vacuum está detenido.
        """
        return (
            self._door_sequence.state == DoorState.CLOSED
            and
            self._soft_vacuum_sequence.state == SoftVacuumState.IDLE
            and
            self._main_vacuum_sequence.state == MainVacuumState.IDLE
        )
    
    # =====================================================================
    # Estado de controles
    # =====================================================================
    def is_door_control_enabled(self):
        # Determina si el botón de puerta puede utilizarse según el estado actual.
        state = self._door_sequence.state

        if state in (
            DoorState.OPENING,
            DoorState.CLOSING,
            DoorState.ERROR,
        ):
            return False

        if state == DoorState.OPEN:
            # Cerrar la puerta siempre debe estar permitido.
            return True

        if state == DoorState.CLOSED:
            # Para abrir se deben cumplir los interlocks.
            return self.can_open_door()

        return False

    def is_soft_vacuum_control_enabled(self):
        #Determina si el botón de Soft Vacuum puede utilizarse según el estado actual.
        state = self._soft_vacuum_sequence.state

        if state in (
            SoftVacuumState.STARTING,
            SoftVacuumState.STOPPING,
            SoftVacuumState.ERROR,
        ):
            return False

        if state == SoftVacuumState.RUNNING:
            # Detener Soft Vacuum siempre debe estar permitido.
            return True

        if state == SoftVacuumState.IDLE:
            # Para iniciar se deben cumplir los interlocks.
            return self.can_start_soft_vacuum()

        return False

    def is_main_vacuum_control_enabled(self):
        # Determina si el control de Main Vacuum puede utilizarse.
        state = self._main_vacuum_sequence.state

        if state in (
            MainVacuumState.STARTING,
            MainVacuumState.STOPPING,
            MainVacuumState.ERROR,
        ):
            return False

        if state == MainVacuumState.RUNNING:
            return self.can_stop_main_vacuum()

        if state == MainVacuumState.IDLE:
            return self.can_start_main_vacuum()

        return False

    def is_vent_control_enabled(self):
        #Determina si el control de venteo puede utilizarse.
        state = self._vent_sequence.state

        if state in (
            VentState.STARTING,
            VentState.STOPPING,
            VentState.ERROR,
        ):
            return False

        if state == VentState.RUNNING:
            # Detener el venteo siempre está permitido.
            return True

        if state == VentState.IDLE:
            return self.can_start_vent()

        return False

    # =====================================================================
    # Permisos de interfaz
    # =====================================================================
    def get_permissions(self):
        # Devuelve los permisos actuales de los controles de secuencias funcionales.
        return {
            "door": self.is_door_control_enabled(),
            "soft_vacuum": (self.is_soft_vacuum_control_enabled()),
            "main_vacuum": (self.is_main_vacuum_control_enabled()),
            "vent": (self.is_vent_control_enabled()),
        }

    def vacuum_started(self):
        """
        Indica que la cámara fue sometida a vacío.
        A partir de este momento no se permite abrir
        la puerta hasta completar un venteo.
        """
        self._vent_required = True

    def vent_completed(self):
        """
        Indica que el venteo finalizó correctamente
        y la cámara puede considerarse venteada.
        """
        self._vent_required = False