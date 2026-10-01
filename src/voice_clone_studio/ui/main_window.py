from PySide6.QtCore import Qt, QThread, Signal
from pathlib import Path
import tempfile

from voice_clone_studio.core.engine import VoiceEngine

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QSlider, QTextEdit, QVBoxLayout, QWidget, QFileDialog, QLineEdit, QComboBox, QMessageBox
)

class GenerateWorker(QThread):
    finished_audio = Signal(str)
    failed = Signal(str)

    def __init__(self, text, reference_audio, output):
        super().__init__()
        self.text = text
        self.reference_audio = reference_audio
        self.output = output

    def run(self):
        try:
            path = VoiceEngine().generate(self.text, self.reference_audio, self.output)
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
        for text in ("Home", "My Voices", "Clone Voice", "Text to Speech", "History"):
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
        c.addWidget(QLabel("SELECT VOICE"))
        voice = QPushButton("Choose Reference Voice…")
        voice.setObjectName("voice")
        voice.clicked.connect(lambda: self._choose_reference(voice))
        c.addWidget(voice)
        c.addSpacing(16)
        c.addWidget(QLabel("TEXT TO SPEECH"))
        editor = QTextEdit()
        self.editor = editor
        editor.setPlaceholderText("Type or paste the text you want to generate...")
        editor.setMinimumHeight(190)
        c.addWidget(editor)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Stability"))
        controls.addWidget(QSlider(Qt.Horizontal))
        controls.addWidget(QLabel("Similarity"))
        controls.addWidget(QSlider(Qt.Horizontal))
        controls.addWidget(QLabel("Style"))
        controls.addWidget(QSlider(Qt.Horizontal))
        c.addLayout(controls)

        actions = QHBoxLayout()
        preview = QPushButton("Preview")
        generate = QPushButton("Generate Speech")
        generate.setObjectName("primary")
        self.generate_button = generate
        generate.clicked.connect(self._generate_speech)
        actions.addStretch()
        actions.addWidget(preview)
        actions.addWidget(generate)
        c.addLayout(actions)
        body.addWidget(card)
        body.addStretch()
        layout.addWidget(content, 1)
        return root

    def _choose_reference(self, button):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Reference Voice", "", "Audio (*.wav *.mp3 *.flac *.m4a)")
        if path:
            self.reference_audio = path
            button.setText("Reference Voice     •     Ready")

    def _generate_speech(self):
        if not self.reference_audio:
            QMessageBox.information(self, "Reference Voice", "Choose a reference voice recording first.")
            return
        text = self.editor.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Text Required", "Enter text to generate.")
            return
        output = str(Path(tempfile.gettempdir()) / "voice-clone-studio-output.wav")
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating…")
        self.worker = GenerateWorker(text, self.reference_audio, output)
        self.worker.finished_audio.connect(self._generation_finished)
        self.worker.failed.connect(self._generation_failed)
        self.worker.start()

    def _generation_finished(self, path):
        self.generated_audio = path
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Speech")
        QMessageBox.information(self, "Voice Clone Studio", f"Speech generated successfully.\n\n{path}")

    def _generation_failed(self, message):
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Speech")
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
