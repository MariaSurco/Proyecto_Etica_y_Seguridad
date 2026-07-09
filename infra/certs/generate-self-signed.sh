#!/usr/bin/env sh
set -eu

DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

openssl req -x509 -nodes -newkey rsa:4096 -days 365 \
  -keyout "$DIR/localhost.key" \
  -out "$DIR/localhost.crt" \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$DIR/localhost.key"
chmod 644 "$DIR/localhost.crt"
