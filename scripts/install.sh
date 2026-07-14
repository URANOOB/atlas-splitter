#!/usr/bin/env sh
set -eu

features="${1:-}"
environment="${ATLAS_SPLITTER_VENV:-.atlas-splitter-venv}"
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python="$root/$environment/bin/python"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Se requiere Python 3.11, 3.12 o 3.13 como python3." >&2
  exit 1
fi
if [ -z "$features" ]; then
  printf '%s\n' "Selecciona: 1) Básico 2) GLB/glTF y UV 3) Segmentación visual 4) Agrupación semántica 5) Todo"
  printf '%s' "Opción: "
  read -r choice
  case "$choice" in
    1) features=basic ;; 2) features=geometry ;; 3) features=vision ;; 4) features=semantic ;; 5) features=all ;;
    *) echo "Opción no válida." >&2; exit 2 ;;
  esac
fi

if [ ! -x "$python" ]; then
  python3 -m venv "$root/$environment"
fi

"$python" -m pip install --upgrade pip
case "$features" in
  basic) extras="." ;;
  geometry) extras=".[geometry]" ;;
  vision) extras=".[vision]" ;;
  semantic) extras=".[semantic]" ;;
  all) extras=".[vision,semantic,geometry]" ;;
  *) echo "Uso: $0 [basic|geometry|vision|semantic|all]" >&2; exit 2 ;;
esac
"$python" -m pip install -e "$extras"
"$python" -m atlas_splitter doctor
printf '%s\n' "Entorno listo en $environment. No se descargó ningún modelo."
