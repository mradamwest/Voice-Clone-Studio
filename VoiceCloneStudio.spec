from PyInstaller.utils.hooks import collect_all, collect_submodules

hiddenimports = collect_submodules("voice_clone_studio")
datas = []
binaries = []

# Chatterbox's package-level __init__ eagerly imports every engine variant.
# Do NOT collect the whole package: that drags optional Turbo/VC dependency
# graphs into startup and can deadlock a frozen Windows import. Bundle only
# the multilingual engine modules used by VoiceEngine plus their dependencies.
for package in ("s3tokenizer", "conformer", "resemble_perth", "perth", "omegaconf", "pyloudnorm", "pykakasi", "spacy_pkuseg"):
    try:
        package_datas, package_binaries, package_hiddenimports = collect_all(package)
        datas += package_datas
        binaries += package_binaries
        hiddenimports += package_hiddenimports
    except Exception:
        pass

hiddenimports += [
    "chatterbox.mtl_tts",
    "chatterbox.models.t3",
    "chatterbox.models.s3gen",
    "chatterbox.models.tokenizers",
    "chatterbox.models.voice_encoder",
]

a = Analysis(["run.py"], pathex=["src"], binaries=binaries, datas=datas, hiddenimports=hiddenimports, hookspath=[], runtime_hooks=[], excludes=["chatterbox.tts_turbo", "chatterbox.vc"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Voice Clone Studio", debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, upx_exclude=[], name="Voice Clone Studio")
