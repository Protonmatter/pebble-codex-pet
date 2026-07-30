#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="$PROJECT_ROOT/pebble-poses"
TARGET_DIR="${CODEX_HOME:-$HOME/.codex}/pets/pebble-poses"

usage() {
  cat <<USAGE
Usage: $(basename "$0") [--source DIR] [--target DIR]

Installs Pebble Poses after validating the source atlas.

Options:
  --source DIR  Pet folder containing pet.json and spritesheet.webp.
  --target DIR  Destination folder. Defaults to
                \${CODEX_HOME:-\$HOME/.codex}/pets/pebble-poses.
  -h, --help    Show this help text.
USAGE
}

while (($#)); do
  case "$1" in
    --source)
      [[ $# -ge 2 ]] || { echo "--source requires a directory" >&2; exit 2; }
      SOURCE_DIR="$2"
      shift 2
      ;;
    --target)
      [[ $# -ge 2 ]] || { echo "--target requires a directory" >&2; exit 2; }
      TARGET_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

python3 "$SCRIPT_DIR/verify_pebble_pose_pet.py" "$SOURCE_DIR"

SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd -P)"
TARGET_PARENT="$(dirname -- "$TARGET_DIR")"
TARGET_NAME="$(basename -- "$TARGET_DIR")"
mkdir -p -- "$TARGET_PARENT"
TARGET_PARENT="$(cd "$TARGET_PARENT" && pwd -P)"
TARGET_DIR="$TARGET_PARENT/$TARGET_NAME"
if [[ "$SOURCE_DIR" == "$TARGET_DIR" ]]; then
  echo "Source and target must be different directories: $SOURCE_DIR" >&2
  exit 2
fi

STAGING_DIR="$(mktemp -d "$TARGET_PARENT/.pebble-poses.install.XXXXXX")"
cleanup() {
  rm -rf -- "$STAGING_DIR"
}
trap cleanup EXIT

install -m 0644 "$SOURCE_DIR/pet.json" "$STAGING_DIR/pet.json"
install -m 0644 "$SOURCE_DIR/spritesheet.webp" "$STAGING_DIR/spritesheet.webp"

BACKUP_DIR=""
if [[ -e "$TARGET_DIR" ]]; then
  BACKUP_BASE="${TARGET_DIR}.backup.$(date -u +%Y%m%dT%H%M%SZ)"
  BACKUP_DIR="$BACKUP_BASE"
  BACKUP_INDEX=0
  while [[ -e "$BACKUP_DIR" ]]; do
    BACKUP_INDEX=$((BACKUP_INDEX + 1))
    BACKUP_DIR="${BACKUP_BASE}.${BACKUP_INDEX}"
  done
  mv -- "$TARGET_DIR" "$BACKUP_DIR"
fi

if ! mv -- "$STAGING_DIR" "$TARGET_DIR"; then
  [[ -n "$BACKUP_DIR" && -e "$BACKUP_DIR" ]] && mv -- "$BACKUP_DIR" "$TARGET_DIR"
  exit 1
fi
trap - EXIT

printf 'Installed Pebble Poses to %s\n' "$TARGET_DIR"
if [[ -n "$BACKUP_DIR" ]]; then
  printf 'Previous installation backed up to %s\n' "$BACKUP_DIR"
fi
