"""Modal progress dialog for six-point MFC output calibration."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from config_gui.strings import tr
from controllers.mfc_controller import MFCController
from gui.widgets.localization import set_localized_text


class MFCCalibrationDialog(QDialog):
    def __init__(self, mfc_name, parent=None):
        super().__init__(parent)
        self.mfc_name = mfc_name
        self.references = MFCController.CALIBRATION_FLOWS[mfc_name]
        self._completed = 0
        self._finished = False
        self.setObjectName("MFCCalibrationDialog")
        self.setWindowTitle(tr("Calibración MFC: {name}").format(name=mfc_name))
        self.setModal(True)
        self.resize(720, 600)
        self.setMinimumSize(680, 560)

        self.phase_label = QLabel()
        self.phase_label.setObjectName("MFCCalibrationPhase")
        self.current_point_label = QLabel()
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("MFCCalibrationProgress")
        self.progress_bar.setRange(0, len(self.references))
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(tr("%v de %m puntos"))

        self.points_table = QTableWidget(len(self.references), 4)
        self.points_table.setObjectName("MFCCalibrationTable")
        self.points_table.setHorizontalHeaderLabels(
            [tr("Paso"), tr("Caudal esperado"), tr("Offset calculado"), tr("Estado")]
        )
        self.points_table.verticalHeader().setVisible(False)
        self.points_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.points_table.setSelectionMode(QTableWidget.NoSelection)
        self.points_table.horizontalHeader().setStretchLastSection(True)
        self.points_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.points_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.points_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.points_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.points_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.points_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.points_table.verticalHeader().setDefaultSectionSize(34)
        self.points_table.setMinimumHeight(270)
        self.points_table.setMaximumHeight(300)

        for row, flow in enumerate(self.references):
            self._set_cell(row, 0, str(row + 1))
            self._set_cell(row, 1, f"{flow:g} SLPM")
            self._set_cell(row, 2, "—")
            self._set_cell(row, 3, tr("Pendiente"))

        self.result_label = QLabel()
        self.result_label.setObjectName("MFCCalibrationResult")
        self.result_label.setWordWrap(True)
        self.close_button = QPushButton(tr("Cerrar"))
        self.close_button.setObjectName("SettingsCloseButton")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)

        current_row = QHBoxLayout()
        current_row.addWidget(self.current_point_label, 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(self.phase_label)
        layout.addLayout(current_row)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.points_table)
        layout.addWidget(self.result_label)
        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self.close_button)
        layout.addLayout(button_row)

        set_localized_text(self.phase_label, "Preparando calibración...")
        set_localized_text(self.current_point_label, "Punto actual: —")

    def update_progress(self, phase, completed, total, current_flow, offsets):
        self._completed = max(0, min(int(completed), len(self.references)))
        self.progress_bar.setValue(self._completed)

        current_index = min(self._completed, len(self.references) - 1)
        if phase == "measuring":
            set_localized_text(
                self.phase_label,
                "Midiendo punto {number} de {total}...",
            )
            self.phase_label.setText(
                tr("Midiendo punto {number} de {total}...").format(
                    number=current_index + 1, total=total
                )
            )
            self.current_point_label.setText(
                tr("Caudal de calibración: {flow:g} SLPM").format(flow=current_flow)
            )
        elif phase == "point_complete":
            set_localized_text(
                self.phase_label,
                "Punto {number} completado; offset calculado.",
            )
            self.phase_label.setText(
                tr("Punto {number} completado; offset calculado.").format(
                    number=self._completed
                )
            )
            self.current_point_label.setText(
                tr("Caudal de calibración: {flow:g} SLPM").format(flow=current_flow)
            )
        elif phase == "saving":
            set_localized_text(self.phase_label, "Guardando tabla de offsets...")
            self.current_point_label.setText(tr("Se completaron los seis puntos."))
        elif phase == "completed":
            self._set_final_rows(offsets)
            set_localized_text(self.phase_label, "Calibración completada.")
            self.current_point_label.setText(tr("Se completaron los seis puntos."))
        elif phase == "failed":
            self._set_final_rows(offsets)
            set_localized_text(self.phase_label, "La calibración se interrumpió.")
            self.current_point_label.setText(
                tr("Último caudal: {flow:g} SLPM").format(flow=current_flow)
            )

        for row, flow in enumerate(self.references):
            if row < self._completed and flow in offsets:
                self._set_cell(row, 2, f"{offsets[flow]:+.4f} SLPM")
                self._set_cell(row, 3, tr("Completado"))
            elif phase == "measuring" and row == self._completed:
                self._set_cell(row, 3, tr("Midiendo"))
            elif phase == "saving" and row < self._completed:
                self._set_cell(row, 3, tr("Completado"))

    def set_result(self, success, saved, error, calibration_date=""):
        self._finished = True
        self.close_button.setEnabled(True)
        if success:
            self.progress_bar.setValue(len(self.references))
            set_localized_text(self.phase_label, "Calibración completada.")
            self.result_label.setText(
                tr("Tabla guardada. Última calibración: {date}.").format(
                    date=calibration_date
                )
            )
            for row in range(len(self.references)):
                self._set_cell(row, 3, tr("Completado"))
        else:
            if saved:
                set_localized_text(self.phase_label, "Tabla guardada con un error al finalizar.")
            else:
                set_localized_text(self.phase_label, "La calibración no se completó.")
            self.result_label.setText(error or tr("No se pudo completar la calibración."))
            if self._completed < len(self.references):
                self._set_cell(self._completed, 3, tr("Interrumpido"))
        self.result_label.show()

    def _set_final_rows(self, offsets):
        for row, flow in enumerate(self.references):
            if row < self._completed and flow in offsets:
                self._set_cell(row, 2, f"{offsets[flow]:+.4f} SLPM")
                self._set_cell(row, 3, tr("Completado"))

    def _set_cell(self, row, column, value):
        self.points_table.setItem(row, column, QTableWidgetItem(str(value)))

    def accept(self):
        if self._finished:
            super().accept()

    def reject(self):
        if self._finished:
            super().reject()

    def closeEvent(self, event):
        if self._finished:
            event.accept()
        else:
            event.ignore()
