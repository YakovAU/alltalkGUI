import sys
import os
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QClipboard

class VoiceGeneratorThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, text, speaker, output_file):
        super().__init__()
        self.text = text
        self.speaker = speaker
        self.output_file = output_file

    def run(self):
        url = "http://10.1.1.200:8020/tts_to_file"
        payload = {
            "text": self.text,
            "speaker": self.speaker,
            "speaker_wav": f"{self.speaker}.wav",
            "language": "en",
            "file_name_or_path": self.output_file
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                self.finished.emit(True, f"Audio file saved to {self.output_file}")
            else:
                self.finished.emit(False, f"Error: {response.status_code}\n{response.text}")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Generator")
        self.setGeometry(100, 100, 400, 200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Text input
        text_layout = QHBoxLayout()
        text_label = QLabel("Text:")
        self.text_input = QLineEdit()
        text_layout.addWidget(text_label)
        text_layout.addWidget(self.text_input)
        layout.addLayout(text_layout)

        # Filename input
        filename_layout = QHBoxLayout()
        filename_label = QLabel("Filename prefix:")
        self.filename_input = QLineEdit()
        filename_layout.addWidget(filename_label)
        filename_layout.addWidget(self.filename_input)
        layout.addLayout(filename_layout)

        # Speaker selection
        speaker_layout = QHBoxLayout()
        speaker_label = QLabel("Speaker:")
        self.speaker_combo = QComboBox()
        self.load_speakers()
        speaker_layout.addWidget(speaker_label)
        speaker_layout.addWidget(self.speaker_combo)
        layout.addLayout(speaker_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.generate_voice)
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(exit_button)
        layout.addLayout(button_layout)

    def load_speakers(self):
        speakers_folder = r"\\DEBIAN-YAKOV\yakov\AI\xtts\speakers"
        try:
            speakers = [f.split('.')[0] for f in os.listdir(speakers_folder) if f.endswith('.wav')]
            self.speaker_combo.addItems(speakers)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load speakers: {str(e)}")

    def generate_voice(self):
        text = self.text_input.text()
        filename_prefix = self.filename_input.text()
        speaker = self.speaker_combo.currentText()

        if not text or not filename_prefix:
            QMessageBox.warning(self, "Error", "Please enter both text and filename prefix.")
            return

        output_file = f"{filename_prefix}.wav"
        self.generate_button.setEnabled(False)

        self.thread = VoiceGeneratorThread(text, speaker, output_file)
        self.thread.finished.connect(self.on_generation_finished)
        self.thread.start()

    def on_generation_finished(self, success, message):
        self.generate_button.setEnabled(True)
        if success:
            filename = message.split()[-1]
            if self.copy_to_clipboard(filename):
                QMessageBox.information(self, "Success", f"{message}\nAudio file copied to clipboard.")
            else:
                QMessageBox.information(self, "Success", f"{message}\nFailed to copy audio file to clipboard.")
        else:
            QMessageBox.warning(self, "Error", message)

    def copy_to_clipboard(self, filename):
        source_path = os.path.join(r"\\DEBIAN-YAKOV\yakov\AI\xtts\output", filename)

        try:
            mime_data = QMimeData()
            url = QUrl.fromLocalFile(source_path)
            mime_data.setUrls([url])

            clipboard = QApplication.clipboard()
            clipboard.setMimeData(mime_data, mode=QClipboard.Mode.Clipboard)
            return True
        except Exception as e:
            print(f"Failed to copy file to clipboard: {str(e)}")
            return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())