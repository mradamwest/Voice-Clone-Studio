$ErrorActionPreference = "Stop"
python -m pip install -e ".[dev]"
python -m pytest -q
python -m PyInstaller --noconfirm --clean VoiceCloneStudio.spec
if (!(Test-Path "dist\\Voice Clone Studio\\Voice Clone Studio.exe")) { throw "Packaged executable missing" }
$inno = "${env:ProgramFiles(x86)}\\Inno Setup 6\\ISCC.exe"
if (!(Test-Path $inno)) { throw "Inno Setup 6 is required to build the installer" }
& $inno "installer\\VoiceCloneStudio.iss"
if (!(Test-Path "dist-installer\\Voice_Clone_Studio_Setup_0.1.0.exe")) { throw "Installer missing" }
