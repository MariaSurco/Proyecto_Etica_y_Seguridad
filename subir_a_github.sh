#!/usr/bin/env bash
set -e

echo "=== Estado actual del repo ==="
git status --short

echo ""
echo "=== Agregando cambios ==="
git add backend/pyproject.toml docs/INFORME_FINAL.tex

echo ""
echo "=== Creando commit ==="
git commit -m "feat: agregar dashboard de privacidad diferencial, notebook e informe final

- Notebook reproducible de privacidad diferencial (diffprivlib)
- Endpoints backend /api/dp/* y /api/demo/usuarios
- Dashboard React con playground de DP, trade-off y vista de usuarios
- Informe final en Markdown y LaTeX con DPIA y reflexion etica
- Fix de packaging en pyproject.toml (pip install -e ahora funciona)"

echo ""
echo "=== Subiendo a GitHub (origin/main) ==="
git push origin main

echo ""
echo "=== Listo. Estado final: ==="
git log --oneline -5
git status --short
