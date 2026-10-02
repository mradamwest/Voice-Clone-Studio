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


def test_invalid_device_is_rejected():
    try:
        VoiceEngine("metal")._best_device()
    except ValueError as exc:
        assert "Unsupported device" in str(exc)
    else:
        raise AssertionError("invalid device must be rejected")


def test_output_extension_is_validated_before_save(tmp_path):
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"x")
    engine = VoiceEngine("cpu")
    class FakeWave:
        def numel(self): return 1
    class FakeModel:
        sr = 24000
        def generate(self, *args, **kwargs): return FakeWave()
    engine._model = FakeModel()
    try:
        engine.generate("hello", str(ref), str(tmp_path / "out.mp3"))
    except ValueError as exc:
        assert "WAV" in str(exc)
    else:
        raise AssertionError("non-WAV output must be rejected")


def test_reference_cannot_be_overwritten(tmp_path):
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"x")
    engine = VoiceEngine("cpu")
    class FakeWave:
        def numel(self): return 1
    class FakeModel:
        sr = 24000
        def generate(self, *args, **kwargs): return FakeWave()
    engine._model = FakeModel()
    try:
        engine.generate("hello", str(ref), str(ref))
    except ValueError as exc:
        assert "overwrite" in str(exc).lower()
    else:
        raise AssertionError("reference overwrite must be rejected")


def test_unsupported_reference_format_is_rejected_before_model_load(tmp_path):
    ref = tmp_path / "voice.txt"
    ref.write_bytes(b"x")
    try:
        VoiceEngine("cpu").generate("hello", str(ref), str(tmp_path / "out.wav"))
    except ValueError as exc:
        assert "Unsupported reference audio format" in str(exc)
    else:
        raise AssertionError("unsupported reference format must be rejected")
