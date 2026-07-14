param(
    [ValidateSet("", "basic", "geometry", "vision", "semantic", "all")]
    [string]$Features = "",
    [string]$Environment = ".atlas-splitter-venv"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root $Environment
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.11, 3.12 o 3.13 debe estar disponible como 'python'."
}
if ($Features -eq "") {
    Write-Host "Selecciona: 1) Básico 2) GLB/glTF y UV 3) Segmentación visual 4) Agrupación semántica 5) Todo"
    $choice = Read-Host "Opción"
    $Features = @{ "1" = "basic"; "2" = "geometry"; "3" = "vision"; "4" = "semantic"; "5" = "all" }[$choice]
    if (-not $Features) { throw "Opción no válida." }
}

if (-not (Test-Path $python)) {
    python -m venv $venv
}

& $python -m pip install --upgrade pip
$extras = switch ($Features) {
    "geometry" { ".[geometry]" }
    "vision" { ".[vision]" }
    "semantic" { ".[semantic]" }
    "all" { ".[vision,semantic,geometry]" }
    default { "." }
}
& $python -m pip install -e $extras
& $python -m atlas_splitter doctor

Write-Host "Entorno listo en $venv. No se descargó ningún modelo."
