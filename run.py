import sys

def _self_test() -> int:
    import voice_clone_studio.app
    from voice_clone_studio.core.engine import VoiceEngine
    from voice_clone_studio.core.voice_library import VoiceLibrary
    assert VoiceEngine("cpu")._best_device() == "cpu"
    assert VoiceLibrary
    return 0

if __name__ == "__main__":
    if "--app-import-self-test" in sys.argv:
        raise SystemExit(_self_test())
    from voice_clone_studio.app import main
    raise SystemExit(main())
