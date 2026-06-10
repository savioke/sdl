#!/usr/bin/env bash
# Per-repo SDL setup. Run once per project repo to opt it into SDL governance.
#
# Adds (all committed):
#   .github/workflows/sdl.yml         calls reusable workflow from savioke/sdl
#   docs/sdl/.gitkeep                  signals SDL is active for this repo
#   docs/sdl/baseline.md              repo security baseline stub; fill via sdl-baseline

set -euo pipefail

INSTALL_DIR="${SDL_INSTALL_DIR:-$HOME/.sdl-governance}"
SDL_REF="${SDL_REF:-v1}"

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

[[ $# -eq 1 ]] || die "Usage: $(basename "$0") <path-to-repo>"
repo="$1"
[[ -d "$repo/.git" ]] || die "$repo is not a git repository."
[[ -d "$INSTALL_DIR" ]] || die "SDL not installed at $INSTALL_DIR. Run install.sh first."

repo="$(cd "$repo" && pwd)"
log "Configuring SDL in $repo"

# 1. Reusable CI workflow.
mkdir -p "$repo/.github/workflows"
workflow="$repo/.github/workflows/sdl.yml"
if [[ -e "$workflow" ]]; then
  warn "$workflow already exists. Leaving as-is."
else
  cat > "$workflow" <<EOF
name: sdl
on: [pull_request, push]
jobs:
  validate:
    uses: savioke/sdl/.github/workflows/sdl-validate.yml@${SDL_REF}
EOF
  log "Wrote $workflow"
fi

# 2. docs/sdl signal.
mkdir -p "$repo/docs/sdl"
keep="$repo/docs/sdl/.gitkeep"
[[ -e "$keep" ]] || { touch "$keep"; log "Created $keep"; }

# 3. Baseline stub.
baseline="$repo/docs/sdl/baseline.md"
if [[ -e "$baseline" ]]; then
  warn "$baseline already exists. Leaving as-is."
else
  cp "$INSTALL_DIR/templates/baseline.md" "$baseline"
  log "Wrote $baseline (stub — fill it with the sdl-baseline skill)"
fi

cat <<EOF

Done. Commit the new files:

  cd $repo
  git add .github/workflows/sdl.yml docs/sdl/.gitkeep docs/sdl/baseline.md
  git commit -m "sdl: opt in to org SDL governance"

Then, once, ask your agent to run the sdl-baseline skill ("initialize the SDL
baseline") to record this repo's standing security posture. Per-feature cycles
reference the baseline and stay small.

EOF
