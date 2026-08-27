#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cleanup() { kill "${API_PID:-}" "${WEB_PID:-}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
(cd "$ROOT_DIR/backend" && uv run uvicorn app.main:app --reload) & API_PID=$!
(cd "$ROOT_DIR/frontend" && npm run dev -- --host 127.0.0.1) & WEB_PID=$!
wait "$API_PID"
wait "$WEB_PID"
