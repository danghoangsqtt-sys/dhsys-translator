[CmdletBinding()]
param(
    [string]$ManifestPath = "",
    [string]$EvidencePath = "",
    [ValidateSet("DeveloperHost", "WindowsSandbox", "DisposableVM", "CleanUser")]
    [string]$EnvironmentKind = "DeveloperHost",
    [string]$WorkRoot = "",
    [switch]$KeepWorkRoot
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SystemTemp = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd("\")
$AppId = "{AE6F9A53-7319-4F6D-80C1-4D50287037D1}_is1"
$UninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppId"

function Assert-SafeWorkRoot([string]$Path) {
    $Resolved = [System.IO.Path]::GetFullPath($Path).TrimEnd("\")
    $Leaf = Split-Path $Resolved -Leaf
    $Parent = (Split-Path $Resolved -Parent).TrimEnd("\")
    $DriveRoot = [System.IO.Path]::GetPathRoot($Resolved).TrimEnd("\")
    if ($Leaf -notmatch '^pyvideotrans-recipient-[0-9a-f]{32}$') {
        throw "WorkRoot leaf must be named pyvideotrans-recipient-<32 hex characters>."
    }
    if (-not (Test-Path $Parent -PathType Container) -or $Parent -eq $DriveRoot) {
        throw "WorkRoot parent must be an existing non-root temporary directory."
    }
    if ($Resolved.StartsWith($ProjectRoot + "\", [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "WorkRoot must be outside the source tree."
    }
    return $Resolved
}

function Quote-ProcessArgument([string]$Value) {
    return '"' + $Value.Replace('"', '\"') + '"'
}

function Invoke-CheckedProcess(
    [string]$FilePath,
    [string[]]$ArgumentList,
    [string]$Description
) {
    $Process = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -PassThru -Wait
    $Process.Refresh()
    if ($Process.ExitCode -ne 0) {
        throw "$Description failed with exit code $($Process.ExitCode)."
    }
}

function Invoke-FrozenProbe(
    [string]$Executable,
    [string]$ProbeScript,
    [string]$ReportPath,
    [string[]]$ExtraArguments = @()
) {
    $Arguments = @(
        (Quote-ProcessArgument $ProbeScript),
        (Quote-ProcessArgument $ReportPath)
    ) + $ExtraArguments
    $Process = Start-Process -FilePath $Executable -ArgumentList $Arguments -PassThru -Wait
    $Process.Refresh()
    if ($Process.ExitCode -ne 0) {
        $Detail = "exit code $($Process.ExitCode)"
        if (Test-Path $ReportPath -PathType Leaf) {
            try {
                $FailedReport = Get-Content $ReportPath -Raw | ConvertFrom-Json
                if ($FailedReport.error) { $Detail = [string]$FailedReport.error }
            } catch {
                $Detail = "exit code $($Process.ExitCode); report could not be parsed"
            }
        }
        throw "Frozen probe $(Split-Path $ProbeScript -Leaf) failed: $Detail"
    }
    $Report = Get-Content $ReportPath -Raw | ConvertFrom-Json
    if ($Report.status -ne "pass") {
        throw "Frozen probe $(Split-Path $ProbeScript -Leaf) reported failure."
    }
    return $Report
}

function Get-InstallSnapshot([string]$InstallDir) {
    $Files = @(Get-ChildItem $InstallDir -File -Recurse | Where-Object { $_.Name -notlike "unins*" })
    $TotalBytes = ($Files | Measure-Object -Property Length -Sum).Sum
    return [ordered]@{
        file_count = $Files.Count
        total_bytes = [long]$TotalBytes
        entry_point_sha256 = (Get-FileHash (Join-Path $InstallDir "sp.exe") -Algorithm SHA256).Hash
    }
}

function Test-SnapshotEqual($Before, $After) {
    return (
        $Before.file_count -eq $After.file_count -and
        $Before.total_bytes -eq $After.total_bytes -and
        $Before.entry_point_sha256 -eq $After.entry_point_sha256
    )
}

if (-not $ManifestPath) {
    $VersionText = Get-Content (Join-Path $ProjectRoot "pyproject.toml") -Raw
    $Version = [regex]::Match($VersionText, '(?m)^version\s*=\s*"([0-9]+(?:\.[0-9]+){1,3})"').Groups[1].Value
    $ManifestPath = Join-Path $ProjectRoot "release\local\pyVideoTrans-DH-$Version-win64-manifest.json"
}
$ManifestPath = (Resolve-Path $ManifestPath).Path
$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$ReleaseDir = Split-Path $ManifestPath -Parent
$SetupPath = Join-Path $ReleaseDir $Manifest.artifacts.setup.name
if (-not (Test-Path $SetupPath -PathType Leaf)) {
    throw "Setup artifact declared by the manifest is missing."
}
if ((Get-FileHash $SetupPath -Algorithm SHA256).Hash -ne $Manifest.artifacts.setup.sha256) {
    throw "Setup artifact checksum does not match the release manifest."
}

if (-not $EvidencePath) {
    $EvidencePath = Join-Path $ProjectRoot ".DHSYSTEM\phases\5\evidence\task-5.5-installed-smoke.json"
}
$EvidencePath = [System.IO.Path]::GetFullPath($EvidencePath)

if (-not $WorkRoot) {
    $WorkRoot = Join-Path $SystemTemp ("pyvideotrans-recipient-" + [guid]::NewGuid().ToString("N"))
}
$WorkRoot = Assert-SafeWorkRoot $WorkRoot

if (Test-Path $UninstallKey) {
    $Existing = Get-ItemProperty $UninstallKey
    throw "An existing pyVideoTrans-DH installation is registered for this user at '$($Existing.InstallLocation)'. Use a clean user, Sandbox, or disposable VM."
}

$Drive = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($WorkRoot))
if ($Drive.AvailableFreeSpace -lt 10GB) {
    throw "At least 10 GiB of free temporary disk space is required."
}

$InstallDir = Join-Path $WorkRoot "install"
$IsolatedLocalAppData = Join-Path $WorkRoot "localappdata"
$IsolatedTemp = Join-Path $WorkRoot "temp"
$ReportsDir = Join-Path $WorkRoot "reports"
$InstallLog = Join-Path $WorkRoot "install.log"
$UpgradeLog = Join-Path $WorkRoot "upgrade.log"
$UninstallLog = Join-Path $WorkRoot "uninstall.log"
$SmokeScript = Join-Path $ProjectRoot "scripts\smoke_frozen.py"
$UiSmokeScript = Join-Path $ProjectRoot "scripts\smoke_frozen_ui.py"
$CliScript = Join-Path $ProjectRoot "cli.py"
$Executable = Join-Path $InstallDir "sp.exe"
$Uninstaller = Join-Path $InstallDir "unins000.exe"
$CleanEnvironment = $EnvironmentKind -ne "DeveloperHost"
$AclDenied = $false
$Installed = $false
$Uninstalled = $false

$OldPath = $env:PATH
$OldLocalAppData = $env:LOCALAPPDATA
$OldQt = $env:QT_QPA_PLATFORM
$OldPyVideoTransLang = $env:PYVIDEOTRANS_LANG
$OldTemp = $env:TEMP
$OldTmp = $env:TMP
$RecipientPath = @(
    (Join-Path $env:SystemRoot "System32"),
    $env:SystemRoot,
    (Join-Path $env:SystemRoot "System32\Wbem"),
    (Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0")
) -join ";"

$Evidence = [ordered]@{
    schema_version = 1
    task = "5.5"
    generated_at_utc = [DateTime]::UtcNow.ToString("o")
    environment_kind = $EnvironmentKind
    clean_environment_claimed = $CleanEnvironment
    task_gate = "fail"
    artifact = [ordered]@{
        name = $Manifest.artifacts.setup.name
        sha256 = $Manifest.artifacts.setup.sha256
        authenticode_status = (Get-AuthenticodeSignature $SetupPath).Status.ToString()
    }
    isolation = [ordered]@{
        external_python_on_path = $null
        install_outside_source_tree = $true
        local_app_data_isolated = $true
        process_temp_isolated = $true
        no_existing_registration = $true
    }
    checks = [ordered]@{}
    limitation = if ($CleanEnvironment) { $null } else { "DeveloperHost is diagnostic only; authoritative acceptance requires Windows Sandbox, a disposable VM, or a clean user profile." }
}

try {
    New-Item -ItemType Directory -Path $InstallDir, $IsolatedLocalAppData, $IsolatedTemp, $ReportsDir -Force | Out-Null
    $env:PATH = $RecipientPath
    $env:LOCALAPPDATA = $IsolatedLocalAppData
    $env:TEMP = $IsolatedTemp
    $env:TMP = $IsolatedTemp
    $env:QT_QPA_PLATFORM = "offscreen"
    $Evidence.isolation.external_python_on_path = $null -ne (Get-Command python.exe -ErrorAction SilentlyContinue)
    if ($Evidence.isolation.external_python_on_path) {
        throw "Python remains available on the machine PATH; clean recipient isolation is not satisfied."
    }

    $InstallArguments = @(
        "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER",
        ("/DIR=" + (Quote-ProcessArgument $InstallDir)),
        ("/LOG=" + (Quote-ProcessArgument $InstallLog))
    )
    if ($CleanEnvironment) {
        $InstallArguments += '/TASKS="startmenuicon,desktopicon"'
    } else {
        $InstallArguments += "/NOICONS"
    }
    Invoke-CheckedProcess $SetupPath $InstallArguments "Silent installation"
    $Installed = $true
    if (-not (Test-Path $Executable -PathType Leaf) -or -not (Test-Path $Uninstaller -PathType Leaf)) {
        throw "Installation did not create the expected executable and uninstaller."
    }
    $Evidence.checks.install = "pass"

    if ($CleanEnvironment) {
        $StartMenuShortcut = Join-Path ([Environment]::GetFolderPath("Programs")) "pyVideoTrans-DH.lnk"
        $DesktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "pyVideoTrans-DH.lnk"
        if (-not (Test-Path $StartMenuShortcut) -or -not (Test-Path $DesktopShortcut)) {
            throw "Requested Start Menu and desktop shortcuts were not both created."
        }
        $Evidence.checks.shortcuts = "pass"
    } else {
        $Evidence.checks.shortcuts = "not_run_on_developer_host"
    }

    $CoreOne = Invoke-FrozenProbe $Executable $SmokeScript (Join-Path $ReportsDir "core-1.json") @((Quote-ProcessArgument $CliScript))
    $CoreTwo = Invoke-FrozenProbe $Executable $SmokeScript (Join-Path $ReportsDir "core-2.json") @((Quote-ProcessArgument $CliScript))
    $Evidence.checks.first_launch = "pass"
    $Evidence.checks.second_launch = "pass"
    $Evidence.checks.system_readiness = $CoreTwo.checks.system_readiness

    $env:PYVIDEOTRANS_LANG = "vi"
    Invoke-FrozenProbe $Executable $UiSmokeScript (Join-Path $ReportsDir "ui-vi.json") | Out-Null
    $env:PYVIDEOTRANS_LANG = "en"
    Invoke-FrozenProbe $Executable $UiSmokeScript (Join-Path $ReportsDir "ui-en.json") | Out-Null
    $env:PYVIDEOTRANS_LANG = $OldPyVideoTransLang
    $Evidence.checks.ui_vi = "pass"
    $Evidence.checks.ui_en = "pass"

    $SnapshotBefore = Get-InstallSnapshot $InstallDir
    $Identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    & icacls.exe $InstallDir /deny "${Identity}:(OI)(CI)(WD,AD,DC,DE)" /Q | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Failed to apply the read-only install-tree ACL." }
    $AclDenied = $true
    $WriteProbe = Join-Path $InstallDir "recipient-write-probe.tmp"
    try {
        Set-Content -Path $WriteProbe -Value "must-not-write" -ErrorAction Stop
        throw "The install tree remained writable after applying the read-only ACL."
    } catch [System.UnauthorizedAccessException] {
        # Expected: execution remains allowed while content mutation is denied.
    }
    Invoke-FrozenProbe $Executable $SmokeScript (Join-Path $ReportsDir "read-only.json") @((Quote-ProcessArgument $CliScript)) | Out-Null
    $Evidence.checks.read_only_install_tree = "pass"
    & icacls.exe $InstallDir /remove:d $Identity /Q | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Failed to restore the install-tree ACL." }
    $AclDenied = $false

    $SentinelDir = Join-Path $IsolatedLocalAppData "pyVideoTrans"
    $SentinelPath = Join-Path $SentinelDir "recipient-sentinel.txt"
    New-Item -ItemType Directory -Path $SentinelDir -Force | Out-Null
    Set-Content -Path $SentinelPath -Value "preserve-user-data" -Encoding UTF8

    $UpgradeArguments = @(
        "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER", "/NOICONS",
        ("/DIR=" + (Quote-ProcessArgument $InstallDir)),
        ("/LOG=" + (Quote-ProcessArgument $UpgradeLog))
    )
    Invoke-CheckedProcess $SetupPath $UpgradeArguments "In-place upgrade"
    $SnapshotAfter = Get-InstallSnapshot $InstallDir
    if (-not (Test-SnapshotEqual $SnapshotBefore $SnapshotAfter)) {
        throw "The installed payload changed unexpectedly after reinstalling the same release."
    }
    if (-not (Test-Path $SentinelPath)) { throw "Upgrade removed isolated user data." }
    Invoke-FrozenProbe $Executable $SmokeScript (Join-Path $ReportsDir "post-upgrade.json") @((Quote-ProcessArgument $CliScript)) | Out-Null
    $Evidence.checks.in_place_upgrade = "pass"
    $Evidence.checks.user_data_after_upgrade = "pass"

    Invoke-CheckedProcess $Uninstaller @(
        "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
        ("/LOG=" + (Quote-ProcessArgument $UninstallLog))
    ) "Silent uninstall"
    $Uninstalled = $true
    for ($Attempt = 0; $Attempt -lt 60 -and (Test-Path $Executable); $Attempt++) {
        Start-Sleep -Milliseconds 500
    }
    if (Test-Path $Executable) { throw "Uninstall left the application executable behind." }
    if (-not (Test-Path $SentinelPath)) { throw "Uninstall removed isolated user data." }
    $Evidence.checks.uninstall = "pass"
    $Evidence.checks.user_data_after_uninstall = "pass"
    $Evidence.task_gate = if ($CleanEnvironment) { "pass" } else { "partial" }
} catch {
    $SafeError = $_.Exception.Message.Replace($ProjectRoot, "<project>").Replace($WorkRoot, "<work-root>")
    $Evidence.error = $SafeError
    throw
} finally {
    if ($AclDenied -and (Test-Path $InstallDir)) {
        $Identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        & icacls.exe $InstallDir /remove:d $Identity /Q 2>$null | Out-Null
    }
    if ($Installed -and -not $Uninstalled -and (Test-Path $Uninstaller -PathType Leaf)) {
        try {
            Invoke-CheckedProcess $Uninstaller @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART") "Failure cleanup uninstall"
        } catch {
            $Evidence.cleanup_warning = "Automatic failure cleanup could not complete."
        }
    }
    $env:PATH = $OldPath
    $env:LOCALAPPDATA = $OldLocalAppData
    $env:QT_QPA_PLATFORM = $OldQt
    $env:PYVIDEOTRANS_LANG = $OldPyVideoTransLang
    $env:TEMP = $OldTemp
    $env:TMP = $OldTmp
    New-Item -ItemType Directory -Path (Split-Path $EvidencePath -Parent) -Force | Out-Null
    $Evidence | ConvertTo-Json -Depth 20 | Set-Content -Path $EvidencePath -Encoding UTF8
    if (-not $KeepWorkRoot -and (Test-Path $WorkRoot)) {
        Remove-Item -LiteralPath $WorkRoot -Recurse -Force
    }
}

Write-Host "Installed distribution smoke: $($Evidence.task_gate)"
Write-Host "Evidence: $EvidencePath"
