#!/usr/bin/env bash
# Per-repo SDL setup. Run once per project repo to opt it into SDL governance.
# Ships inside the sdl plugin; resolves the baseline template relative to
# itself, so it works from the Claude plugin cache, a ~/.sdl-governance clone,
# or any other checkout. Agents invoke it as:
#   bash "$CLAUDE_PLUGIN_ROOT/lib/sync_to_repo.sh" <path-to-repo>
#
# Adds (all committed):
#   .github/workflows/sdl.yml          calls reusable workflow from savioke/sdl
#   docs/sdl/.gitkeep                  signals SDL is active for this repo
#   docs/sdl/baseline.md               repo security baseline stub; fill via sdl-baseline

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDL_REF="${SDL_REF:-v1}"
# Interpolated into generated YAML; restrict to git-ref characters so a
# crafted value can't inject workflow content.
[[ "$SDL_REF" =~ ^[A-Za-z0-9._/-]+$ ]] || { echo "xx invalid SDL_REF: $SDL_REF" >&2; exit 1; }

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

[[ $# -eq 1 ]] || die "Usage: $(basename "$0") <path-to-repo>"
repo="$1"
[[ -d "$repo/.git" ]] || die "$repo is not a git repository."
template="$PLUGIN_ROOT/templates/baseline.md"
[[ -f "$template" ]] || die "Baseline template not found at $template. Broken plugin install?"

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
on:
  pull_request:
  # The pull_request run is the gate. The push run exists to catch code that
  # reached the branch without one — a direct push — and skips anything that
  # arrived through a merged PR. Branch-filtered deliberately: an unfiltered
  # push also fires on tag pushes, where there is nothing to validate.
  # Change 'main' if this repo's default branch is named differently.
  push:
    branches: [main]
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
  cp "$template" "$baseline"
  log "Wrote $baseline (stub — fill it with the sdl-baseline skill)"
fi

cat <<EOF

Done. Before committing, ask your agent to run the sdl-baseline skill
("initialize the SDL baseline") to record this repo's standing security posture.
Per-feature cycles reference the baseline and stay small.

Then commit the scaffold and the filled baseline together:

  cd $repo
  git add .github/workflows/sdl.yml docs/sdl/.gitkeep docs/sdl/baseline.md
  git commit -m "sdl: opt in to org SDL governance"

The gate recognizes that adoption PR and needs no cycle for it — but only if the
baseline has real content. Pushing the stub on its own fails the gate.

EOF
