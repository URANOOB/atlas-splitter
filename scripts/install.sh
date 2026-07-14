#!/usr/bin/env sh
set -eu

features="${1:-basic}"
environment="${ATLAS_SPLITTER_VENV:-.atlas-splitter-venv}"
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python="$root/$environment/bin/python"

if [ ! -x "$python" ]; then
  python3 -m venv "$root/$environment"
fi

"$python" -m pip install --upgrade pip
case "$features" in
  basic) extras="." ;;
  geometry) extras=".[geometry]" ;;
  semantic) extras=".[semantic]" ;;
  all) extras=".[vision,semantic,geometry]" ;;
  *) echo "Uso: $0 [basic|geometry|semantic|all]" >&2; exit 2 ;;
esac
"$python" -m pip install -e "$extras"
"$python" -m atlas_splitter doctor
printf '%s\n' "Entorno listo en $environment. No se descargó ningún modelo."
