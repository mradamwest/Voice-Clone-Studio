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
