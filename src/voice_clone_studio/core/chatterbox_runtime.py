import importlib.util
import sys
from pathlib import Path


def load_multilingual_tts_class():
    """Load Chatterbox mtl_tts without executing its eager package __init__."""
    spec = importlib.util.find_spec("chatterbox")
    if spec is None or not spec.submodule_search_locations:
        raise ImportError("Chatterbox runtime is not installed.")
    package_dir = Path(next(iter(spec.submodule_search_locations)))
    module_path = package_dir / "mtl_tts.py"
    if not module_path.is_file():
        raise ImportError(f"Chatterbox multilingual runtime missing: {module_path}")
    module_name = "chatterbox.mtl_tts"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing.ChatterboxMultilingualTTS
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    if module_spec is None or module_spec.loader is None:
        raise ImportError("Unable to create Chatterbox multilingual module loader.")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = module
    module_spec.loader.exec_module(module)
    return module.ChatterboxMultilingualTTS
