#!/usr/bin/env sh
set -eu

: "${DATABASE_URL:?DATABASE_URL es requerido}"
: "${BACKUP_ENCRYPTION_KEY:?BACKUP_ENCRYPTION_KEY es requerido}"

OUT_DIR="${BACKUP_DIR:-./backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"
PLAIN="$OUT_DIR/bank_campaigns_$STAMP.sql"
ENCRYPTED="$PLAIN.enc"

mkdir -p "$OUT_DIR"

cleanup() {
  rm -f "$PLAIN"
}
trap cleanup EXIT

pg_dump "$DATABASE_URL" > "$PLAIN"
openssl enc -aes-256-cbc -salt -pbkdf2 -pass "pass:$BACKUP_ENCRYPTION_KEY" -in "$PLAIN" -out "$ENCRYPTED"

printf '%s\n' "$ENCRYPTED"
