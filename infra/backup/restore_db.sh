#!/usr/bin/env sh
set -eu

: "${DATABASE_URL:?DATABASE_URL es requerido}"
: "${BACKUP_ENCRYPTION_KEY:?BACKUP_ENCRYPTION_KEY es requerido}"

BACKUP_FILE="${1:?Uso: restore_db.sh archivo.sql.enc}"
TMP_SQL="$(mktemp)"

cleanup() {
  rm -f "$TMP_SQL"
}
trap cleanup EXIT

openssl enc -d -aes-256-cbc -pbkdf2 -pass "pass:$BACKUP_ENCRYPTION_KEY" -in "$BACKUP_FILE" -out "$TMP_SQL"
psql "$DATABASE_URL" < "$TMP_SQL"
