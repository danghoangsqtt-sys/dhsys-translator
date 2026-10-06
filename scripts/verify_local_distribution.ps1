[CmdletBinding()]
param(
    [string]$ManifestPath = "",
    [string]$InnoCompiler = "",
    [switch]$AllowMissingInstaller,
    [switch]$SkipPortableSmoke
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$PinnedInnoVersion = "6.7.3"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$ManifestTool = Join-Path $PSScriptRoot "distribution_manifest.py"

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
if (-not $ManifestPath) {
    $VersionText = Get-Content (Join-Path $ProjectRoot "pyproject.toml") -Raw
    $Version = [regex]::Match($VersionText, '(?m)^version\s*=\s*"([0-9]+(?:\.[0-9]+){1,3})"').Groups[1].Value
    $ManifestPath = Join-Path $ProjectRoot "release\local\pyVideoTrans-DH-$Version-win64-manifest.json"
}
$ManifestPath = (Resolve-Path $ManifestPath).Path
$ReleaseDir = Split-Path $ManifestPath -Parent

if (-not (Test-Path $Python -PathType Leaf)) {
    throw "Python 3.12 build environment is missing at $Python."
}

if (-not $AllowMissingInstaller) {
    if (-not $InnoCompiler) {
        $CompilerCandidates = @(
            (Join-Path ${env:LOCALAPPDATA} "Programs\Inno Setup 6\ISCC.exe"),
            "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            "C:\Program Files\Inno Setup 6\ISCC.exe"
        )
        $InnoCompiler = $CompilerCandidates | Where-Object { Test-Path $_ -PathType Leaf } | Select-Object -First 1
    }
    if (-not $InnoCompiler -or -not (Test-Path $InnoCompiler -PathType Leaf)) {
        throw "Installer verification requires Inno Setup $PinnedInnoVersion. Compiler not found; install JRSoftware.InnoSetup $PinnedInnoVersion or pass -InnoCompiler."
    }
    $CompilerVersion = Get-RegisteredInnoVersion $InnoCompiler
    if ($CompilerVersion -ne $PinnedInnoVersion) {
        $Reported = if ($CompilerVersion) { $CompilerVersion } else { "unverified" }
        throw "Inno Setup compiler version mismatch: found $Reported, required registered version $PinnedInnoVersion."
    }
}

$VerifyArgs = @($ManifestTool, "verify-release", "--manifest", $ManifestPath, "--release-dir", $ReleaseDir)
if ($AllowMissingInstaller) { $VerifyArgs += "--allow-missing-installer" }
& $Python @VerifyArgs
if ($LASTEXITCODE -ne 0) { throw "Manifest/checksum/archive verification failed." }

if (-not $SkipPortableSmoke) {
    $Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
    $PortableName = $Manifest.artifacts.portable.name
    $PortablePath = Join-Path $ReleaseDir $PortableName
    $SmokeRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("pyvideotrans-portable-smoke-" + [guid]::NewGuid().ToString("N"))
    $ExtractRoot = Join-Path $SmokeRoot "extract"
    $IsolatedData = Join-Path $SmokeRoot "localappdata"
    New-Item -ItemType Directory -Path $ExtractRoot, $IsolatedData -Force | Out-Null
    try {
        tar.exe -xf $PortablePath -C $ExtractRoot
        if ($LASTEXITCODE -ne 0) { throw "Portable ZIP extraction failed." }
        $ExtractedCandidate = Join-Path $ExtractRoot $Manifest.candidate.root_name
        & $Python $ManifestTool verify-tree --manifest $ManifestPath --candidate $ExtractedCandidate
        if ($LASTEXITCODE -ne 0) { throw "Extracted portable tree does not match the manifest." }

        $SmokeScript = Join-Path $ProjectRoot "scripts\smoke_frozen.py"
        $CliScript = Join-Path $ProjectRoot "cli.py"
        $ReportPath = Join-Path $SmokeRoot "portable-smoke.json"
        $OldPath = $env:PATH
        $OldLocalAppData = $env:LOCALAPPDATA
        $OldQt = $env:QT_QPA_PLATFORM
        try {
            $SystemOnlyPath = @(
                "$env:SystemRoot\System32",
                "$env:SystemRoot",
                "$env:SystemRoot\System32\Wbem",
                "$env:SystemRoot\System32\WindowsPowerShell\v1.0"
            ) -join ";"
            $env:PATH = $SystemOnlyPath
            $env:LOCALAPPDATA = $IsolatedData
            $env:QT_QPA_PLATFORM = "offscreen"
            $Executable = Join-Path $ExtractedCandidate "sp.exe"
            $Process = Start-Process -FilePath $Executable -ArgumentList @($SmokeScript, $ReportPath, $CliScript) -WorkingDirectory $SmokeRoot -WindowStyle Hidden -Wait -PassThru
            if ($Process.ExitCode -ne 0) { throw "Frozen portable smoke failed. See $ReportPath" }
            $SmokeResult = Get-Content $ReportPath -Raw | ConvertFrom-Json
            if ($SmokeResult.status -ne "pass") { throw "Frozen portable smoke report is not PASS: $ReportPath" }
        } finally {
            $env:PATH = $OldPath
            $env:LOCALAPPDATA = $OldLocalAppData
            $env:QT_QPA_PLATFORM = $OldQt
        }
    } finally {
        if (Test-Path $SmokeRoot) { Remove-Item $SmokeRoot -Recurse -Force }
    }
}

Write-Host "Distribution verification PASS: $ManifestPath"
