from voice_clone_studio.core.engine import VoiceEngine

def test_explicit_device_is_respected():
    assert VoiceEngine("cpu")._best_device() == "cpu"

def test_empty_text_is_rejected(tmp_path):
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"x")
    try:
        VoiceEngine("cpu").generate("   ", str(ref), str(tmp_path / "out.wav"))
    except ValueError:
        pass
    else:
        raise AssertionError("empty text must be rejected")
