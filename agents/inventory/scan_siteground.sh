#!/usr/bin/env bash
set -euo pipefail

# Read-only inventory of SiteGround public_html (FREEZE-safe: no writes).
# Requires ssh client and access configured on the operator machine.

: "${SITEGROUND_USER:?Set SITEGROUND_USER (e.g. u123456789)}"
: "${SITEGROUND_HOST:?Set SITEGROUND_HOST (e.g. sftp.siteground.net)}"
: "${SITEGROUND_PORT:?Set SITEGROUND_PORT (e.g. 18765)}"

ssh -p "${SITEGROUND_PORT}" "${SITEGROUND_USER}@${SITEGROUND_HOST}" << 'EOF'
cd ~/public_html
find . -maxdepth 5 -type f \
  \( -name "*.html" -o -name "*.js" -o -name "*.json" -o -name "*.wasm" -o -name "*.txt" \) \
  | sort
EOF
