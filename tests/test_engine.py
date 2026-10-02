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


def test_missing_reference_is_rejected_before_model_load(tmp_path):
    missing = tmp_path / "missing.wav"
    try:
        VoiceEngine("cpu").generate("hello", str(missing), str(tmp_path / "out.wav"))
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing reference audio must be rejected")


def test_empty_reference_is_rejected_before_model_load(tmp_path):
    ref = tmp_path / "empty.wav"
    ref.write_bytes(b"")
    try:
        VoiceEngine("cpu").generate("hello", str(ref), str(tmp_path / "out.wav"))
    except ValueError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("empty reference audio must be rejected")
