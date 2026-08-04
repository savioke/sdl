#!/usr/bin/env bash
# Per-repo SDL setup for clone-based installs. Thin delegate: the real logic
# ships inside the plugin so Claude Code marketplace users get it too.
set -euo pipefail
exec bash "$(dirname "${BASH_SOURCE[0]}")/../plugins/sdl/lib/sync_to_repo.sh" "$@"
