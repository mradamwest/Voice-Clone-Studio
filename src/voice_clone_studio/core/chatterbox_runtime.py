import importlib


def load_multilingual_tts_class():
    """Load the Chatterbox multilingual TTS class from the installed or packaged module."""
    try:
        module = importlib.import_module("chatterbox.mtl_tts")
    except (ImportError, ModuleNotFoundError) as exc:
        raise ImportError("Chatterbox multilingual runtime is unavailable.") from exc
    try:
        return module.ChatterboxMultilingualTTS
    except AttributeError as exc:
        raise ImportError("Chatterbox multilingual runtime is missing ChatterboxMultilingualTTS.") from exc
