from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import shutil
import tempfile
import uuid


@dataclass
class GeneratedVoice:
    id: str
    name: str
    audio_path: str
    voice_name: str
    language: str
    created_at: str


class GeneratedVoiceLibrary:
    def __init__(self, root: Path | None = None):
        if root is None:
            base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
            root = base / "Voice Clone Studio"
        self.root = Path(root)
        self.directory = self.root / "Generated Voices"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "generated_voices.json"

    def list(self) -> list[GeneratedVoice]:
        if not self.index.exists():
            return []
        try:
            data = json.loads(self.index.read_text(encoding="utf-8"))
            return [GeneratedVoice(**item) for item in data] if isinstance(data, list) else []
        except (json.JSONDecodeError, TypeError, KeyError):
            return []

    def _save(self, items: list[GeneratedVoice]) -> None:
        payload = json.dumps([asdict(item) for item in items], indent=2)
        fd, temp_name = tempfile.mkstemp(prefix="generated-", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(temp_name, self.index)
        finally:
            if os.path.exists(temp_name): os.unlink(temp_name)

    def add(self, source_audio: str, voice_name: str, language: str, name: str | None = None) -> GeneratedVoice:
        source = Path(source_audio).expanduser().resolve()
        if not source.is_file() or source.stat().st_size == 0:
            raise FileNotFoundError(source)
        item_id = str(uuid.uuid4())
        clean_name = (name or source.stem).strip() or "Generated Voice"
        destination = self.directory / f"{item_id}.wav"
        shutil.copy2(source, destination)
        item = GeneratedVoice(item_id, clean_name, str(destination), voice_name.strip() or "Reference Voice", language.strip().lower() or "en", datetime.now(timezone.utc).isoformat())
        items = self.list(); items.append(item); self._save(items)
        return item

    def remove(self, item_id: str) -> bool:
        items = self.list(); target = next((x for x in items if x.id == item_id), None)
        if target is None: return False
        Path(target.audio_path).unlink(missing_ok=True)
        self._save([x for x in items if x.id != item_id])
        return True

    def rename(self, item_id: str, name: str) -> GeneratedVoice:
        clean = name.strip()
        if not clean: raise ValueError("Generated voice name cannot be empty.")
        items = self.list(); target = next((x for x in items if x.id == item_id), None)
        if target is None: raise KeyError(item_id)
        updated = GeneratedVoice(target.id, clean, target.audio_path, target.voice_name, target.language, target.created_at)
        self._save([updated if x.id == item_id else x for x in items])
        return updated
