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
            if not isinstance(data, list):
                return []
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
        if len(clean_name) > 80:
            raise ValueError("Voice name cannot exceed 80 characters.")
        ref = Path(reference_audio).expanduser().resolve()
        if ref.suffix.lower() not in {".wav", ".mp3", ".flac", ".ogg", ".m4a"}:
            raise ValueError("Unsupported reference audio format.")
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


    def remove(self, profile_id: str) -> bool:
        """Remove a saved profile record without deleting the user's source audio."""
        profiles = self.list()
        remaining = [profile for profile in profiles if profile.id != profile_id]
        if len(remaining) == len(profiles):
            return False
        self._save(remaining)
        return True


    def rename(self, profile_id: str, new_name: str) -> VoiceProfile:
        """Rename a saved profile without touching its reference recording."""
        clean_name = new_name.strip()
        if not clean_name:
            raise ValueError("Voice name cannot be empty.")
        if len(clean_name) > 80:
            raise ValueError("Voice name cannot exceed 80 characters.")
        profiles = self.list()
        target = next((p for p in profiles if p.id == profile_id), None)
        if target is None:
            raise KeyError(profile_id)
        if any(p.id != profile_id and p.name.casefold() == clean_name.casefold() for p in profiles):
            raise ValueError("A voice with this name already exists.")
        updated = VoiceProfile(target.id, clean_name, target.reference_audio, target.language)
        self._save([updated if p.id == profile_id else p for p in profiles])
        return updated


    def get(self, profile_id: str) -> VoiceProfile:
        """Return one saved profile by stable ID."""
        profile = next((p for p in self.list() if p.id == profile_id), None)
        if profile is None:
            raise KeyError(profile_id)
        return profile


    def validate_references(self) -> dict[str, str]:
        """Report saved profiles whose original reference audio is no longer usable."""
        issues: dict[str, str] = {}
        for profile in self.list():
            path = Path(profile.reference_audio).expanduser()
            if not path.is_file():
                issues[profile.id] = "Reference audio file is missing."
            elif path.stat().st_size == 0:
                issues[profile.id] = "Reference audio file is empty."
        return issues


    def update_language(self, profile_id: str, language: str) -> VoiceProfile:
        """Update a saved voice language hint without changing its source audio."""
        clean = language.strip() or "auto"
        if len(clean) > 32:
            raise ValueError("Language value cannot exceed 32 characters.")
        profiles = self.list()
        target = next((p for p in profiles if p.id == profile_id), None)
        if target is None:
            raise KeyError(profile_id)
        updated = VoiceProfile(target.id, target.name, target.reference_audio, clean)
        self._save([updated if p.id == profile_id else p for p in profiles])
        return updated


    def replace_reference(self, profile_id: str, reference_audio: str) -> VoiceProfile:
        """Point a saved voice at a new validated reference without deleting either source file."""
        reference = Path(reference_audio).expanduser().resolve()
        if reference.suffix.lower() not in {".wav", ".mp3", ".flac", ".ogg", ".m4a"}:
            raise ValueError("Unsupported reference audio format.")
        if not reference.is_file():
            raise FileNotFoundError(reference)
        if reference.stat().st_size == 0:
            raise ValueError("Reference audio file is empty.")
        profiles = self.list()
        target = next((p for p in profiles if p.id == profile_id), None)
        if target is None:
            raise KeyError(profile_id)
        updated = VoiceProfile(target.id, target.name, str(reference), target.language)
        self._save([updated if p.id == profile_id else p for p in profiles])
        return updated


    def names(self) -> tuple[str, ...]:
        """Return saved voice names in deterministic case-insensitive order."""
        return tuple(sorted((profile.name for profile in self.list()), key=str.casefold))


    def find_by_name(self, name: str) -> VoiceProfile | None:
        """Find a saved voice by name using Windows-friendly case-insensitive matching."""
        target = name.strip().casefold()
        if not target:
            return None
        return next((p for p in self.list() if p.name.casefold() == target), None)
