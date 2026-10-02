import pytest

from voice_clone_studio.core.engine import VoiceEngine, engine_status, ensure_voice_ready, first_run_status, validate_generation_request, model_cache_status, reference_audio_status, generation_output_path, generation_preflight, verify_generated_audio

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


def test_output_directory_path_is_rejected(tmp_path):
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"x")
    out = tmp_path / "folder.wav"
    out.mkdir()
    engine = VoiceEngine("cpu")
    class FakeWave:
        def numel(self): return 1
    class FakeModel:
        sr = 24000
        def generate(self, *args, **kwargs): return FakeWave()
    engine._model = FakeModel()
    try:
        engine.generate("hello", str(ref), str(out))
    except ValueError as exc:
        assert "directory" in str(exc).lower()
    else:
        raise AssertionError("directory output path must be rejected")


def test_invalid_sample_rate_is_rejected(tmp_path):
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"x")
    engine = VoiceEngine("cpu")
    class FakeWave:
        def numel(self): return 1
    class FakeModel:
        sr = 0
        def generate(self, *args, **kwargs): return FakeWave()
    engine._model = FakeModel()
    try:
        engine.generate("hello", str(ref), str(tmp_path / "out.wav"))
    except RuntimeError as exc:
        assert "sample rate" in str(exc).lower()
    else:
        raise AssertionError("invalid sample rate must be rejected")


def test_engine_status_does_not_load_model():
    status = engine_status("cpu")
    assert status["device"] == "cpu"
    assert status["model_loaded"] is False
    assert isinstance(status["available"], bool)


def test_validate_generation_request_normalizes_paths(tmp_path):
    ref = tmp_path / "voice.wav"; ref.write_bytes(b"audio")
    text, reference, out = validate_generation_request("  hello  ", str(ref), str(tmp_path / "out.wav"))
    assert text == "hello"
    assert reference == ref.resolve()
    assert out == (tmp_path / "out.wav").resolve()


def test_generate_uses_shared_request_validation(tmp_path):
    ref = tmp_path / "voice.txt"; ref.write_bytes(b"x")
    try:
        VoiceEngine("cpu").generate("hello", str(ref), str(tmp_path / "out.wav"))
    except ValueError as exc:
        assert "Unsupported reference audio format" in str(exc)
    else:
        raise AssertionError("shared validation must reject unsupported reference audio")


def test_model_cache_status_does_not_require_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("TORCH_HOME", str(tmp_path / "torch-home"))
    status = model_cache_status()
    assert status["exists"] is False
    assert status["files"] == ()
    assert status["bytes"] == 0


def test_reference_audio_status_reports_readiness(tmp_path):
    ref = tmp_path / "voice.wav"; ref.write_bytes(b"audio")
    status = reference_audio_status(str(ref))
    assert status["ready"] is True
    assert status["bytes"] == 5


def test_generation_output_path_never_overwrites(tmp_path):
    first = tmp_path / "voice-clone.wav"; first.write_bytes(b"existing")
    assert generation_output_path(tmp_path) == tmp_path / "voice-clone_2.wav"


def test_verify_generated_audio_requires_nonempty_wav(tmp_path):
    wav = tmp_path / "generated.wav"; wav.write_bytes(b"RIFFdata")
    assert verify_generated_audio(wav)["ready"] is True
    empty = tmp_path / "empty.wav"; empty.write_bytes(b"")
    with pytest.raises(RuntimeError, match="empty"):
        verify_generated_audio(empty)


def test_voice_first_run_status_reports_model_download(monkeypatch):
    monkeypatch.setattr("voice_clone_studio.core.engine.engine_status", lambda device=None: {"available": True})
    monkeypatch.setattr("voice_clone_studio.core.engine.model_cache_status", lambda: {"directory": "cache", "files": (), "bytes": 0, "exists": False})
    status = first_run_status()
    assert status["model_cached"] is False
    assert status["requires_model_download"] is True


def test_ensure_voice_ready_requires_download_approval(monkeypatch):
    monkeypatch.setattr("voice_clone_studio.core.engine.first_run_status", lambda: {"runtime_available": True, "requires_model_download": True})
    with pytest.raises(RuntimeError, match="approval"):
        ensure_voice_ready()
    assert ensure_voice_ready(allow_model_download=True)["requires_model_download"] is True


def test_generation_preflight_combines_request_and_model_readiness(monkeypatch, tmp_path):
    ref = tmp_path / "voice.wav"; ref.write_bytes(b"audio")
    monkeypatch.setattr("voice_clone_studio.core.engine.ensure_voice_ready", lambda allow_model_download=False: {"runtime_available": True, "model_cached": True})
    status = generation_preflight(" hello ", str(ref), str(tmp_path / "out.wav"))
    assert status["text"] == "hello"
    assert status["model_cached"] is True
