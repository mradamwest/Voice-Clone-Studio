from PyInstaller.utils.hooks import collect_all, collect_submodules

hiddenimports = collect_submodules("voice_clone_studio")
datas = []
binaries = []

# Chatterbox is imported lazily at generation time, so PyInstaller cannot
# discover it by following run.py imports. Collect its runtime package
# explicitly instead of merely installing it in the CI Python environment.
for package in ("chatterbox", "s3tokenizer", "conformer", "resemble_perth", "perth", "omegaconf", "pyloudnorm", "pykakasi", "spacy_pkuseg"):
    try:
        package_datas, package_binaries, package_hiddenimports = collect_all(package)
        datas += package_datas
        binaries += package_binaries
        hiddenimports += package_hiddenimports
    except Exception:
        pass

a = Analysis(["run.py"], pathex=["src"], binaries=binaries, datas=datas, hiddenimports=hiddenimports, hookspath=[], runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Voice Clone Studio", debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, upx_exclude=[], name="Voice Clone Studio")
