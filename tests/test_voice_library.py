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
    assert voices[0].reference_audio == str(ref)

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
