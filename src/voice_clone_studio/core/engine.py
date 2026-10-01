from pathlib import Path

class VoiceEngine:
    """Lazy Chatterbox adapter so the UI can start without loading the model."""

    def __init__(self):
        self._model = None

    @property
    def available(self) -> bool:
        try:
            import chatterbox  # noqa: F401
            return True
        except ImportError:
            return False

    def _load(self):
        if self._model is None:
            if not self.available:
                raise RuntimeError("Chatterbox engine is not installed.")
            from chatterbox.tts import ChatterboxTTS
            self._model = ChatterboxTTS.from_pretrained(device="cuda")
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
