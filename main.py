import sys
import os
import requests
import json
import tempfile
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QCheckBox, QSlider
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QClipboard
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class VoiceGeneratorThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, text, character_voice, narrator_voice, narrator_enabled, text_not_inside, language, output_file_name, output_file_timestamp, autoplay, autoplay_volume):
        super().__init__()
        self.text = text
        self.character_voice = character_voice
        self.narrator_voice = narrator_voice
        self.narrator_enabled = narrator_enabled
        self.text_not_inside = text_not_inside
        self.language = language
        self.output_file_name = output_file_name
        self.output_file_timestamp = output_file_timestamp
        self.autoplay = autoplay
        self.autoplay_volume = autoplay_volume

    def run(self):
        base_url = 'http://10.1.1.200:7851'
        tts_url = f'{base_url}/api/tts-generate'

        try:
            data = {
                'text_input': self.text,
                'text_filtering': 'standard',
                'character_voice_gen': self.character_voice,
                'narrator_enabled': str(self.narrator_enabled).lower(),
                'narrator_voice_gen': self.narrator_voice,
                'text_not_inside': self.text_not_inside,
                'language': self.language,
                'output_file_name': self.output_file_name,
                'output_file_timestamp': str(self.output_file_timestamp).lower(),
                'autoplay': str(self.autoplay).lower(),
                'autoplay_volume': str(self.autoplay_volume)
            }

            response = requests.post(tts_url, data=data, timeout=30)

            if response.status_code != 200:
                self.finished.emit(False, f"API request failed with status {response.status_code}")
                return

            result = response.json()
            if result['status'] == 'generate-success':
                self.finished.emit(True, result['output_file_url'])
            else:
                self.finished.emit(False, "Generation failed")

        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Generator")
        self.setGeometry(100, 100, 500, 400)

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

        # Character voice selection
        character_voice_layout = QHBoxLayout()
        character_voice_label = QLabel("Character Voice:")
        self.character_voice_combo = QComboBox()
        character_voice_layout.addWidget(character_voice_label)
        character_voice_layout.addWidget(self.character_voice_combo)
        layout.addLayout(character_voice_layout)

        # Narrator settings
        narrator_layout = QHBoxLayout()
        self.narrator_checkbox = QCheckBox("Enable Narrator")
        self.narrator_voice_combo = QComboBox()
        narrator_layout.addWidget(self.narrator_checkbox)
        narrator_layout.addWidget(self.narrator_voice_combo)
        layout.addLayout(narrator_layout)

        # Text not inside quotes
        text_not_inside_layout = QHBoxLayout()
        text_not_inside_label = QLabel("Text not inside quotes:")
        self.text_not_inside_combo = QComboBox()
        self.text_not_inside_combo.addItems(["character", "narrator"])
        text_not_inside_layout.addWidget(text_not_inside_label)
        text_not_inside_layout.addWidget(self.text_not_inside_combo)
        layout.addLayout(text_not_inside_layout)

        # Language selection
        language_layout = QHBoxLayout()
        language_label = QLabel("Language:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["en", "fr", "de", "es", "it", "ja", "ko", "pt", "ru", "zh-cn"])
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        layout.addLayout(language_layout)

        # Output file name
        output_file_layout = QHBoxLayout()
        output_file_label = QLabel("Output file name:")
        self.output_file_input = QLineEdit()
        self.output_file_input.setText("output")
        output_file_layout.addWidget(output_file_label)
        output_file_layout.addWidget(self.output_file_input)
        layout.addLayout(output_file_layout)

        # Output file timestamp
        self.output_file_timestamp_checkbox = QCheckBox("Add timestamp to output file")
        self.output_file_timestamp_checkbox.setChecked(True)
        layout.addWidget(self.output_file_timestamp_checkbox)

        # Autoplay settings
        autoplay_layout = QHBoxLayout()
        self.autoplay_checkbox = QCheckBox("Autoplay")
        self.autoplay_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.autoplay_volume_slider.setRange(1, 100)
        self.autoplay_volume_slider.setValue(80)
        autoplay_layout.addWidget(self.autoplay_checkbox)
        autoplay_layout.addWidget(QLabel("Volume:"))
        autoplay_layout.addWidget(self.autoplay_volume_slider)
        layout.addLayout(autoplay_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.generate_voice)
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_audio)
        self.play_button.setEnabled(False)
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(exit_button)
        layout.addLayout(button_layout)

        self.load_voices()

        # Media player setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        # Temporary file
        self.temp_file = None

    def load_voices(self):
        try:
            response = requests.get("http://10.1.1.200:7851/api/voices")
            voices = response.json()["voices"]
            self.character_voice_combo.addItems(voices)
            self.narrator_voice_combo.addItems(voices)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load voices: {str(e)}")

    def generate_voice(self):
        text = self.text_input.text()
        character_voice = self.character_voice_combo.currentText()
        narrator_voice = self.narrator_voice_combo.currentText()
        narrator_enabled = self.narrator_checkbox.isChecked()
        text_not_inside = self.text_not_inside_combo.currentText()
        language = self.language_combo.currentText()
        output_file_name = self.output_file_input.text()
        output_file_timestamp = self.output_file_timestamp_checkbox.isChecked()
        autoplay = self.autoplay_checkbox.isChecked()
        autoplay_volume = self.autoplay_volume_slider.value() / 100

        if not text:
            QMessageBox.warning(self, "Error", "Please enter text.")
            return

        self.generate_button.setEnabled(False)
        self.play_button.setEnabled(False)

        self.thread = VoiceGeneratorThread(text, character_voice, narrator_voice, narrator_enabled, text_not_inside, language, output_file_name, output_file_timestamp, autoplay, autoplay_volume)
        self.thread.finished.connect(self.on_generation_finished)
        self.thread.start()

    def on_generation_finished(self, success, result):
        self.generate_button.setEnabled(True)
        if success:
            QMessageBox.information(self, "Success", f"Audio generated successfully. URL: {result}")
            self.add_to_clipboard(result)
            self.download_audio(result)
        else:
            QMessageBox.warning(self, "Error", result)
            self.play_button.setEnabled(False)

    def add_to_clipboard(self, url):
        clipboard = QApplication.clipboard()
        mime_data = QMimeData()
        mime_data.setUrls([QUrl(url)])
        clipboard.setMimeData(mime_data)

    def download_audio(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Create a temporary file
                if self.temp_file:
                    self.temp_file.close()
                self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                self.temp_file.write(response.content)
                self.temp_file.close()
                self.play_button.setEnabled(True)
            else:
                QMessageBox.warning(self, "Error", f"Failed to download audio: HTTP {response.status_code}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to download audio: {str(e)}")

    def play_audio(self):
        if self.temp_file and os.path.exists(self.temp_file.name):
            self.media_player.setSource(QUrl.fromLocalFile(self.temp_file.name))
            self.audio_output.setVolume(self.autoplay_volume_slider.value() / 100)
            self.media_player.play()

    def closeEvent(self, event):
        if self.temp_file:
            self.temp_file.close()
            os.unlink(self.temp_file.name)
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())