from pathlib import Path
import importlib.util

class VoiceEngine:
    """Lazy Chatterbox adapter; model loading never blocks application startup."""

    def __init__(self, device: str | None = None):
        self._model = None
        self.device = device

    @property
    def available(self) -> bool:
        # Do not import chatterbox here. Its package initializer eagerly imports
        # optional engines and can stall a frozen Windows process. Presence of
        # the exact module we use is enough for this lightweight readiness check.
        return importlib.util.find_spec("chatterbox.mtl_tts") is not None

    def _best_device(self) -> str:
        if self.device:
            if self.device not in {"cpu", "cuda"}:
                raise ValueError(f"Unsupported device: {self.device}")
            return self.device
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _load(self):
        if self._model is None:
            if not self.available:
                raise RuntimeError("Chatterbox multilingual engine is not installed.")
            from voice_clone_studio.core.chatterbox_runtime import load_multilingual_tts_class
            ChatterboxMultilingualTTS = load_multilingual_tts_class()
            try:
                # Use the upstream multilingual V2 checkpoint as the compatibility baseline.\n                # V3 has known regressions in non-English multilingual generation.
                self._model = ChatterboxMultilingualTTS.from_pretrained(
                    device=self._best_device(), t3_model="v2"
                )
            except TypeError as exc:
                # Some published Chatterbox builds have temporarily shipped
                # without the t3_model keyword. Fall back without hiding any
                # other initialization failure.
                if "t3_model" not in str(exc):
                    raise
                self._model = ChatterboxMultilingualTTS.from_pretrained(
                    device=self._best_device()
                )
        return self._model

    def generate(self, text: str, reference_audio: str, output: str, language_id: str = "en") -> Path:
        """Generate cloned speech without loading the model until validation passes."""
        clean_text, reference, out = validate_generation_request(text, reference_audio, output)
        if not clean_text:
            raise ValueError("Text cannot be empty.")
        model = self._load()
        language_id = language_id.strip().lower()
        supported = getattr(model, "get_supported_languages", lambda: {})()
        if supported and language_id not in supported:
            raise ValueError(f"Unsupported language: {language_id}")
        wav = model.generate(clean_text, language_id=language_id, audio_prompt_path=str(reference))
        if wav is None or not hasattr(wav, "numel") or wav.numel() == 0:
            raise RuntimeError("Voice engine returned no audio.")
        import torchaudio
        # Chatterbox can occasionally return a valid but nearly inaudible waveform.
        # Raise only abnormally quiet output; leave normal model output untouched.
        try:
            peak = float(wav.detach().abs().max().item())
        except (AttributeError, TypeError, ValueError):
            peak = None
        if peak is not None and 0.0 < peak < 0.05:
            target_peak = 0.85
            wav = wav * (target_peak / peak)
        if out.exists() and out.is_dir():
            raise ValueError("Voice output path points to a directory.")
        out.parent.mkdir(parents=True, exist_ok=True)
        sample_rate = getattr(model, "sr", None)
        if not isinstance(sample_rate, int) or sample_rate <= 0:
            raise RuntimeError("Voice engine returned an invalid sample rate.")
        torchaudio.save(str(out), wav, sample_rate)
        if not out.is_file() or out.stat().st_size == 0:
            raise RuntimeError("Generated voice audio was not written successfully.")
        return out


def engine_status(device: str | None = None) -> dict[str, object]:
    """Return lightweight readiness information without loading model weights."""
    engine = VoiceEngine(device)
    return {
        "available": engine.available,
        "device": engine._best_device(),
        "model_loaded": engine._model is not None,
    }


def validate_generation_request(text: str, reference_audio: str, output: str) -> tuple[str, Path, Path]:
    """Validate a generation request without loading the voice model."""
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Text cannot be empty.")
    reference = Path(reference_audio).expanduser().resolve()
    if reference.suffix.lower() not in {".wav", ".mp3", ".flac", ".ogg", ".m4a"}:
        raise ValueError("Unsupported reference audio format.")
    if not reference.is_file():
        raise FileNotFoundError(reference)
    if reference.stat().st_size == 0:
        raise ValueError("Reference audio file is empty.")
    out = Path(output).expanduser().resolve()
    if out == reference:
        raise ValueError("Output file cannot overwrite the reference audio.")
    if out.suffix.lower() != ".wav":
        raise ValueError("Voice output must be a WAV file.")
    return clean_text, reference, out


def model_cache_status() -> dict[str, object]:
    """Report the local Torch model cache without downloading or loading model weights."""
    import os
    default_root = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
    torch_home = os.environ.get("TORCH_HOME")
    root = (Path(torch_home).expanduser() / "hub" / "checkpoints") if torch_home else default_root
    root = root.resolve()
    files = tuple(sorted((p for p in root.glob("*") if p.is_file()), key=lambda p: p.name.casefold())) if root.is_dir() else ()
    return {"directory": str(root), "exists": root.is_dir(), "files": tuple(p.name for p in files), "bytes": sum(p.stat().st_size for p in files)}


def reference_audio_status(reference_audio: str) -> dict[str, object]:
    """Return UI-ready reference-file status without loading the AI model."""
    path = Path(reference_audio).expanduser().resolve()
    supported = path.suffix.lower() in {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
    exists = path.is_file()
    size = path.stat().st_size if exists else 0
    return {"path": str(path), "exists": exists, "supported": supported, "bytes": size, "ready": exists and supported and size > 0}


def generation_output_path(root: str | Path, filename: str = "voice-clone.wav") -> Path:
    """Create a safe deterministic WAV destination without touching an existing file."""
    directory = Path(root).expanduser().resolve()
    name = Path(filename).name
    if not name.lower().endswith(".wav"):
        raise ValueError("Generated voice filename must use .wav.")
    candidate = directory / name
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    index = 2
    while True:
        alternative = directory / f"{stem}_{index}.wav"
        if not alternative.exists():
            return alternative
        index += 1


def verify_generated_audio(path: str | Path) -> dict[str, object]:
    """Verify a generated WAV before the UI enables playback/export."""
    audio = Path(path).expanduser().resolve()
    if audio.suffix.lower() != ".wav":
        raise ValueError("Generated audio must be a WAV file.")
    if not audio.is_file():
        raise FileNotFoundError(audio)
    size = audio.stat().st_size
    if size <= 0:
        raise RuntimeError("Generated audio file is empty.")
    return {"path": str(audio), "bytes": size, "ready": True}


def first_run_status() -> dict[str, object]:
    """Return UI-ready first-run voice model state without loading/downloading weights."""
    engine = engine_status("cpu")
    cache = model_cache_status()
    cached = bool(cache["files"])
    return {
        "runtime_available": engine["available"],
        "cache_directory": cache["directory"],
        "cached_files": cache["files"],
        "model_cached": cached,
        "requires_model_download": bool(engine["available"]) and not cached,
    }


def ensure_voice_ready(allow_model_download: bool = False) -> dict[str, object]:
    """Require explicit approval before first-run voice model acquisition."""
    status = first_run_status()
    if not status["runtime_available"]:
        raise RuntimeError("Voice cloning runtime is not available.")
    if status["requires_model_download"] and not allow_model_download:
        raise RuntimeError("Voice model is not cached; model download approval is required.")
    return status


def generation_preflight(text: str, reference_audio: str, output: str, allow_model_download: bool = False) -> dict[str, object]:
    """Single preflight contract for the UI before starting a generation worker."""
    clean_text, reference, destination = validate_generation_request(text, reference_audio, output)
    readiness = ensure_voice_ready(allow_model_download=allow_model_download)
    return {
        "text": clean_text,
        "reference_audio": str(reference),
        "output": str(destination),
        **readiness,
    }
