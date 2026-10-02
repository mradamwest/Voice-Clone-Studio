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
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            try:
                # Current upstream V3 documentation accepts t3_model="v3".
                self._model = ChatterboxMultilingualTTS.from_pretrained(
                    device=self._best_device(), t3_model="v3"
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

    def generate(self, text: str, reference_audio: str, output: str) -> Path:
        """Generate cloned speech without loading the model until validation passes."""
        if not text.strip():
            raise ValueError("Text cannot be empty.")
        reference = Path(reference_audio).expanduser().resolve()
        if not reference.is_file():
            raise FileNotFoundError(reference)
        if reference.stat().st_size == 0:
            raise ValueError("Reference audio file is empty.")
        model = self._load()
        wav = model.generate(text.strip(), audio_prompt_path=str(reference))
        if wav is None or not hasattr(wav, "numel") or wav.numel() == 0:
            raise RuntimeError("Voice engine returned no audio.")
        import torchaudio
        out = Path(output).expanduser().resolve()
        if out == reference:
            raise ValueError("Output file cannot overwrite the reference audio.")
        if out.suffix.lower() != ".wav":
            raise ValueError("Voice output must be a WAV file.")
        out.parent.mkdir(parents=True, exist_ok=True)
        sample_rate = getattr(model, "sr", None)
        if not isinstance(sample_rate, int) or sample_rate <= 0:
            raise RuntimeError("Voice engine returned an invalid sample rate.")
        torchaudio.save(str(out), wav, sample_rate)
        return out
