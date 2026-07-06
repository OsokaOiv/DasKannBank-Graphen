param(
    [string]$Target = "x86_64-pc-windows-msvc",
    [switch]$Msi,
    [switch]$Nsis
)

$ErrorActionPreference = "Stop"

# Find repo root by walking up until Makefile is found
$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } elseif ($PSCommandPath) { Split-Path -Parent $PSCommandPath } else { Get-Location }
$RepoRoot = $ScriptDir
while ($RepoRoot -and -not (Test-Path "$RepoRoot\Makefile")) {
    $RepoRoot = Split-Path -Parent $RepoRoot
}
if (-not $RepoRoot -or -not (Test-Path "$RepoRoot\Makefile")) {
    throw "Could not find repo root (Makefile not found)"
}

Write-Host "=== DasKannBank-Graphen Windows Build ===" -ForegroundColor Cyan
Write-Host "Target : $Target"
Write-Host "Repo   : $RepoRoot"
Write-Host ""

# ---- helpers ----
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

function Ensure-Tool($Name, $Command, $WingetId, $StandaloneUrl, $StandaloneArgs) {
    if (Get-Command $Command -ErrorAction SilentlyContinue) {
        Write-Host "[*] $Name found" -ForegroundColor Green
        return $true
    }
    Write-Host "[!] $Name not found — installing..." -ForegroundColor Yellow
    $admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if ($admin -and $WingetId) {
        winget install --id $WingetId --silent --accept-package-agreements
    } elseif ($StandaloneUrl) {
        $ext = if ($StandaloneUrl -match '\.msi$') { "msi" } else { "exe" }
        $tmp = "$env:TEMP\$([System.IO.Path]::GetRandomFileName()).$ext"
        Write-Host "  -> Downloading from $StandaloneUrl ..." -ForegroundColor DarkYellow
        Invoke-WebRequest -Uri $StandaloneUrl -OutFile $tmp -UseBasicParsing
        if ($ext -eq "msi") {
            Start-Process -Wait msiexec.exe -ArgumentList "/i `"$tmp`" /quiet /norestart"
        } else {
            Start-Process -Wait -FilePath $tmp -ArgumentList $StandaloneArgs
        }
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host "  -> Cannot install $Name automatically (needs admin)." -ForegroundColor Red
        return $false
    }
    Refresh-Path
    Write-Host "  -> $Name installed." -ForegroundColor Green
    return $true
}

# ---- 1. Visual Studio Build Tools — detect and load environment ----
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vsPath = $null
if (Test-Path $vswhere) {
    $vsPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Workload.NativeDesktop -property installationPath
}
if (-not $vsPath) {
    # fallback: search common locations
    $candidates = @(
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\*\BuildTools",
        "${env:ProgramFiles}\Microsoft Visual Studio\*\BuildTools"
    )
    $vsPath = Get-ChildItem $candidates -ErrorAction SilentlyContinue |
        Sort-Object { [regex]::Replace($_.Name, '\d+', { $args[0].Value.PadLeft(10) }) } -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}

if ($vsPath) {
    $vcvars = Get-ChildItem "$vsPath\VC\Auxiliary\Build\vcvars64.bat" -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
    if (-not $vcvars) {
        $vcvars = Get-ChildItem "$vsPath\VC\Auxiliary\Build\vcvars*.bat" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match 'vcvars(64|amd64)' } |
            Select-Object -First 1 -ExpandProperty FullName
    }
    if ($vcvars -and (Test-Path $vcvars)) {
        Write-Host "[1/5] Loading MSVC environment from $vcvars" -ForegroundColor Green
        cmd /c "`"$vcvars`" && set" | ForEach-Object {
            if ($_ -match '^(\w+)=(.*)') {
                Set-Item -Path "env:$($Matches[1])" -Value $Matches[2]
            }
        }
        $cl = if (Get-Command cl.exe -ErrorAction SilentlyContinue) { "found" } else { "NOT in PATH" }
        Write-Host "  -> cl.exe $cl" -ForegroundColor DarkGray
    } else {
        Write-Host "[!] vcvars*.bat not found under $vsPath" -ForegroundColor Yellow
    }
} else {
    Write-Host "[!] Visual Studio Build Tools not found." -ForegroundColor Yellow
    Write-Host "    -> Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor DarkYellow
    Write-Host "       Select 'Desktop development with C++' workload." -ForegroundColor DarkYellow
}

# ---- 2. Rust ----
$null = Ensure-Tool "Rust" "rustup" "Rustlang.Rustup" "https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe" "-y --default-host $Target --default-toolchain stable"

cmd /c "rustup target add $Target >nul 2>&1"
$current = rustup default
if ($current -notlike "*msvc*") {
    cmd /c "rustup default stable-msvc >nul 2>&1"
    Write-Host "  -> Default toolchain set to stable-msvc" -ForegroundColor DarkGray
} else {
    Write-Host "  -> Toolchain: $current" -ForegroundColor DarkGray
}
Write-Host "  -> $(rustc --version)" -ForegroundColor DarkGray

# ---- 3. Node.js ----
$null = Ensure-Tool "Node.js" "node" "OpenJS.NodeJS" "https://nodejs.org/dist/v22.14.0/node-v22.14.0-x64.msi" $null
Write-Host "  -> $(node --version), npm $(cmd /c "npm --version 2>&1")" -ForegroundColor DarkGray

# ---- 4. npm install ----
Write-Host "[4/5] Installing npm dependencies..." -ForegroundColor Yellow
Set-Location "$RepoRoot\desktop"
& "npm.cmd" install
if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
Write-Host "  -> npm install done." -ForegroundColor Green

# ---- 5. generate icons (if missing) ----
$iconIco = "$RepoRoot\desktop\src-tauri\icons\icon.ico"
$iconPng = "$RepoRoot\desktop\src-tauri\icons\icon.png"
if (-not (Test-Path $iconIco) -and (Test-Path $iconPng)) {
    Write-Host "[5/5] Generating icon.ico from icon.png..." -ForegroundColor Yellow
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python -c "from PIL import Image; Image.open('$iconPng').save('$iconIco', format='ICO', sizes=[(32,32),(256,256)])"
    } elseif (Get-Command magick -ErrorAction SilentlyContinue) {
        magick convert "$iconPng" -define icon:auto-resize=256,32 "$iconIco"
    }
}

# ---- 6. tauri build ----
Write-Host "[6/6] Building Tauri app..." -ForegroundColor Yellow
$bundleArgs = @()
if ($Msi) { $bundleArgs += "--bundles"; $bundleArgs += "msi" }
if ($Nsis) { $bundleArgs += "--bundles"; $bundleArgs += "nsis" }
if (-not $Msi -and -not $Nsis) { $bundleArgs += "--bundles"; $bundleArgs += "nsis" }

& "npm.cmd" run tauri build -- --target $Target @bundleArgs
if ($LASTEXITCODE -ne 0) { throw "tauri build failed" }

Write-Host ""
Write-Host "=== Build complete! ===" -ForegroundColor Cyan
Write-Host "Output: $RepoRoot\desktop\src-tauri\target\$Target\release\bundle\" -ForegroundColor Cyan
