from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os
import tempfile
import uuid

@dataclass
class VoiceProfile:
    id: str
    name: str
    reference_audio: str
    language: str = "auto"

class VoiceLibrary:
    def __init__(self, root: Path | None = None):
        if root is None:
            base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
            root = base / "Voice Clone Studio"
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "voices.json"

    def list(self) -> list[VoiceProfile]:
        if not self.index.exists():
            return []
        try:
            data = json.loads(self.index.read_text(encoding="utf-8"))
            return [VoiceProfile(**v) for v in data]
        except (json.JSONDecodeError, TypeError, KeyError):
            return []

    def _save(self, voices: list[VoiceProfile]) -> None:
        payload = json.dumps([asdict(v) for v in voices], indent=2)
        fd, temp_name = tempfile.mkstemp(prefix="voices-", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(temp_name, self.index)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def add(self, name: str, reference_audio: str, language: str = "auto") -> VoiceProfile:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Voice name cannot be empty.")
        ref = Path(reference_audio).expanduser().resolve()
        if not ref.is_file():
            raise FileNotFoundError(ref)
        if ref.stat().st_size == 0:
            raise ValueError("Reference audio file is empty.")
        if any(v.name.casefold() == clean_name.casefold() for v in self.list()):
            raise ValueError(f'A voice named "{clean_name}" already exists.')
        profile = VoiceProfile(str(uuid.uuid4()), clean_name, str(ref), language)
        voices = self.list()
        voices.append(profile)
        self._save(voices)
        return profile
