; Inno Setup script: turns dist\medu.exe into Medu-Setup-<version>.exe
; Build with packaging\build.ps1, or open this file in Inno Setup and press Compile.

#define AppName "Medu"
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{6B1E2A55-4D2C-4E8B-9C1A-3D5E7F9A0B21}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=CharlseEmpire Tech
AppPublisherURL=https://github.com/fanyicharllson/medu
AppSupportURL=https://github.com/fanyicharllson/medu/issues
AppCopyright=Copyright (c) 2026 Charllson & Adrien Tello
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Wizard pages, in order: Welcome -> About Medu -> Licence (must accept) ->
; About you (name, optional) -> Folder -> Options -> Ready -> Install -> Getting started -> Finish
InfoBeforeFile=welcome.txt
LicenseFile=..\LICENSE
InfoAfterFile=getting-started.txt
WizardImageFile=wizard-side.bmp
WizardSmallImageFile=wizard-small.bmp
SetupIconFile=medu.ico
UninstallDisplayIcon={app}\medu.exe
OutputDir=..\dist
OutputBaseFilename=Medu-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes
ChangesAssociations=yes
PrivilegesRequiredOverridesAllowed=dialog

[Tasks]
Name: "addtopath"; Description: "Add medu to PATH (use it from any terminal)"; Flags: checkedonce
Name: "associate"; Description: "Open .med and .mdt files with Medu"; Flags: checkedonce
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\medu.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\samples\*"; DestDir: "{app}\samples"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Medu (interactive)"; Filename: "{app}\medu.exe"
Name: "{autodesktop}\Medu"; Filename: "{app}\medu.exe"; Tasks: desktopicon
Name: "{group}\Medu samples"; Filename: "{app}\samples"
Name: "{group}\Uninstall Medu"; Filename: "{uninstallexe}"

[Registry]
; PATH (current user or all users, depending on install mode)
Root: HKA; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; \
  ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))
; .med = Medu program, .mdt = Medumba text; double-click opens a terminal that stays open
Root: HKA; Subkey: "Software\Classes\.med"; ValueType: string; ValueData: "Medu.Program"; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Medu.Program"; ValueType: string; ValueData: "Medu program"; Flags: uninsdeletekey; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Medu.Program\DefaultIcon"; ValueType: string; ValueData: "{app}\medu.exe,0"; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Medu.Program\shell\open\command"; ValueType: string; ValueData: "cmd.exe /k ""{app}\medu.exe"" run ""%1"""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.mdt"; ValueType: string; ValueData: "Medu.Text"; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Medu.Text"; ValueType: string; ValueData: "Medumba text"; Flags: uninsdeletekey; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Medu.Text\DefaultIcon"; ValueType: string; ValueData: "{app}\medu.exe,0"; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Medu.Text\shell\open\command"; ValueType: string; ValueData: "cmd.exe /k ""{app}\medu.exe"" translate ""%1"""; Tasks: associate

[Run]
Filename: "{cmd}"; Parameters: "/k ""{app}\medu.exe"""; Description: "Open Medu now"; Flags: postinstall nowait skipifsilent

[Code]
var
  NamePage: TInputQueryWizardPage;

{ "About you" page, after the licence. Nothing leaves the computer: the name is
  saved in %APPDATA%\Medu\config.json and Medu uses it to say "Welcome, <name>". }
procedure InitializeWizard;
begin
  NamePage := CreateInputQueryPage(wpLicense,
    'About you', 'How should Medu greet you?',
    'Medu works offline. Your name stays on this computer and is never sent anywhere. You can leave it empty.');
  NamePage.Add('Your name (optional):', False);
  NamePage.Values[0] := GetUserNameString;
end;

function JsonEscape(S: string): string;
begin
  StringChangeEx(S, '\', '\\', True);
  StringChangeEx(S, '"', '\"', True);
  Result := S;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var Dir: string; Lines: TArrayOfString;
begin
  if CurStep <> ssPostInstall then Exit;
  Dir := ExpandConstant('{userappdata}\Medu');
  ForceDirectories(Dir);
  SetArrayLength(Lines, 1);
  Lines[0] := '{"name": "' + JsonEscape(Trim(NamePage.Values[0])) + '"}';
  SaveStringsToUTF8File(Dir + '\config.json', Lines, False);
end;
function NeedsAddPath(Dir: string): Boolean;
var Paths: string;
begin
  if not RegQueryStringValue(HKA, 'Environment', 'Path', Paths) then Paths := '';
  Result := Pos(';' + Uppercase(Dir) + ';', ';' + Uppercase(Paths) + ';') = 0;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var Paths, Dir: string; P: Integer;
begin
  if CurUninstallStep <> usPostUninstall then Exit;
  Dir := ExpandConstant('{app}');
  if RegQueryStringValue(HKA, 'Environment', 'Path', Paths) then begin
    P := Pos(';' + Uppercase(Dir), Uppercase(Paths));
    if P > 0 then begin
      Delete(Paths, P, Length(Dir) + 1);
      RegWriteExpandStringValue(HKA, 'Environment', 'Path', Paths);
    end;
  end;
end;
