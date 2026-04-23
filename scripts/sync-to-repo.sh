#!/usr/bin/env bash
# Per-repo SDL setup. Run once per project repo to opt it into SDL governance.
#
# Adds:
#   .github/workflows/sdl.yml         (committed: calls reusable workflow)
#   docs/sdl/.gitkeep                  (committed: signals SDL is active)
#   .git/hooks/pre-commit             (NOT committed: shim to canonical hook)
#   .git/hooks/prepare-commit-msg     (NOT committed: shim to canonical hook)

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

# 3. Opt-in git hook shims (not committed).
hooks_dir="$repo/.git/hooks"
for h in pre-commit prepare-commit-msg; do
  shim="$hooks_dir/$h"
  if [[ -e "$shim" && ! -L "$shim" ]]; then
    if grep -q "sdl-governance" "$shim" 2>/dev/null; then
      log "Shim already present: $shim"
      continue
    fi
    warn "$shim exists and is not an SDL shim. Skipping. Move it aside and re-run if desired."
    continue
  fi
  cat > "$shim" <<EOF
#!/usr/bin/env bash
# sdl-governance shim — runs the canonical hook from the central install.
exec "$INSTALL_DIR/hooks/$h" "\$@"
EOF
  chmod +x "$shim"
  log "Installed shim: $shim"
done

cat <<EOF

Done. Commit the new files:

  cd $repo
  git add .github/workflows/sdl.yml docs/sdl/.gitkeep
  git commit -m "sdl: opt in to org SDL governance"

Hook shims in .git/hooks/ are local-only (not committed). New clones of this
repo do not get hooks until their developer also runs sync-to-repo.sh.

EOF
