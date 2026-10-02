from pathlib import Path
from voice_clone_studio.core.generated_library import GeneratedVoiceLibrary


def test_generated_voice_is_copied_and_indexed(tmp_path):
    source = tmp_path / "out.wav"; source.write_bytes(b"RIFFvoice")
    library = GeneratedVoiceLibrary(tmp_path / "library")
    item = library.add(str(source), "Adam", "ar")
    assert Path(item.audio_path).read_bytes() == b"RIFFvoice"
    assert item.language == "ar"
    assert library.list()[0].voice_name == "Adam"


def test_generated_voice_delete_removes_library_copy(tmp_path):
    source = tmp_path / "out.wav"; source.write_bytes(b"RIFFvoice")
    library = GeneratedVoiceLibrary(tmp_path / "library")
    item = library.add(str(source), "Voice", "en")
    stored = Path(item.audio_path)
    assert library.remove(item.id) is True
    assert not stored.exists()
    assert library.list() == []
