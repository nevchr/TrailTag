[CmdletBinding()]
param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$specPath = Join-Path $projectRoot "TrailTag.spec"
$iconScriptPath = Join-Path $projectRoot "scripts\create_app_icon.py"
$buildRoot = Join-Path $projectRoot "build"
$packageStageRoot = Join-Path `
    $buildRoot `
    ("package-staging-" + [guid]::NewGuid().ToString("N"))
$pytestTempPath = Join-Path `
    $buildRoot `
    ("pytest-" + [guid]::NewGuid().ToString("N"))
$distributionPath = Join-Path $packageStageRoot "TrailTag"
$executablePath = Join-Path $distributionPath "TrailTag.exe"
$smokeStatusPath = Join-Path $packageStageRoot "TrailTag-smoke-test.txt"
$archivePath = Join-Path $projectRoot "dist\TrailTag-windows-x64.zip"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "TrailTag's virtual environment is missing. Create .venv first."
}

Push-Location $projectRoot

try {
    & $pythonPath $iconScriptPath

    if ($LASTEXITCODE -ne 0) {
        throw "TrailTag's application icon could not be created."
    }

    if (-not $SkipTests) {
        & $pythonPath -m pytest `
            -q `
            -p no:cacheprovider `
            --basetemp $pytestTempPath

        if ($LASTEXITCODE -ne 0) {
            throw "Tests failed. The Windows package was not built."
        }
    }

    & $pythonPath -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath $packageStageRoot `
        $specPath

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed to build TrailTag."
    }

    if (-not (Test-Path -LiteralPath $distributionPath)) {
        throw "The TrailTag distribution folder was not created."
    }

    & $pythonPath (Join-Path $PSScriptRoot "collect_notices.py") $distributionPath
    if ($LASTEXITCODE -ne 0) {
        throw "Third-party software notices could not be collected."
    }

    if (Test-Path -LiteralPath $smokeStatusPath) {
        Remove-Item -LiteralPath $smokeStatusPath -Force
    }

    $smokeProcess = Start-Process `
        -FilePath $executablePath `
        -ArgumentList ('"--smoke-test-status=' + $smokeStatusPath + '"') `
        -WindowStyle Hidden `
        -PassThru

    if (-not $smokeProcess.WaitForExit(30000)) {
        Stop-Process -Id $smokeProcess.Id -Force
        throw "The packaged TrailTag app did not finish its startup test."
    }

    $smokeProcess.Refresh()
    if ($smokeProcess.ExitCode -ne 0) {
        throw "The packaged TrailTag app failed its startup test."
    }

    $smokeStatus = if (Test-Path -LiteralPath $smokeStatusPath) {
        Get-Content -LiteralPath $smokeStatusPath -Raw
    }

    if ($smokeStatus -ne "passed") {
        throw "The packaged TrailTag window did not initialize correctly."
    }

    Remove-Item -LiteralPath $smokeStatusPath -Force

    if (Test-Path -LiteralPath $archivePath) {
        Remove-Item -LiteralPath $archivePath -Force
    }

    Compress-Archive `
        -Path $distributionPath `
        -DestinationPath $archivePath `
        -CompressionLevel Optimal

    $archiveHash = (
        Get-FileHash -LiteralPath $archivePath -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    Set-Content `
        -LiteralPath "$archivePath.sha256" `
        -Value "$archiveHash  $(Split-Path -Leaf $archivePath)" `
        -Encoding ascii

    Write-Host ""
    Write-Host "TrailTag package created:"
    Write-Host $archivePath
}
finally {
    if (Test-Path -LiteralPath $smokeStatusPath) {
        Remove-Item -LiteralPath $smokeStatusPath -Force
    }

    foreach ($temporaryPath in @($packageStageRoot, $pytestTempPath)) {
        if (-not (Test-Path -LiteralPath $temporaryPath)) {
            continue
        }

        $resolvedTemporaryPath = [System.IO.Path]::GetFullPath(
            $temporaryPath
        )
        $resolvedBuildRoot = (
            [System.IO.Path]::GetFullPath($buildRoot)
        ).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
        $expectedPrefix = $resolvedBuildRoot + (
            [System.IO.Path]::DirectorySeparatorChar
        )

        if (-not $resolvedTemporaryPath.StartsWith(
            $expectedPrefix,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            throw "Refusing to clean an unexpected temporary folder."
        }

        Remove-Item `
            -LiteralPath $resolvedTemporaryPath `
            -Recurse `
            -Force
    }

    Pop-Location
}
