#define MyAppName "pyVideoTrans-DH"
#define MyAppExeName "sp.exe"

#ifndef SourceDir
  #error SourceDir must point to the verified PyInstaller onedir candidate.
#endif
#ifndef OutputDir
  #error OutputDir is required.
#endif
#ifndef AppVersion
  #error AppVersion is required.
#endif
#ifndef SetupBaseFilename
  #error SetupBaseFilename is required.
#endif
#ifndef LicensePath
  #error LicensePath is required.
#endif

[Setup]
AppId={{AE6F9A53-7319-4F6D-80C1-4D50287037D1}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher=pyVideoTrans-DH
DefaultDirName={localappdata}\Programs\pyVideoTrans-DH
DefaultGroupName=pyVideoTrans-DH
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename={#SetupBaseFilename}
LicenseFile={#LicensePath}
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#AppVersion}.0

[Tasks]
Name: "startmenuicon"; Description: "Create a Start Menu shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\pyVideoTrans-DH"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: startmenuicon
Name: "{userdesktop}\pyVideoTrans-DH"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch pyVideoTrans-DH"; Flags: nowait postinstall skipifsilent

; User settings live under %LOCALAPPDATA%\pyVideoTrans and are intentionally
; outside {app}. There is no [UninstallDelete] entry for that data directory,
; so upgrades and uninstall preserve user settings by default.
