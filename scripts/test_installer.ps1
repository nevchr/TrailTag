[CmdletBinding()]
param(
    [string]$InstallerPath
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $InstallerPath) {
    $versionSource = Get-Content -LiteralPath (Join-Path $projectRoot "src\geotagger\version.py") -Raw
    if ($versionSource -notmatch '__version__ = "(\d+\.\d+\.\d+)"') {
        throw "TrailTag's version could not be read."
    }
    $appVersion = $Matches[1]
    $InstallerPath = Join-Path $projectRoot "dist\TrailTag-Setup-$appVersion-x64.msi"
}
$InstallerPath = (Resolve-Path -LiteralPath $InstallerPath).Path
$qaRoot = Join-Path $projectRoot ("build\installer-qa-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $qaRoot | Out-Null

$windowsInstaller = New-Object -ComObject WindowsInstaller.Installer
$database = $windowsInstaller.OpenDatabase($InstallerPath, 0)
function Read-MsiProperty([string]$Name) {
    $view = $database.OpenView("SELECT Value FROM Property WHERE Property = '$Name'")
    $null = $view.Execute()
    $record = $view.Fetch()
    $value = $record.StringData(1)
    $null = $view.Close()
    return $value
}
$productCode = Read-MsiProperty "ProductCode"
if ($productCode -isnot [string] -or $productCode -notmatch '^\{[0-9A-Fa-f-]{36}\}$') {
    throw "The installer product identifier could not be read safely. No installation was attempted."
}
$existingInstallations = Get-ItemProperty `
    'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*', `
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*', `
    'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' `
    -ErrorAction SilentlyContinue | Where-Object DisplayName -eq 'TrailTag'
if ($existingInstallations) {
    throw "TrailTag is already installed. This test will not replace or uninstall an existing installation."
}
foreach ($candidateDirectory in @(
    (Join-Path $env:LOCALAPPDATA "Programs\TrailTag"),
    (Join-Path $env:ProgramFiles "TrailTag")
)) {
    if (Test-Path -LiteralPath $candidateDirectory) {
        throw "An existing app folder was found at $candidateDirectory. The test will not replace it."
    }
}

$tripPath = Join-Path $env:LOCALAPPDATA "TrailTag\trips.json"
$originalTripHash = if (Test-Path -LiteralPath $tripPath) {
    (Get-FileHash -LiteralPath $tripPath -Algorithm SHA256).Hash
} else { $null }
$shortcutPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\TrailTag.lnk"
if (Test-Path -LiteralPath $shortcutPath) {
    throw "An existing TrailTag shortcut was found. The installer test will not replace it."
}

function Invoke-Msi([string[]]$MsiArguments, [string]$LogName) {
    $logPath = Join-Path $qaRoot $LogName
    $allArguments = $MsiArguments + @('/qn', '/norestart', '/l*v', ('"' + $logPath + '"'))
    $process = Start-Process -FilePath "$env:WINDIR\System32\msiexec.exe" `
        -ArgumentList $allArguments -WindowStyle Hidden -PassThru
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $lastReport = 0
    while (-not $process.WaitForExit(1000)) {
        if ($timer.Elapsed.TotalSeconds - $lastReport -ge 30) {
            Write-Host "Windows Installer is still working ($LogName, $([int]$timer.Elapsed.TotalSeconds) seconds)."
            $lastReport = $timer.Elapsed.TotalSeconds
        }
    }
    $process.Refresh()
    if ($process.ExitCode -notin @(0, 3010)) {
        throw "Windows Installer returned $($process.ExitCode). See $logPath"
    }
}

$installationAttempted = $false
try {
    $installationAttempted = $true
    Invoke-Msi @('/i', ('"' + $InstallerPath + '"')) "install.log"
    if ($windowsInstaller.ProductState($productCode) -ne 5) {
        throw "Windows did not register the installed TrailTag product."
    }
    if (-not (Test-Path -LiteralPath $shortcutPath)) {
        throw "The installer did not create the Start menu shortcut."
    }

    # Query the advertised shortcut through Windows Installer to locate the
    # actual default install directory, rather than assuming Program Files.
    $componentView = $database.OpenView("SELECT ComponentId FROM Component WHERE Component = 'MainExecutable'")
    $componentView.Execute()
    $componentId = $componentView.Fetch().StringData(1)
    $componentView.Close()
    $installedExecutable = $windowsInstaller.ComponentPath($productCode, $componentId)
    if (-not (Test-Path -LiteralPath $installedExecutable)) {
        throw "The installed TrailTag executable was not found."
    }
    Write-Host "Installed to: $installedExecutable"
    $installedDirectory = Split-Path -Parent $installedExecutable
    $fileView = $database.OpenView('SELECT File FROM File')
    $fileView.Execute()
    $expectedFileCount = 0
    while ($fileView.Fetch()) { $expectedFileCount++ }
    $fileView.Close()
    $actualFileCount = (Get-ChildItem -LiteralPath $installedDirectory -Recurse -File | Measure-Object).Count
    if ($actualFileCount -ne $expectedFileCount) {
        throw "Expected $expectedFileCount installed files, but found $actualFileCount."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $installedDirectory "Third-party notices\README.txt"))) {
        throw "Third-party software notices were not installed."
    }
    Write-Host "Verified all $actualFileCount installed files."

    $smokePath = Join-Path $qaRoot "installed-smoke.txt"
    $smokeProcess = Start-Process -FilePath $installedExecutable `
        -ArgumentList ('"--smoke-test-status=' + $smokePath + '"') `
        -WindowStyle Hidden -PassThru
    if (-not $smokeProcess.WaitForExit(30000)) {
        Stop-Process -Id $smokeProcess.Id -Force
        throw "The installed app did not finish its startup test."
    }
    $smokeProcess.Refresh()
    if ($smokeProcess.ExitCode -ne 0 -or (Get-Content -LiteralPath $smokePath -Raw) -ne "passed") {
        throw "The installed TrailTag app failed its startup test."
    }

    Invoke-Msi @('/fa', $productCode) "repair.log"
    Write-Host "Install, installed-app startup, and repair passed."
}
finally {
    if ($installationAttempted -and $windowsInstaller.ProductState($productCode) -eq 5) {
        Invoke-Msi @('/x', $productCode) "uninstall.log"
    }
}

if ($windowsInstaller.ProductState($productCode) -eq 5) {
    throw "The test installation was not removed."
}
if (Test-Path -LiteralPath $shortcutPath) {
    throw "The test Start menu shortcut was not removed."
}
if ($installedExecutable -and (Test-Path -LiteralPath $installedExecutable)) {
    throw "The test executable was not removed."
}
$finalTripHash = if (Test-Path -LiteralPath $tripPath) {
    (Get-FileHash -LiteralPath $tripPath -Algorithm SHA256).Hash
} else { $null }
if ($originalTripHash -ne $finalTripHash) {
    throw "The saved-trip file changed during the installer test."
}
Write-Host "Uninstall passed. Saved trips were unchanged."
Write-Host "Verification logs: $qaRoot"
