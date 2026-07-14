param([ValidateSet("Lite", "AI")] [string]$Edition = "Lite")

$ErrorActionPreference = "Stop"
$extras = if ($Edition -eq "AI") { ".[vision,semantic,geometry]" } else { ".[geometry]" }
python -m pip install -e $extras pyinstaller
$arguments = @("--noconfirm", "--clean", "--onedir", "--name", "AtlasSplitter-$Edition", "--collect-all", "pygltflib")
if ($Edition -eq "Lite") { $arguments += @("--exclude-module", "torch", "--exclude-module", "transformers", "--exclude-module", "sam2") }
$arguments += "src/atlas_splitter/cli.py"
pyinstaller @arguments
Write-Host "Build listo en dist/AtlasSplitter-$Edition. Lite no incluye PyTorch, modelos ni CUDA."
