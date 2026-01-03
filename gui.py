import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Slot, QObject
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QDialog,
    QTextEdit,
    QScrollArea,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget, QMainWindow, QStatusBar,
)

from main import batch_convert, DependencyMissing

AUDIO_IN = "flac"
AUDIO_OUT = "mp3"

class Worker(QObject):
    progress = Signal(int)
    log = Signal(str)
    finished = Signal()

    def __init__(self, folder: str, delete_originals: bool, bitrate: str):
        super().__init__()
        self.folder = folder
        self.delete_originals = delete_originals
        self.bitrate = bitrate

    @Slot()
    def run_conversion(self):
        """Runs the conversion in a separate thread."""
        try:
            for progress, log_message in batch_convert(
                self.folder, bitrate=self.bitrate
            ):
                self.progress.emit(progress)
                self.log.emit(log_message)

            if self.delete_originals:
                self.log.emit("Deleting original files...")
                for flac_file in Path(self.folder).glob(f"*.{AUDIO_IN}"):
                    flac_file.unlink()
                    self.log.emit(f"Deleted {flac_file.name}")
        except DependencyMissing as e:
            self.log.emit(f"Error: {e}")
        except Exception as e:
            self.log.emit(f"An unexpected error occurred: {e}")
        finally:
            self.finished.emit()


class StatusBar(QStatusBar):
    def __init__(self, initial_msg: str = 'Ready'):
        super().__init__()
        self.showMessage(initial_msg)

    def set_message(self, message: str):
        self.showMessage(message)

    def set_temp_message(self, message: str, ms_timeout: int):
        self.showMessage(message, timeout=ms_timeout)

    def add_permanent_widget(self, label: str, widget: QWidget):
        self.addPermanentWidget(QLabel(label))
        self.addPermanentWidget(widget)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sound Converter")
        self.setGeometry(400, 400, 500, 200)
        self.status_bar = StatusBar('Select a folder with .flac files to convert')
        self.setStatusBar(self.status_bar)
        container = QWidget()
        self.layout = QVBoxLayout()

        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("Source Folder:")
        self.folder_path = QLineEdit()
        self.folder_path.setReadOnly(True)
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder_dialog)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(self.open_folder_button)
        self.layout.addLayout(folder_layout)

        # Options
        option_delete_layout = QHBoxLayout()
        self.delete_checkbox = QCheckBox("Delete original FLAC files after conversion")
        self.delete_checkbox.setChecked(False)
        option_delete_layout.addWidget(self.delete_checkbox)
        option_delete_layout.addStretch()

        option_bitrate_layout = QHBoxLayout()
        self.bitrate_label = QLabel("MP3 Bitrate:")
        self.bitrate_label.setToolTip("Conversion bitrate - 192k is a good balance between quality and file size")
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["128k", "192k", "256k", "320k"])
        self.bitrate_combo.setCurrentText("192k")
        option_bitrate_layout.addWidget(self.bitrate_label)
        option_bitrate_layout.addWidget(self.bitrate_combo)
        option_bitrate_layout.addStretch()

        self.layout.addLayout(option_delete_layout)
        self.layout.addLayout(option_bitrate_layout)

        # Progress bar
        self.progress_bar = QProgressBar(value=0)
        self.layout.addWidget(self.progress_bar)

        # Convert button
        self.convert_button = QPushButton("Convert")
        self.convert_button.setEnabled(False)
        self.convert_button.clicked.connect(self.start_conversion)
        self.layout.addWidget(self.convert_button)

        container.setLayout(self.layout)
        self.setCentralWidget(container)
        self.log_messages = []

    @Slot()
    def open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            flac_files = len(list(Path(folder).glob(f"*.{AUDIO_IN}")))
            self.folder_path.setText(folder)
            self.convert_button.setEnabled(True)
            self.status_bar.set_message(f"{flac_files} flac files in selected folder")

    @Slot()
    def start_conversion(self):
        folder = self.folder_path.text()
        if not folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return

        self.convert_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_messages = []

        self.thread = QThread()
        self.worker = Worker(
            folder,
            self.delete_checkbox.isChecked(),
            self.bitrate_combo.currentText(),
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run_conversion)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.append_log)
        self.worker.finished.connect(self.conversion_finished)

        self.thread.start()


    @Slot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @Slot(str)
    def append_log(self, message):
        self.log_messages.append(message)
        self.status_bar.set_message(message)

    @Slot()
    def conversion_finished(self):
        self.convert_button.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_bar.set_message('Conversion ended')
        log_text = "\n".join(self.log_messages)

        user_choice = QMessageBox.question(self, 'Conversion ended', 'Would you like to see a log?')
        if user_choice != QMessageBox.Yes:
            return

        log_dialog = QDialog(self)
        log_dialog.setWindowTitle("Conversion Log")
        log_dialog.resize(600, 400)  # Set a default size

        dialog_layout = QVBoxLayout(log_dialog)

        log_text_edit = QTextEdit()
        log_text_edit.setReadOnly(True)
        log_text_edit.setText(log_text)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(log_text_edit)

        dialog_layout.addWidget(scroll_area)

        close_button = QPushButton("Close")
        close_button.clicked.connect(log_dialog.accept)
        dialog_layout.addWidget(close_button)

        log_dialog.exec()  # Use exec() for modal dialog

        self.log_messages = []


app = QApplication([])
window = MainWindow()
window.show()
app.exec()