param(
    [ValidateSet("Lite", "AI")] [string]$Edition = "Lite",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$extras = if ($Edition -eq "AI") { ".[vision,semantic,geometry]" } else { ".[geometry]" }
$packageName = "AtlasSplitter-$Edition"
$packageRoot = Join-Path $root "dist/$packageName"
$archive = Join-Path $root "dist/$packageName.zip"

Push-Location $root
try {
    & $Python -m pip install -e $extras pyinstaller
    $arguments = @("--noconfirm", "--clean", "--onedir", "--name", $packageName, "--collect-all", "pygltflib")
    if ($Edition -eq "Lite") {
        $arguments += @("--exclude-module", "torch", "--exclude-module", "transformers", "--exclude-module", "sam2")
    }
    $arguments += "src/atlas_splitter/__main__.py"
    & $Python -m PyInstaller @arguments

    $executable = Join-Path $packageRoot "$packageName.exe"
    foreach ($check in @(@("--help"), @("doctor"), @("inspect", "--help"))) {
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

    $addonDirectory = Join-Path $root "dist/blender-addon"
    New-Item -ItemType Directory -Path $addonDirectory -Force | Out-Null
    $addonArchive = Join-Path $addonDirectory "atlas_splitter_blender.zip"
    Remove-Item $addonArchive -Force -ErrorAction SilentlyContinue
    Compress-Archive -Path (Join-Path $root "blender_addon") -DestinationPath $addonArchive -Force
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
