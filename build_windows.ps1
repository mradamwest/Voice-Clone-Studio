$ErrorActionPreference = "Stop"
# CI already installs dependencies, runs tests, and builds the packaged app.
# Reuse the verified package instead of rebuilding it during installer creation.
if (!(Test-Path "dist\Voice Clone Studio\Voice Clone Studio.exe")) {
    python -m PyInstaller --noconfirm --clean VoiceCloneStudio.spec
}
if (!(Test-Path "dist\Voice Clone Studio\Voice Clone Studio.exe")) { throw "Packaged executable missing" }

$innoRoot = Join-Path $env:TEMP "voice-clone-studio-inno"
$innoInstaller = Join-Path $env:TEMP "innosetup-6.7.3.exe"
$inno = Join-Path $innoRoot "ISCC.exe"
if (!(Test-Path $inno)) {
    New-Item -ItemType Directory -Force -Path $innoRoot | Out-Null
    if (!(Test-Path $innoInstaller)) {
        Invoke-WebRequest "https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe" -OutFile $innoInstaller
    }
    $proc = Start-Process -FilePath $innoInstaller -ArgumentList @("/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART","/SP-","/CURRENTUSER","/DIR=$innoRoot") -Wait -PassThru
    if ($proc.ExitCode -ne 0) { throw "Local Inno Setup extraction failed with exit code $($proc.ExitCode)" }
}
if (!(Test-Path $inno)) {
    $candidate = Get-ChildItem -Path $innoRoot -Filter "ISCC.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($candidate) { $inno = $candidate.FullName }
}
if (!(Test-Path $inno)) { throw "Local Inno Setup compiler missing after isolated install" }
& $inno "installer\VoiceCloneStudio.iss"
if ($LASTEXITCODE -ne 0) { throw "Installer compilation failed with exit code $LASTEXITCODE" }
if (!(Test-Path "dist-installer\Voice_Clone_Studio_Setup_0.1.0.exe")) { throw "Installer missing" }
