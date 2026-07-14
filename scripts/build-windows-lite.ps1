param(
    [ValidateSet("Lite", "AI")] [string]$Edition = "Lite",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$root = Split-Path -Parent $PSScriptRoot
$extras = if ($Edition -eq "AI") { ".[vision,semantic,geometry]" } else { ".[geometry]" }
$packageName = "AtlasSplitter-$Edition"
$packageRoot = Join-Path $root "dist/$packageName"
$archive = Join-Path $root "dist/$packageName.zip"

Push-Location $root
try {
    & $Python -m pip install -e $extras pyinstaller
    $arguments = @("--noconfirm", "--clean", "--onedir", "--name", $packageName, "--collect-all", "pygltflib", "--add-data", "blender_addon;atlas_splitter/resources/blender_addon")
    if ($Edition -eq "Lite") {
        $arguments += @("--exclude-module", "torch", "--exclude-module", "transformers", "--exclude-module", "sam2")
    }
    $arguments += "src/atlas_splitter/__main__.py"
    & $Python -m PyInstaller @arguments

    $executable = Join-Path $packageRoot "$packageName.exe"
    foreach ($check in @(@("--version"), @("--help"), @("doctor", "--format", "json"), @("inspect", "--help"), @("blender-addon", "info"))) {
        & $executable @check
        if ($LASTEXITCODE -ne 0) { throw "La comprobación '$($check -join ' ')' falló con código $LASTEXITCODE." }
    }

    Copy-Item LICENSE (Join-Path $packageRoot "LICENSE") -Force
    Set-Content (Join-Path $packageRoot "VERSION.txt") ((& $Python -c "from atlas_splitter import __version__; print(__version__)")) -Encoding utf8
    @(
        "Atlas Splitter para Windows",
        "",
        "1. Extrae este ZIP en una carpeta local.",
        "2. Ejecuta AtlasSplitter-$Edition.exe desde PowerShell o haciendo doble clic.",
        "3. Escribe doctor para comprobar el equipo.",
        "4. Usa split atlas.webp --output resultados para separar un atlas.",
        "5. Usa setup geometry --yes antes de comandos GLB si hace falta."
    ) | Set-Content (Join-Path $packageRoot "README-WINDOWS.txt") -Encoding utf8

    $addonSmoke = Join-Path $root "addon-smoke"
    Remove-Item $addonSmoke -Recurse -Force -ErrorAction SilentlyContinue
    & $executable blender-addon export --output $addonSmoke
    if ($LASTEXITCODE -ne 0) { throw "La exportación del add-on falló con código $LASTEXITCODE." }
    $addonArchive = Join-Path $addonSmoke "atlas_splitter_blender.zip"
    if (-not (Test-Path -LiteralPath $addonArchive -PathType Leaf)) { throw "No se generó $addonArchive." }
    $requiredAddonFiles = @("__init__.py", "operators.py", "panels.py", "properties.py", "manifest.py")
    $archiveEntries = [IO.Compression.ZipFile]::OpenRead($addonArchive)
    try {
        $entryNames = @($archiveEntries.Entries | ForEach-Object { [IO.Path]::GetFileName($_.FullName) })
        foreach ($required in $requiredAddonFiles) {
            if ($entryNames -notcontains $required) { throw "El add-on exportado no contiene $required." }
        }
    }
    finally {
        $archiveEntries.Dispose()
    }
    Copy-Item $addonArchive (Join-Path $packageRoot "atlas_splitter_blender.zip") -Force

    Remove-Item $archive -Force -ErrorAction SilentlyContinue
    Compress-Archive -Path $packageRoot -DestinationPath $archive -Force
    Get-FileHash $archive -Algorithm SHA256 | ForEach-Object { "$($_.Hash.ToLower())  $([IO.Path]::GetFileName($archive))" } |
        Set-Content (Join-Path $root "dist/SHA256SUMS.txt") -Encoding ascii
}
finally {
    Pop-Location
}

Write-Host "Build listo en dist/$packageName y dist/$packageName.zip. Lite no incluye modelos ni CUDA."
