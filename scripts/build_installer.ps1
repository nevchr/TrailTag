[CmdletBinding()]
param(
    [switch]$SkipAppBuild,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$buildRoot = Join-Path $projectRoot "build"
$versionSource = Get-Content -LiteralPath (Join-Path $projectRoot "src\geotagger\version.py") -Raw
if ($versionSource -notmatch '__version__ = "(\d+\.\d+\.\d+)"') {
    throw "TrailTag's release version could not be read."
}
$appVersion = $Matches[1]
$portableArchive = Join-Path $projectRoot "dist\TrailTag-windows-x64.zip"
$installerPath = Join-Path $projectRoot "dist\TrailTag-Setup-$appVersion-x64.msi"
$installerHashPath = "$installerPath.sha256"
$installerSource = Join-Path $projectRoot "packaging\TrailTag.wxs"
$installerUiSource = Join-Path $projectRoot "packaging\TrailTagUI.wxs"
$windowsBuildScript = Join-Path $PSScriptRoot "build_windows.ps1"
$wixVersion = "5.0.2"
$wixPackageHash = "F30EF0C74E2A986126539C5780BE93AC24E8136EAF723B1937B26272703AE173"
$wixPackagePath = Join-Path $buildRoot "wix.$wixVersion.nupkg"
$wixToolRoot = Join-Path $buildRoot "wix-$wixVersion"
$wixUiPackagePath = Join-Path $buildRoot "wixtoolset.ui.wixext.$wixVersion.nupkg"
$wixUiPackageHash = "5EF2C707614B9F70B6BBADD2D4ABCB4124EFEE215E9B16BFBC80113079A604C7"
$wixUiRoot = Join-Path $buildRoot "wix-ui-$wixVersion"
$wixUiExtension = Join-Path $wixUiRoot "wixext5\WixToolset.UI.wixext.dll"
$installerStageRoot = Join-Path `
    $buildRoot `
    ("installer-staging-" + [guid]::NewGuid().ToString("N"))
$intermediatePath = Join-Path $installerStageRoot "intermediate"

function Confirm-BuildChildPath([string]$Path) {
    $resolvedPath = [System.IO.Path]::GetFullPath($Path)
    $resolvedBuildRoot = (
        [System.IO.Path]::GetFullPath($buildRoot)
    ).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    $expectedPrefix = $resolvedBuildRoot + (
        [System.IO.Path]::DirectorySeparatorChar
    )

    if (-not $resolvedPath.StartsWith(
        $expectedPrefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Refusing to change an unexpected folder outside build."
    }
}

Push-Location $projectRoot

try {
    New-Item -ItemType Directory -Force $buildRoot | Out-Null

    if (-not $SkipAppBuild) {
        if ($SkipTests) {
            & $windowsBuildScript -SkipTests
        }
        else {
            & $windowsBuildScript
        }

        if ($LASTEXITCODE -ne 0) {
            throw "The portable TrailTag app could not be built."
        }
    }

    if (-not (Test-Path -LiteralPath $portableArchive)) {
        throw "Build the portable TrailTag ZIP before creating the installer."
    }

    if (-not (Test-Path -LiteralPath $wixPackagePath)) {
        Invoke-WebRequest `
            -Uri "https://api.nuget.org/v3-flatcontainer/wix/$wixVersion/wix.$wixVersion.nupkg" `
            -OutFile $wixPackagePath
    }

    $actualWixHash = (
        Get-FileHash -LiteralPath $wixPackagePath -Algorithm SHA256
    ).Hash
    if ($actualWixHash -ne $wixPackageHash) {
        throw "The downloaded WiX build tool did not match its pinned checksum."
    }

    $wixExecutable = Get-ChildItem `
        -LiteralPath $wixToolRoot `
        -Filter "wix.exe" `
        -Recurse `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName

    if (-not $wixExecutable) {
        New-Item -ItemType Directory -Force $wixToolRoot | Out-Null
        & tar.exe -xf $wixPackagePath -C $wixToolRoot
        if ($LASTEXITCODE -ne 0) {
            throw "The WiX build tool could not be unpacked."
        }

        $wixExecutable = Get-ChildItem `
            -LiteralPath $wixToolRoot `
            -Filter "wix.exe" `
            -Recurse |
            Select-Object -First 1 -ExpandProperty FullName
    }

    if (-not (Test-Path -LiteralPath $wixUiPackagePath)) {
        Invoke-WebRequest `
            -Uri "https://api.nuget.org/v3-flatcontainer/wixtoolset.ui.wixext/$wixVersion/wixtoolset.ui.wixext.$wixVersion.nupkg" `
            -OutFile $wixUiPackagePath
    }
    if ((Get-FileHash -LiteralPath $wixUiPackagePath -Algorithm SHA256).Hash -ne $wixUiPackageHash) {
        throw "The WiX setup-dialog library did not match its pinned checksum."
    }
    if (-not (Test-Path -LiteralPath $wixUiExtension)) {
        New-Item -ItemType Directory -Force $wixUiRoot | Out-Null
        & tar.exe -xf $wixUiPackagePath -C $wixUiRoot
        if ($LASTEXITCODE -ne 0) {
            throw "The WiX setup-dialog library could not be unpacked."
        }
    }

    New-Item -ItemType Directory -Force $installerStageRoot | Out-Null
    Expand-Archive `
        -LiteralPath $portableArchive `
        -DestinationPath $installerStageRoot

    $payloadPath = Join-Path $installerStageRoot "TrailTag"
    $payloadExecutable = Join-Path $payloadPath "TrailTag.exe"
    if (-not (Test-Path -LiteralPath $payloadExecutable)) {
        throw "The portable app did not contain TrailTag.exe."
    }

    if (Test-Path -LiteralPath $installerPath) {
        Remove-Item -LiteralPath $installerPath -Force
    }

    & $wixExecutable build `
        -arch x64 `
        -d "SourceDir=$payloadPath" `
        -d "AppVersion=$appVersion" `
        -ext $wixUiExtension `
        -pdbtype none `
        -intermediatefolder $intermediatePath `
        -o $installerPath `
        $installerSource `
        $installerUiSource

    if ($LASTEXITCODE -ne 0) {
        throw "WiX could not create the TrailTag installer."
    }

    $installerHash = (
        Get-FileHash -LiteralPath $installerPath -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    Set-Content `
        -LiteralPath $installerHashPath `
        -Value "$installerHash  $(Split-Path -Leaf $installerPath)" `
        -Encoding ascii

    Write-Host ""
    Write-Host "TrailTag installer created:"
    Write-Host $installerPath
}
finally {
    if (Test-Path -LiteralPath $installerStageRoot) {
        Confirm-BuildChildPath $installerStageRoot
        Remove-Item `
            -LiteralPath $installerStageRoot `
            -Recurse `
            -Force
    }

    Pop-Location
}
