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
    # Import the exact modules needed by Generate Speech from the packaged EXE.
    # This catches the failure that a source-environment import test cannot.
    import torch
    import torchaudio
    import chatterbox
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    assert torch
    assert torchaudio
    assert chatterbox
    assert ChatterboxMultilingualTTS
    # Torch/audio native runtimes can keep non-Python worker state alive after
    # successful imports. This is a packaging probe, so exit immediately once
    # all required engine modules have loaded.
    os._exit(0)

if __name__ == "__main__":
    if "--app-import-self-test" in sys.argv:
        raise SystemExit(_self_test())
    if "--engine-import-self-test" in sys.argv:
        raise SystemExit(_engine_self_test())
    from voice_clone_studio.app import main
    raise SystemExit(main())
