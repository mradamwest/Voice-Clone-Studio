import os
import sys

def _self_test() -> int:
    import voice_clone_studio.app
    from voice_clone_studio.core.engine import VoiceEngine
    from voice_clone_studio.core.voice_library import VoiceLibrary
    assert VoiceEngine("cpu")._best_device() == "cpu"
    assert VoiceLibrary
    return 0

def _engine_self_test() -> int:
    marker = os.environ.get("VOICE_ENGINE_SELF_TEST_MARKER")
    def mark(name: str) -> None:
        if marker:
            with open(marker, "a", encoding="utf-8") as handle:
                handle.write(name + "\n")
                handle.flush()
    mark("start")
    import torch
    mark("torch")
    import torchaudio
    mark("torchaudio")
    # Use the same isolated loader as Generate Speech.\n    from voice_clone_studio.core.chatterbox_runtime import load_multilingual_tts_class\n    ChatterboxMultilingualTTS = load_multilingual_tts_class()
    mark("mtl_tts")
    assert torch and torchaudio and ChatterboxMultilingualTTS
    mark("success")
    os._exit(0)

if __name__ == "__main__":
    if "--app-import-self-test" in sys.argv:
        raise SystemExit(_self_test())
    if "--engine-import-self-test" in sys.argv:
        raise SystemExit(_engine_self_test())
    from voice_clone_studio.app import main
    raise SystemExit(main())
