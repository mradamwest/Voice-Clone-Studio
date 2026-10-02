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
            self._model = ChatterboxMultilingualTTS.from_pretrained(device=self._best_device(), t3_model="v3")
        return self._model

    def generate(self, text: str, reference_audio: str, output: str) -> Path:
        if not text.strip():
            raise ValueError("Text cannot be empty.")
        if not Path(reference_audio).is_file():
            raise FileNotFoundError(reference_audio)
        model = self._load()
        wav = model.generate(text, audio_prompt_path=reference_audio)
        import torchaudio
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        torchaudio.save(str(out), wav, model.sr)
        return out
