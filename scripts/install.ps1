param(
    [ValidateSet("basic", "geometry", "semantic", "all")]
    [string]$Features = "basic",
    [string]$Environment = ".atlas-splitter-venv"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root $Environment
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
    python -m venv $venv
}

& $python -m pip install --upgrade pip
$extras = switch ($Features) {
    "geometry" { ".[geometry]" }
    "semantic" { ".[semantic]" }
    "all" { ".[vision,semantic,geometry]" }
    default { "." }
}
& $python -m pip install -e $extras
& $python -m atlas_splitter doctor

Write-Host "Entorno listo en $venv. No se descargó ningún modelo."
