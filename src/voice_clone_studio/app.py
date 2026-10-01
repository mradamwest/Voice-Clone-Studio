import sys
from PySide6.QtWidgets import QApplication
from .ui.main_window import MainWindow

def main() -> int:
    if "--app-import-self-test" in sys.argv:
        from .core.engine import VoiceEngine
        from .core.voice_library import VoiceLibrary
        assert VoiceEngine("cpu")._best_device() == "cpu"
        assert VoiceLibrary
        return 0
    app = QApplication(sys.argv)
    app.setApplicationName("Voice Clone Studio")
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
