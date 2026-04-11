#!/usr/bin/env bash
# Load production environment variables into the current shell.
#
# Usage (from repo root):
#   source scripts/load_env.sh
#
# Then run Django management commands as normal:
#   cd sup_backend && python manage.py migrate

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.prod.env"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: $ENV_FILE not found." >&2
    exit 1
fi

# Export every non-comment, non-blank line
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip blank lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    export "$line"
done < "$ENV_FILE"

echo "Loaded env from $ENV_FILE"
