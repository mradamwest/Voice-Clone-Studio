from dataclasses import dataclass, asdict
from pathlib import Path
import json
import uuid

@dataclass
class VoiceProfile:
    id: str
    name: str
    reference_audio: str
    language: str = "auto"

class VoiceLibrary:
    def __init__(self, root: Path | None = None):
        self.root = root or (Path.home() / ".voice_clone_studio")
        self.root.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "voices.json"

    def list(self) -> list[VoiceProfile]:
        if not self.index.exists():
            return []
        return [VoiceProfile(**v) for v in json.loads(self.index.read_text(encoding="utf-8"))]

    def add(self, name: str, reference_audio: str, language: str = "auto") -> VoiceProfile:
        profile = VoiceProfile(str(uuid.uuid4()), name.strip(), reference_audio, language)
        voices = self.list()
        voices.append(profile)
        self.index.write_text(json.dumps([asdict(v) for v in voices], indent=2), encoding="utf-8")
        return profile
