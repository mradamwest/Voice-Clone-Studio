from pathlib import Path

import pytest

from voice_clone_studio.core.voice_library import VoiceLibrary

def test_voice_library_round_trip(tmp_path):
    ref = tmp_path / "reference.wav"
    ref.write_bytes(b"audio")
    library = VoiceLibrary(tmp_path / "data")
    added = library.add("Test Voice", str(ref), "en")
    voices = library.list()
    assert len(voices) == 1
    assert voices[0].id == added.id
    assert voices[0].name == "Test Voice"
    assert Path(voices[0].reference_audio).parent == library.references
    assert Path(voices[0].reference_audio).read_bytes() == b"audio"

def test_voice_library_rejects_missing_reference(tmp_path):
    library = VoiceLibrary(tmp_path / "data")
    try:
        library.add("Missing", str(tmp_path / "missing.wav"))
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing reference audio must be rejected")

def test_corrupt_index_does_not_crash(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "voices.json").write_text("{broken", encoding="utf-8")
    assert VoiceLibrary(root).list() == []


def test_voice_name_length_limit(tmp_path):
    library = VoiceLibrary(tmp_path)
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"x")
    with pytest.raises(ValueError, match="80"):
        library.add("x" * 81, str(ref))


def test_voice_library_rejects_unsupported_reference_format(tmp_path):
    library = VoiceLibrary(tmp_path)
    ref = tmp_path / "voice.txt"
    ref.write_bytes(b"x")
    with pytest.raises(ValueError, match="Unsupported reference audio format"):
        library.add("Test Voice", str(ref))


def test_remove_profile_preserves_reference_audio(tmp_path):
    library = VoiceLibrary(tmp_path)
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"audio")
    profile = library.add("Keep Source", str(ref))
    assert library.remove(profile.id) is True
    assert ref.exists()
    assert library.list() == []
    assert library.remove(profile.id) is False


def test_rename_profile_preserves_reference_audio(tmp_path):
    library = VoiceLibrary(tmp_path)
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"audio")
    profile = library.add("Original", str(ref))
    renamed = library.rename(profile.id, "Renamed")
    assert renamed.name == "Renamed"
    assert Path(renamed.reference_audio) == Path(profile.reference_audio)
    assert Path(renamed.reference_audio).is_file()
    assert ref.exists()


def test_get_profile_by_stable_id(tmp_path):
    library = VoiceLibrary(tmp_path)
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"audio")
    profile = library.add("Lookup", str(ref))
    assert library.get(profile.id) == profile
    with pytest.raises(KeyError):
        library.get("missing-id")


def test_validate_references_reports_missing_source(tmp_path):
    library = VoiceLibrary(tmp_path)
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"audio")
    profile = library.add("Reference Check", str(ref))
    Path(profile.reference_audio).unlink()
    issues = library.validate_references()
    assert issues[profile.id] == "Reference audio file is missing."


def test_update_language_preserves_voice_source(tmp_path):
    library = VoiceLibrary(tmp_path)
    ref = tmp_path / "voice.wav"
    ref.write_bytes(b"audio")
    profile = library.add("Language Test", str(ref))
    updated = library.update_language(profile.id, "en")
    assert updated.language == "en"
    assert Path(updated.reference_audio) == Path(profile.reference_audio)
    assert Path(updated.reference_audio).is_file()
    assert ref.exists()


def test_replace_reference_preserves_old_and_new_audio(tmp_path):
    library = VoiceLibrary(tmp_path)
    old = tmp_path / "old.wav"; old.write_bytes(b"old")
    new = tmp_path / "new.wav"; new.write_bytes(b"new")
    profile = library.add("Replace Test", str(old))
    updated = library.replace_reference(profile.id, str(new))
    saved = Path(updated.reference_audio)
    assert saved.parent == library.references
    assert saved.read_bytes() == b"new"
    assert old.exists() and new.exists()
    new.unlink()
    assert saved.is_file()
    assert saved.read_bytes() == b"new"
    assert library.validate_references() == {}


def test_voice_names_are_deterministic(tmp_path):
    library = VoiceLibrary(tmp_path)
    a = tmp_path / "a.wav"; a.write_bytes(b"a")
    b = tmp_path / "b.wav"; b.write_bytes(b"b")
    library.add("Zulu", str(a)); library.add("alpha", str(b))
    assert library.names() == ("alpha", "Zulu")


def test_find_voice_by_name_is_case_insensitive(tmp_path):
    library = VoiceLibrary(tmp_path)
    ref = tmp_path / "voice.wav"; ref.write_bytes(b"audio")
    profile = library.add("Narrator", str(ref))
    assert library.find_by_name(" narrator ") == profile
    assert library.find_by_name("missing") is None


def test_saved_voice_owns_reference_copy(tmp_path):
    source = tmp_path / "source.wav"
    source.write_bytes(b"voice-data")
    library = VoiceLibrary(tmp_path / "library")
    profile = library.add("Durable Voice", str(source), "en")
    saved = Path(profile.reference_audio)
    assert saved.parent == library.references
    assert saved.read_bytes() == b"voice-data"
    source.unlink()
    assert saved.is_file()
    assert library.validate_references() == {}
