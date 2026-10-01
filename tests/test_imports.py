def test_package_import():
    import voice_clone_studio
    assert voice_clone_studio.__version__ == "0.1.0"

def test_window_import():
    from voice_clone_studio.ui.main_window import MainWindow
    assert MainWindow is not None
