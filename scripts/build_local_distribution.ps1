[CmdletBinding()]
param(
    [string]$CandidateDir = "",
    [string]$OutputDir = "",
    [string]$InnoCompiler = "",
    [switch]$SkipInstaller,
    [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$PinnedInnoVersion = "6.7.3"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$ManifestTool = Join-Path $PSScriptRoot "distribution_manifest.py"
$InstallerScript = Join-Path $ProjectRoot "installer\pyvideotrans.iss"

function Get-RegisteredInnoVersion([string]$CompilerPath) {
    $ResolvedCompiler = (Resolve-Path $CompilerPath).Path
    $Roots = @(
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall",
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall",
        "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    )
    foreach ($Root in $Roots) {
        if (-not (Test-Path $Root)) { continue }
        foreach ($Key in Get-ChildItem $Root -ErrorAction SilentlyContinue) {
            $Entry = Get-ItemProperty $Key.PSPath -ErrorAction SilentlyContinue
            if (-not $Entry) { continue }
            $DisplayNameProperty = $Entry.PSObject.Properties["DisplayName"]
            $VersionProperty = $Entry.PSObject.Properties["DisplayVersion"]
            $LocationProperty = $Entry.PSObject.Properties["InstallLocation"]
            if (-not $DisplayNameProperty -or -not $VersionProperty -or -not $LocationProperty) { continue }
            if ($Entry.DisplayName -notlike "Inno Setup*") { continue }
            if (-not $Entry.InstallLocation) { continue }
            $InstallRoot = [System.IO.Path]::GetFullPath($Entry.InstallLocation).TrimEnd("\")
            if ($ResolvedCompiler.StartsWith($InstallRoot + "\", [System.StringComparison]::OrdinalIgnoreCase)) {
                return [string]$Entry.DisplayVersion
            }
        }
    }
    return ""
}

if (-not $CandidateDir) { $CandidateDir = Join-Path $ProjectRoot "dist\sp" }
if (-not $OutputDir) { $OutputDir = Join-Path $ProjectRoot "release\local" }
$CandidateDir = (Resolve-Path $CandidateDir).Path
$OutputDir = [System.IO.Path]::GetFullPath($OutputDir)

if (-not (Test-Path (Join-Path $CandidateDir "sp.exe") -PathType Leaf)) {
    throw "Frozen candidate is invalid: missing $CandidateDir\sp.exe"
}
if (-not (Test-Path (Join-Path $ProjectRoot "LICENSE") -PathType Leaf)) {
    throw "Project LICENSE is required for redistribution."
}
if (-not (Test-Path $Python -PathType Leaf)) {
    throw "Python 3.12 build environment is missing at $Python. Run the project dependency setup first."
}
$PythonVersion = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0 -or $PythonVersion.Trim() -ne "3.12") {
    throw "Task 5.4 requires the project Python 3.12 environment; found $PythonVersion."
}
$Tar = (Get-Command tar.exe -ErrorAction SilentlyContinue).Source
if (-not $Tar) {
    throw "Windows tar.exe is required to create the ZIP64 portable archive."
}

$PyProject = Get-Content (Join-Path $ProjectRoot "pyproject.toml") -Raw
$VersionMatch = [regex]::Match($PyProject, '(?m)^version\s*=\s*"([0-9]+(?:\.[0-9]+){1,3})"')
if (-not $VersionMatch.Success) {
    throw "Unable to read the product version from pyproject.toml."
}
$Version = $VersionMatch.Groups[1].Value
$Prefix = "pyVideoTrans-DH-$Version-win64"
$PortableName = "$Prefix-portable.zip"
$SetupName = "$Prefix-setup.exe"
$ManifestName = "$Prefix-manifest.json"

if (-not $SkipInstaller) {
    if (-not $InnoCompiler) {
        $CompilerCandidates = @(
            (Join-Path ${env:LOCALAPPDATA} "Programs\Inno Setup 6\ISCC.exe"),
            "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            "C:\Program Files\Inno Setup 6\ISCC.exe"
        )
        $InnoCompiler = $CompilerCandidates | Where-Object { Test-Path $_ -PathType Leaf } | Select-Object -First 1
    }
    if (-not $InnoCompiler -or -not (Test-Path $InnoCompiler -PathType Leaf)) {
        throw "Inno Setup $PinnedInnoVersion compiler is required. Install exact package JRSoftware.InnoSetup version $PinnedInnoVersion with WinGet, or pass -InnoCompiler to that exact ISCC.exe. No PATH change is required."
    }
    $CompilerVersion = Get-RegisteredInnoVersion $InnoCompiler
    if ($CompilerVersion -ne $PinnedInnoVersion) {
        $Reported = if ($CompilerVersion) { $CompilerVersion } else { "unverified" }
        throw "Inno Setup compiler version mismatch: found $Reported, required registered version $PinnedInnoVersion."
    }
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$PortablePath = Join-Path $OutputDir $PortableName
$SetupPath = Join-Path $OutputDir $SetupName
$ManifestPath = Join-Path $OutputDir $ManifestName

foreach ($GeneratedPath in @(
    $PortablePath,
    "$PortablePath.sha256",
    $SetupPath,
    "$SetupPath.sha256",
    $ManifestPath,
    "$ManifestPath.sha256"
)) {
    if (Test-Path $GeneratedPath) { Remove-Item $GeneratedPath -Force }
}

Write-Host "[1/5] Inventory and safety scan: $CandidateDir"
& $Python $ManifestTool inventory --candidate $CandidateDir --manifest $ManifestPath --version $Version --build-root $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "Candidate inventory/safety scan failed." }

Write-Host "[2/5] Creating portable ZIP64 archive with Windows tar.exe"
$CandidateParent = Split-Path $CandidateDir -Parent
$CandidateLeaf = Split-Path $CandidateDir -Leaf
& $Tar -a -c -f $PortablePath -C $CandidateParent $CandidateLeaf
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $PortablePath -PathType Leaf)) {
    throw "Portable ZIP creation failed."
}
& $Python $ManifestTool record-artifact --manifest $ManifestPath --kind portable --path $PortablePath
if ($LASTEXITCODE -ne 0) { throw "Unable to record portable artifact metadata." }

if (-not $SkipInstaller) {
    Write-Host "[3/5] Building per-user Setup.exe with pinned Inno Setup $PinnedInnoVersion"
    $SetupBase = [System.IO.Path]::GetFileNameWithoutExtension($SetupName)
    $LicensePath = Join-Path $ProjectRoot "LICENSE"
    & $InnoCompiler "/DSourceDir=$CandidateDir" "/DOutputDir=$OutputDir" "/DAppVersion=$Version" "/DSetupBaseFilename=$SetupBase" "/DLicensePath=$LicensePath" $InstallerScript
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $SetupPath -PathType Leaf)) {
        throw "Inno Setup compilation failed or did not create $SetupName."
    }
    & $Python $ManifestTool record-artifact --manifest $ManifestPath --kind setup --path $SetupPath
    if ($LASTEXITCODE -ne 0) { throw "Unable to record Setup.exe artifact metadata." }
} else {
    Write-Warning "Developer-only -SkipInstaller used. This output does not satisfy the Task 5.4 shipping gate."
}

Write-Host "[4/5] Writing SHA-256 sidecars"
& $Python $ManifestTool sidecar --path $PortablePath
if ($LASTEXITCODE -ne 0) { throw "Unable to write portable SHA-256 sidecar." }
if (-not $SkipInstaller) {
    & $Python $ManifestTool sidecar --path $SetupPath
    if ($LASTEXITCODE -ne 0) { throw "Unable to write Setup.exe SHA-256 sidecar." }
}
& $Python $ManifestTool sidecar --path $ManifestPath
if ($LASTEXITCODE -ne 0) { throw "Unable to write manifest SHA-256 sidecar." }

$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$GiB = [math]::Round($Manifest.candidate.total_bytes / 1GB, 2)
Write-Host "Candidate: $($Manifest.candidate.file_count) files, $GiB GiB"
Write-Host "Largest components:"
$Manifest.candidate.largest_files | Select-Object -First 10 | ForEach-Object {
    Write-Host ("  {0,8:N2} MiB  {1}" -f ($_.size / 1MB), $_.path)
}

if (-not $SkipVerify) {
    Write-Host "[5/5] Verifying generated distribution"
    $VerifyScript = Join-Path $PSScriptRoot "verify_local_distribution.ps1"
    $VerifyArgs = @{
        ManifestPath = $ManifestPath
        InnoCompiler = $InnoCompiler
    }
    if ($SkipInstaller) { $VerifyArgs.AllowMissingInstaller = $true }
    & $VerifyScript @VerifyArgs
    if ($LASTEXITCODE -ne 0) { throw "Distribution verification failed." }
} else {
    Write-Warning "Verification was skipped; this output is not shipping evidence."
}

Write-Host "Local distribution output: $OutputDir"
