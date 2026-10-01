from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("voice_clone_studio")

a = Analysis(["src/voice_clone_studio/app.py"], pathex=["src"], binaries=[], datas=[], hiddenimports=hiddenimports, hookspath=[], runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Voice Clone Studio", debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, upx_exclude=[], name="Voice Clone Studio")
