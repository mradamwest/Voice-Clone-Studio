from PySide6.QtCore import Qt, QThread, Signal, QUrl, QStandardPaths
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from pathlib import Path

from voice_clone_studio.core.engine import VoiceEngine, generation_preflight, reference_audio_status, generation_output_path, verify_generated_audio

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QSlider, QTextEdit, QVBoxLayout, QWidget, QFileDialog, QLineEdit, QComboBox, QMessageBox, QProgressBar, QButtonGroup
)

class GenerateWorker(QThread):
    finished_audio = Signal(str)
    failed = Signal(str)
    status = Signal(str)

    def __init__(self, text, reference_audio, output, language_id="en", allow_model_download=False):
        super().__init__()
        self.text = text
        self.reference_audio = reference_audio
        self.output = output
        self.language_id = language_id
        self.allow_model_download = allow_model_download

    def run(self):
        try:
            self.status.emit("Preparing voice model…")
            generation_preflight(self.text, self.reference_audio, self.output, allow_model_download=self.allow_model_download)
            self.status.emit("Generating speech…")
            path = VoiceEngine().generate(self.text, self.reference_audio, self.output, language_id=self.language_id)
            self.finished_audio.emit(str(path))
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Clone Studio")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(self._style())
        self.reference_audio = ""
        self.worker = None
        self.generated_audio = ""
        self.audio_output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.setCentralWidget(self._build())

    def _build(self):
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        side = QVBoxLayout(sidebar)
        brand = QLabel("◉  VOICE CLONE\n     STUDIO")
        brand.setObjectName("brand")
        side.addWidget(brand)
        for text in ("My Voices", "Generated Voices"):
            b = QPushButton(text)
            b.setObjectName("nav")
            side.addWidget(b)
        side.addStretch()
        side.addWidget(QLabel("Settings"))
        layout.addWidget(sidebar)

        content = QWidget()
        body = QVBoxLayout(content)
        body.setContentsMargins(42, 34, 42, 34)
        title = QLabel("Bring Voices to Life")
        title.setObjectName("title")
        subtitle = QLabel("Create natural speech with your cloned voices")
        subtitle.setObjectName("muted")
        body.addWidget(title)
        body.addWidget(subtitle)
        body.addSpacing(22)

        card = QFrame()
        card.setObjectName("card")
        c = QVBoxLayout(card)
        c.setContentsMargins(28, 24, 28, 24)
        c.addWidget(QLabel("VOICE SOURCE"))
        source_row = QHBoxLayout()
        self.my_voice_source = QPushButton("My Voice")
        self.builtin_voice_source = QPushButton("Built-in Voice")
        self.my_voice_source.setCheckable(True); self.builtin_voice_source.setCheckable(True)
        self.my_voice_source.setChecked(True)
        self.voice_source_group = QButtonGroup(self); self.voice_source_group.setExclusive(True)
        self.voice_source_group.addButton(self.my_voice_source); self.voice_source_group.addButton(self.builtin_voice_source)
        source_row.addWidget(self.my_voice_source); source_row.addWidget(self.builtin_voice_source); source_row.addStretch()
        c.addLayout(source_row)
        c.addWidget(QLabel("SELECT VOICE"))
        voice = QPushButton("Choose or Drop Reference Voice…")
        voice.setObjectName("voice")
        self.reference_button = voice
        voice.clicked.connect(lambda: self._choose_reference(voice))
        c.addWidget(voice)
        self.setAcceptDrops(True)
        c.addSpacing(16)
        c.addWidget(QLabel("TEXT TO SPEECH"))
        editor = QTextEdit()
        self.editor = editor
        editor.setPlaceholderText("Type or paste the text you want to generate...")
        editor.setMinimumHeight(190)
        c.addWidget(editor)
        language_row = QHBoxLayout()
        language_row.addWidget(QLabel("Language"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English (en)", "Arabic (ar)", "Danish (da)", "German (de)", "Greek (el)", "Spanish (es)", "Finnish (fi)", "French (fr)", "Hebrew (he)", "Hindi (hi)", "Italian (it)", "Japanese (ja)", "Korean (ko)", "Malay (ms)", "Dutch (nl)", "Norwegian (no)", "Polish (pl)", "Portuguese (pt)", "Russian (ru)", "Swedish (sv)", "Swahili (sw)", "Turkish (tr)", "Chinese (zh)"])
        language_row.addWidget(self.language_combo, 1)
        c.addLayout(language_row)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Stability"))
        controls.addWidget(QSlider(Qt.Horizontal))
        controls.addWidget(QLabel("Similarity"))
        controls.addWidget(QSlider(Qt.Horizontal))
        controls.addWidget(QLabel("Style"))
        controls.addWidget(QSlider(Qt.Horizontal))
        c.addLayout(controls)

        self.generation_progress = QProgressBar()
        self.generation_progress.setRange(0, 0)
        self.generation_progress.setTextVisible(False)
        self.generation_progress.setFixedHeight(6)
        self.generation_progress.setVisible(False)
        c.addWidget(self.generation_progress)

        self.generation_status = QLabel("")
        self.generation_status.setObjectName("muted")
        self.generation_status.setVisible(False)
        c.addWidget(self.generation_status)

        actions = QHBoxLayout()
        play = QPushButton("Play Generated Audio")
        self.play_button = play
        play.setEnabled(False)
        play.clicked.connect(self._play_generated_audio)
        preview = QPushButton("Save Generated Audio…")
        self.preview_button = preview
        preview.setEnabled(False)
        preview.clicked.connect(self._save_generated_audio)
        generate = QPushButton("Generate Speech")
        generate.setObjectName("primary")
        self.generate_button = generate
        generate.clicked.connect(self._generate_speech)
        actions.addStretch()
        actions.addWidget(play)
        actions.addWidget(preview)
        actions.addWidget(generate)
        c.addLayout(actions)
        body.addWidget(card)
        body.addStretch()
        layout.addWidget(content, 1)
        return root

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if len(urls) == 1 and Path(urls[0].toLocalFile()).suffix.lower() in {".wav", ".mp3", ".flac", ".m4a"}:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if len(urls) != 1:
            return
        path = urls[0].toLocalFile()
        status = reference_audio_status(path)
        if not status["ready"]:
            QMessageBox.warning(self, "Reference Voice", "The dropped recording is not ready for cloning.")
            return
        self.reference_audio = path
        self.reference_button.setText(f"Reference Voice     •     Ready ({status['bytes'] / 1024:.0f} KB)")
        self.my_voice_source.setChecked(True)
        event.acceptProposedAction()

    def _choose_reference(self, button):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Reference Voice", "", "Audio (*.wav *.mp3 *.flac *.m4a)")
        if path:
            status = reference_audio_status(path)
            if not status["ready"]:
                QMessageBox.warning(self, "Reference Voice", "The selected recording is not ready for cloning.")
                return
            self.reference_audio = path
            button.setText(f"Reference Voice     •     Ready ({status['bytes'] / 1024:.0f} KB)")

    def _generate_speech(self):
        if not self.reference_audio:
            QMessageBox.information(self, "Reference Voice", "Choose a reference voice recording first.")
            return
        text = self.editor.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Text Required", "Enter text to generate.")
            return
        music_dir = QStandardPaths.writableLocation(QStandardPaths.MusicLocation) or str(Path.home() / "Music")
        output_dir = Path(music_dir) / "Voice Clone Studio"
        output_dir.mkdir(parents=True, exist_ok=True)
        output = str(generation_output_path(output_dir, "voice-clone-studio-output.wav"))
        allow_model_download = False
        try:
            generation_preflight(text, self.reference_audio, output, allow_model_download=False)
        except (ValueError, FileNotFoundError) as exc:
            QMessageBox.warning(self, "Cannot Generate", str(exc))
            return
        except RuntimeError as exc:
            if "download approval" not in str(exc).lower():
                QMessageBox.warning(self, "Cannot Generate", str(exc)); return
            answer = QMessageBox.question(self, "Model Download Required", "The voice model is not cached yet and must be downloaded before first use. Continue?")
            if answer != QMessageBox.Yes:
                return
            generation_preflight(text, self.reference_audio, output, allow_model_download=True)
            allow_model_download = True
        self.generated_audio = ""
        self.preview_button.setEnabled(False)
        self.play_button.setEnabled(False)
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating…")
        self.generation_progress.setVisible(True)
        self.generation_status.setText("Preparing voice model…")
        self.generation_status.setVisible(True)
        language_id = self.language_combo.currentText().rsplit("(", 1)[-1].rstrip(")")
        self.worker = GenerateWorker(text, self.reference_audio, output, language_id=language_id, allow_model_download=allow_model_download)
        self.worker.finished_audio.connect(self._generation_finished)
        self.worker.finished.connect(self._generation_worker_finished)
        self.worker.status.connect(self.generate_button.setText)
        self.worker.status.connect(self.generation_status.setText)
        self.worker.failed.connect(self._generation_failed)
        self.worker.start()

    def _generation_worker_finished(self):
        self.worker = None

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Voice Clone Studio", "Speech generation is still running. Wait for it to finish before closing.")
            event.ignore()
            return
        event.accept()

    def _generation_finished(self, path):
        try:
            verify_generated_audio(path)
        except (ValueError, FileNotFoundError, RuntimeError) as exc:
            self._generation_failed(str(exc))
            return
        self.generated_audio = path
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Speech")
        self.preview_button.setEnabled(True)
        self.play_button.setEnabled(True)
        self.generation_progress.setVisible(False)
        self.generation_status.setText("Speech generated successfully.")
        self.generation_status.setVisible(True)
        QMessageBox.information(self, "Voice Clone Studio", f"Speech generated successfully.\n\nSaved to:\n{path}")

    def _play_generated_audio(self):
        if not self.generated_audio or not Path(self.generated_audio).is_file():
            QMessageBox.information(self, "Generated Audio", "Generate speech before playback.")
            return
        self.player.setSource(QUrl.fromLocalFile(str(Path(self.generated_audio).resolve())))
        self.player.play()

    def _save_generated_audio(self):
        if not self.generated_audio or not Path(self.generated_audio).is_file():
            QMessageBox.information(self, "Generated Audio", "Generate speech before saving audio.")
            return
        destination, _ = QFileDialog.getSaveFileName(
            self, "Save Generated Audio", "voice-clone.wav", "WAV Audio (*.wav)"
        )
        if destination:
            import shutil
            shutil.copy2(self.generated_audio, destination)
            QMessageBox.information(self, "Voice Clone Studio", f"Audio saved successfully.\n\n{destination}")

    def _generation_failed(self, message):
        self.generated_audio = ""
        self.preview_button.setEnabled(False)
        self.play_button.setEnabled(False)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Speech")
        self.generation_progress.setVisible(False)
        self.generation_status.setText("Generation failed.")
        self.generation_status.setVisible(True)
        QMessageBox.critical(self, "Generation Failed", message)

    @staticmethod
    def _style():
        return """
        QMainWindow, QWidget { background:#070b16; color:#e9ecf7; font-family:'Segoe UI'; font-size:14px; }
        #sidebar { background:#0b1020; border-right:1px solid #1a2440; }
        #brand { color:#9c8cff; font-size:17px; font-weight:700; padding:24px 14px; }
        #nav { text-align:left; padding:12px 18px; border:0; border-radius:8px; background:transparent; color:#c8ccda; }
        #nav:hover { background:#151c33; color:white; }
        #title { font-size:32px; font-weight:700; }
        #muted { color:#858da4; font-size:15px; }
        #card { background:#0e1425; border:1px solid #202b48; border-radius:14px; }
        #voice, QTextEdit { background:#11192d; border:1px solid #293656; border-radius:9px; padding:13px; color:white; }
        QPushButton { background:#151d32; border:1px solid #2a3654; border-radius:8px; padding:10px 18px; color:#e8eaf4; }
        #primary { background:#7047ed; border-color:#825dff; font-weight:700; }
        QSlider::groove:horizontal { height:4px; background:#27304b; border-radius:2px; }
        QSlider::handle:horizontal { width:14px; margin:-5px 0; border-radius:7px; background:#8a68ff; }
        """
