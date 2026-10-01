from voice_clone_studio.core.voice_library import VoiceLibrary

def test_voice_library_round_trip(tmp_path):
    library = VoiceLibrary(tmp_path)
    added = library.add("Test Voice", "reference.wav", "en")
    voices = library.list()
    assert len(voices) == 1
    assert voices[0].id == added.id
    assert voices[0].name == "Test Voice"
    assert voices[0].reference_audio == "reference.wav"
