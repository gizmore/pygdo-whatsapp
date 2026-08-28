#!/usr/bin/env bash
# Keep the WhatsApp Web bridge alive. Run this as gizmore so Chromium can use
# the saved LocalAuth profile.
set -u

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE_DIR="$APP_DIR/.wwebjs_auth/session"

cleanup_browser() {
    pkill -u "$(id -u)" -f -- "--user-data-dir=${PROFILE_DIR}" 2>/dev/null || true
}

trap 'cleanup_browser; exit 0' INT TERM
cd "$APP_DIR"

while true; do
    /usr/bin/node bin/dog.js
    status=$?
    printf 'WhatsApp bridge exited with status %s; restarting in 5 seconds.\n' "$status" >&2
    cleanup_browser
    sleep 5
done
