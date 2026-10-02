from pathlib import Path


def test_voice_ui_guards_active_worker_shutdown():
    text = Path("src/voice_clone_studio/ui/main_window.py").read_text(encoding="utf-8")
    assert "def closeEvent" in text
    assert "isRunning()" in text
