#define MyAppName "Voice Clone Studio"
#define MyAppVersion "0.1.0"
#define MyAppExeName "Voice Clone Studio.exe"

[Setup]
AppId={{AF337768-23E8-49E9-A5B6-8C5A58E842D4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
UninstallDisplayName={#MyAppName}
DefaultDirName={autopf}\\Voice Clone Studio
DefaultGroupName={#MyAppName}
OutputDir=..\\dist-installer
OutputBaseFilename=Voice_Clone_Studio_Setup_0.1.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Uninstallable=yes
CreateUninstallRegKey=yes

[Files]
Source: "..\\dist\\Voice Clone Studio\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{autoprograms}\\{#MyAppName}\\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
