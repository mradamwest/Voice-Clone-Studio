from PySide6.QtCore import Qt, QThread, Signal, QUrl, QStandardPaths
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from pathlib import Path

from voice_clone_studio.core.engine import VoiceEngine, generation_preflight, reference_audio_status, generation_output_path, verify_generated_audio, expressive_settings
from voice_clone_studio.core.voice_library import VoiceLibrary
from voice_clone_studio.core.generated_library import GeneratedVoiceLibrary

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QSlider, QTextEdit, QVBoxLayout, QWidget, QFileDialog, QLineEdit, QComboBox, QMessageBox, QProgressBar, QButtonGroup, QInputDialog, QStackedWidget
)

class GenerateWorker(QThread):
    finished_audio = Signal(str)
    failed = Signal(str)
    status = Signal(str)

    def __init__(self, text, reference_audio, output, language_id="en", allow_model_download=False, emotion="Neutral", intensity="Medium"):
        super().__init__()
        self.text = text
        self.reference_audio = reference_audio
        self.output = output
        self.language_id = language_id
        self.allow_model_download = allow_model_download
        self.emotion = emotion
        self.intensity = intensity

    def run(self):
        try:
            self.status.emit("Preparing voice model…")
            generation_preflight(self.text, self.reference_audio, self.output, allow_model_download=self.allow_model_download)
            self.status.emit("Generating speech…")
            settings = expressive_settings(self.emotion, self.intensity)
            path = VoiceEngine().generate(self.text, self.reference_audio, self.output, language_id=self.language_id, **settings)
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
        self.voice_library = VoiceLibrary()
        self.generated_library = GeneratedVoiceLibrary()
        self.active_voice_name = "Reference Voice"
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
        self.my_voices_nav = QPushButton("My Voices")
        self.my_voices_nav.setObjectName("nav")
        self.generated_voices_nav = QPushButton("Generated Voices")
        self.generated_voices_nav.setObjectName("nav")
        side.addWidget(self.my_voices_nav)
        side.addWidget(self.generated_voices_nav)
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
        self.saved_voice_combo = QComboBox()
        self.saved_voice_combo.addItem("Choose a saved voice…", "")
        for profile in self.voice_library.list():
            self.saved_voice_combo.addItem(profile.name, profile.id)
        self.saved_voice_combo.currentIndexChanged.connect(self._select_saved_voice)
        c.addWidget(self.saved_voice_combo)
        saved_actions = QHBoxLayout()
        save_voice = QPushButton("Save Current Voice")
        save_voice.clicked.connect(self._save_current_voice)
        preview_voice = QPushButton("Preview")
        preview_voice.clicked.connect(self._preview_saved_voice)
        rename_voice = QPushButton("Rename")
        rename_voice.clicked.connect(self._rename_saved_voice)
        delete_voice = QPushButton("Delete")
        delete_voice.clicked.connect(self._delete_saved_voice)
        saved_actions.addWidget(save_voice); saved_actions.addWidget(preview_voice)
        saved_actions.addWidget(rename_voice); saved_actions.addWidget(delete_voice); saved_actions.addStretch()
        c.addLayout(saved_actions)
        voice = QPushButton("Choose or Drop Reference Voice…")
        voice.setObjectName("voice")
        self.reference_button = voice
        voice.clicked.connect(lambda: self._choose_reference(voice))
        c.addWidget(voice)
        self.setAcceptDrops(True)
        self.reference_button.setProperty("dropActive", False)
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

        expressive_row = QHBoxLayout()
        expressive_row.addWidget(QLabel("Emotion"))
        self.emotion_combo = QComboBox()
        self.emotion_combo.addItems(["Neutral", "Angry", "Sad", "Happy", "Excited", "Fearful", "Serious", "Whisper"])
        expressive_row.addWidget(self.emotion_combo, 1)
        expressive_row.addWidget(QLabel("Intensity"))
        self.intensity_combo = QComboBox()
        self.intensity_combo.addItems(["Low", "Medium", "High"])
        self.intensity_combo.setCurrentText("Medium")
        expressive_row.addWidget(self.intensity_combo, 1)
        c.addLayout(expressive_row)

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
        self.main_content = content
        self.generated_content = self._build_generated_voices_page()
        self.pages = QStackedWidget()
        self.pages.addWidget(self.main_content)
        self.pages.addWidget(self.generated_content)
        self.my_voices_nav.clicked.connect(lambda: self.pages.setCurrentWidget(self.main_content))
        self.generated_voices_nav.clicked.connect(self._show_generated_voices)
        layout.addWidget(self.pages, 1)
        return root

    def _build_generated_voices_page(self):
        page = QWidget()
        body = QVBoxLayout(page)
        body.setContentsMargins(42, 34, 42, 34)
        title = QLabel("Generated Voices")
        title.setObjectName("title")
        subtitle = QLabel("Your generated speech is saved here automatically")
        subtitle.setObjectName("muted")
        body.addWidget(title); body.addWidget(subtitle); body.addSpacing(22)
        card = QFrame(); card.setObjectName("card")
        c = QVBoxLayout(card); c.setContentsMargins(28, 24, 28, 24)
        self.generated_voice_combo = QComboBox()
        c.addWidget(self.generated_voice_combo)
        self.generated_voice_details = QLabel("No generated voices yet.")
        self.generated_voice_details.setObjectName("muted")
        c.addWidget(self.generated_voice_details)
        actions = QHBoxLayout()
        for label, handler in (
            ("Play", self._play_library_generated_voice),
            ("Save / Export…", self._export_library_generated_voice),
            ("Rename", self._rename_library_generated_voice),
            ("Delete", self._delete_library_generated_voice),
        ):
            button = QPushButton(label); button.clicked.connect(handler); actions.addWidget(button)
        actions.addStretch(); c.addLayout(actions)
        self.generated_voice_combo.currentIndexChanged.connect(self._update_generated_voice_details)
        body.addWidget(card); body.addStretch()
        return page

    def _refresh_generated_voices(self, selected_id=""):
        self.generated_voice_combo.blockSignals(True)
        self.generated_voice_combo.clear()
        self.generated_voice_combo.addItem("Choose generated audio…", "")
        selected_index = 0
        for item in self.generated_library.list():
            self.generated_voice_combo.addItem(item.name, item.id)
            if item.id == selected_id:
                selected_index = self.generated_voice_combo.count() - 1
        self.generated_voice_combo.setCurrentIndex(selected_index)
        self.generated_voice_combo.blockSignals(False)
        self._update_generated_voice_details()

    def _show_generated_voices(self):
        self._refresh_generated_voices()
        self.pages.setCurrentWidget(self.generated_content)

    def _selected_generated_voice(self):
        item_id = self.generated_voice_combo.currentData()
        if not item_id:
            return None
        return next((item for item in self.generated_library.list() if item.id == item_id), None)

    def _update_generated_voice_details(self, *_):
        item = self._selected_generated_voice()
        if item is None:
            self.generated_voice_details.setText("No generated voice selected.")
            return
        self.generated_voice_details.setText(
            f"Voice: {item.voice_name}     •     Language: {item.language}     •     Created: {item.created_at}"
        )

    def _play_library_generated_voice(self):
        item = self._selected_generated_voice()
        if item is None or not Path(item.audio_path).is_file():
            QMessageBox.information(self, "Generated Voices", "Choose an available generated voice first.")
            return
        self.player.setSource(QUrl.fromLocalFile(str(Path(item.audio_path).resolve())))
        self.player.play()

    def _export_library_generated_voice(self):
        item = self._selected_generated_voice()
        if item is None or not Path(item.audio_path).is_file():
            QMessageBox.information(self, "Generated Voices", "Choose an available generated voice first.")
            return
        destination, _ = QFileDialog.getSaveFileName(self, "Save Generated Voice", f"{item.name}.wav", "WAV Audio (*.wav)")
        if destination:
            import shutil
            shutil.copy2(item.audio_path, destination)

    def _rename_library_generated_voice(self):
        item = self._selected_generated_voice()
        if item is None:
            QMessageBox.information(self, "Generated Voices", "Choose a generated voice to rename.")
            return
        name, ok = QInputDialog.getText(self, "Rename Generated Voice", "Name:", text=item.name)
        name = name.strip()
        if not ok or not name or name == item.name:
            return
        try:
            updated = self.generated_library.rename(item.id, name)
        except (ValueError, KeyError) as exc:
            QMessageBox.warning(self, "Generated Voices", str(exc)); return
        self._refresh_generated_voices(updated.id)

    def _delete_library_generated_voice(self):
        item = self._selected_generated_voice()
        if item is None:
            QMessageBox.information(self, "Generated Voices", "Choose a generated voice to delete.")
            return
        if QMessageBox.question(self, "Delete Generated Voice", f'Delete "{item.name}" from Generated Voices?') != QMessageBox.Yes:
            return
        self.generated_library.remove(item.id)
        if self.generated_audio == item.audio_path:
            self.generated_audio = ""
            self.play_button.setEnabled(False)
            self.preview_button.setEnabled(False)
        self._refresh_generated_voices()

    def _refresh_saved_voices(self, selected_id=""):
        self.saved_voice_combo.blockSignals(True)
        self.saved_voice_combo.clear()
        self.saved_voice_combo.addItem("Choose a saved voice…", "")
        selected_index = 0
        for profile in self.voice_library.list():
            self.saved_voice_combo.addItem(profile.name, profile.id)
            if profile.id == selected_id:
                selected_index = self.saved_voice_combo.count() - 1
        self.saved_voice_combo.setCurrentIndex(selected_index)
        self.saved_voice_combo.blockSignals(False)

    def _selected_saved_voice(self):
        profile_id = self.saved_voice_combo.currentData()
        if not profile_id:
            return None
        try:
            return self.voice_library.get(profile_id)
        except KeyError:
            self._refresh_saved_voices()
            return None

    def _save_current_voice(self):
        if not self.reference_audio:
            QMessageBox.information(self, "My Voices", "Choose a reference voice recording first.")
            return
        status = reference_audio_status(self.reference_audio)
        if not status["ready"]:
            QMessageBox.warning(self, "My Voices", "The current reference recording is not ready to save.")
            return
        name, ok = QInputDialog.getText(self, "Save Voice", "Voice name:", text=self.active_voice_name)
        name = name.strip()
        if not ok or not name:
            return
        try:
            profile = self.voice_library.add(name, self.reference_audio)
        except (ValueError, FileNotFoundError) as exc:
            QMessageBox.warning(self, "My Voices", str(exc))
            return
        self._refresh_saved_voices(profile.id)
        self.reference_audio = profile.reference_audio
        self.active_voice_name = profile.name
        self.reference_button.setText(f"Saved Voice     •     {profile.name}")

    def _preview_saved_voice(self):
        profile = self._selected_saved_voice()
        if profile is None:
            QMessageBox.information(self, "My Voices", "Choose a saved voice to preview.")
            return
        status = reference_audio_status(profile.reference_audio)
        if not status["ready"]:
            QMessageBox.warning(self, "My Voices", f"{profile.name} is missing its reference recording.")
            return
        self.player.setSource(QUrl.fromLocalFile(profile.reference_audio))
        self.player.play()

    def _rename_saved_voice(self):
        profile = self._selected_saved_voice()
        if profile is None:
            QMessageBox.information(self, "My Voices", "Choose a saved voice to rename.")
            return
        name, ok = QInputDialog.getText(self, "Rename Voice", "Voice name:", text=profile.name)
        name = name.strip()
        if not ok or not name or name == profile.name:
            return
        try:
            updated = self.voice_library.rename(profile.id, name)
        except (ValueError, KeyError) as exc:
            QMessageBox.warning(self, "My Voices", str(exc))
            return
        self._refresh_saved_voices(updated.id)
        if self.reference_audio == updated.reference_audio:
            self.active_voice_name = updated.name
            self.reference_button.setText(f"Saved Voice     •     {updated.name}")

    def _delete_saved_voice(self):
        profile = self._selected_saved_voice()
        if profile is None:
            QMessageBox.information(self, "My Voices", "Choose a saved voice to delete.")
            return
        answer = QMessageBox.question(
            self, "Delete Saved Voice",
            f'Delete "{profile.name}" from My Voices?\n\nYour original recording will not be deleted.',
        )
        if answer != QMessageBox.Yes:
            return
        was_active = self.reference_audio == profile.reference_audio
        if self.voice_library.remove(profile.id):
            self._refresh_saved_voices()
            if was_active:
                self.reference_audio = ""
                self.active_voice_name = "Reference Voice"
                self.reference_button.setText("Choose or Drop Reference Voice…")

    def _select_saved_voice(self, index):
        profile_id = self.saved_voice_combo.itemData(index)
        if not profile_id:
            return
        try:
            profile = self.voice_library.get(profile_id)
        except KeyError:
            QMessageBox.warning(self, "My Voices", "That saved voice is no longer available.")
            return
        status = reference_audio_status(profile.reference_audio)
        if not status["ready"]:
            QMessageBox.warning(self, "My Voices", f"{profile.name} is missing its reference recording.")
            return
        self.reference_audio = profile.reference_audio
        self.active_voice_name = profile.name
        self.reference_button.setText(f"Saved Voice     •     {profile.name}")
        self.my_voice_source.setChecked(True)

    def _set_reference_drop_highlight(self, active):
        self.reference_button.setProperty("dropActive", bool(active))
        self.reference_button.style().unpolish(self.reference_button)
        self.reference_button.style().polish(self.reference_button)

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        valid = (
            len(urls) == 1
            and urls[0].isLocalFile()
            and Path(urls[0].toLocalFile()).suffix.lower() in {".wav", ".mp3", ".flac", ".m4a"}
        )
        self._set_reference_drop_highlight(valid)
        if valid:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_reference_drop_highlight(False)
        event.accept()

    def dropEvent(self, event):
        self._set_reference_drop_highlight(False)
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if len(urls) != 1 or not urls[0].isLocalFile():
            QMessageBox.warning(self, "Reference Voice", "Drop one local WAV, MP3, FLAC, or M4A recording.")
            event.ignore()
            return
        path = urls[0].toLocalFile()
        if Path(path).suffix.lower() not in {".wav", ".mp3", ".flac", ".m4a"}:
            QMessageBox.warning(self, "Reference Voice", "Unsupported file type. Use WAV, MP3, FLAC, or M4A.")
            event.ignore()
            return
        status = reference_audio_status(path)
        if not status["ready"]:
            QMessageBox.warning(self, "Reference Voice", "The dropped recording is missing or empty.")
            event.ignore()
            return
        self.reference_audio = path
        self.active_voice_name = Path(path).stem
        self.reference_button.setText(f"Reference Voice     •     Ready ({status['bytes'] / 1024:.0f} KB)")
        event.acceptProposedAction()

    def _choose_reference(self, button):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Reference Voice", "", "Audio (*.wav *.mp3 *.flac *.m4a)")
        if path:
            status = reference_audio_status(path)
            if not status["ready"]:
                QMessageBox.warning(self, "Reference Voice", "The selected recording is not ready for cloning.")
                return
            self.reference_audio = path
            self.active_voice_name = Path(path).stem
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
        self.worker = GenerateWorker(text, self.reference_audio, output, language_id=language_id, allow_model_download=allow_model_download, emotion=self.emotion_combo.currentText(), intensity=self.intensity_combo.currentText())
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
        language_id = self.language_combo.currentText().rsplit("(", 1)[-1].rstrip(")")
        try:
            saved = self.generated_library.add(path, self.active_voice_name, language_id)
            self.generated_audio = saved.audio_path
        except Exception as exc:
            self._generation_failed(f"Speech was generated, but could not be added to Generated Voices: {exc}")
            return
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
        #voice, QTextEdit { background:#11192d; border:1px solid #293656; border-radius:9px; padding:13px; color:white; }\n        #voice[dropActive="true"] { border:2px solid #8a68ff; background:#171f38; }
        QPushButton { background:#151d32; border:1px solid #2a3654; border-radius:8px; padding:10px 18px; color:#e8eaf4; }
        #primary { background:#7047ed; border-color:#825dff; font-weight:700; }
        QSlider::groove:horizontal { height:4px; background:#27304b; border-radius:2px; }
        QSlider::handle:horizontal { width:14px; margin:-5px 0; border-radius:7px; background:#8a68ff; }
        """
