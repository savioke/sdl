#!/usr/bin/env bash
# One-shot dev setup for SDL governance.
# Clones (or updates) the canonical repo, registers the Relay plugin marketplace
# and installs the sdl plugin in Claude Code and Codex when available, and
# symlinks skills into Copilot's skills dir. No global git hook config — hooks
# are opt-in per repo via sync-to-repo.sh.

set -euo pipefail

REPO_URL="${SDL_REPO_URL:-git@github.com:savioke/sdl.git}"
INSTALL_DIR="${SDL_INSTALL_DIR:-$HOME/.sdl-governance}"
MARKETPLACE_URL="${RELAY_MARKETPLACE_URL:-https://github.com/savioke/relay-plugin-marketplace.git}"

CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
COPILOT_SKILLS_DIR="$HOME/.copilot/skills"
LINK_NAME="sdl"

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

# 1. Clone or update the repo.
if [[ -d "$INSTALL_DIR/.git" ]]; then
  log "Updating existing install at $INSTALL_DIR"
  git -C "$INSTALL_DIR" pull --ff-only
else
  log "Cloning $REPO_URL to $INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

# 2. Remove legacy Claude skills symlink if a prior install created one.
#    Skills are now delivered through the Claude Code plugin marketplace below.
legacy="$CLAUDE_SKILLS_DIR/$LINK_NAME"
if [[ -L "$legacy" && "$(readlink "$legacy")" == "$INSTALL_DIR/skills" ]]; then
  log "Removing legacy Claude skills symlink: $legacy"
  rm "$legacy"
fi

# 3. Symlink skills into Copilot's skills dir. Copilot has no marketplace path.
SKILLS_DIR="$INSTALL_DIR/plugins/sdl/skills"
mkdir -p "$COPILOT_SKILLS_DIR"
target="$COPILOT_SKILLS_DIR/$LINK_NAME"
if [[ -L "$target" ]]; then
  log "Refreshing Copilot symlink: $target"
  ln -sfn "$SKILLS_DIR" "$target"
elif [[ -e "$target" ]]; then
  warn "$target exists and is not a symlink. Skipping. Move it aside and re-run."
else
  log "Linking Copilot skills: $target -> $SKILLS_DIR"
  ln -s "$SKILLS_DIR" "$target"
fi

# 4. Register the Relay plugin marketplace and install the plugin.
#    The marketplace fetches the plugin from GitHub itself; the local clone is
#    only needed for Copilot skills and the scripts.
if command -v claude >/dev/null 2>&1; then
  log "Registering Relay plugin marketplace"
  claude plugin marketplace add "$MARKETPLACE_URL" || \
    warn "Marketplace registration failed (may already be registered)."
  log "Installing sdl plugin"
  claude plugin install sdl@relay || \
    warn "Plugin install failed; run 'claude plugin install sdl@relay' manually."
else
  warn "claude CLI not found. Skipping plugin install. Install Claude Code and re-run."
fi

if command -v codex >/dev/null 2>&1; then
  log "Registering Relay plugin marketplace in Codex"
  codex plugin marketplace add "$MARKETPLACE_URL" || \
    warn "Codex marketplace registration failed (may already be registered)."
  log "Installing sdl plugin in Codex"
  codex plugin add sdl@relay || \
    warn "Codex plugin install failed; run 'codex plugin add sdl@relay' manually."
else
  warn "codex CLI not found. Skipping Codex plugin install. Install Codex and re-run."
fi

cat <<EOF

Done.

  Install dir:      $INSTALL_DIR
  Claude plugin:    sdl@relay (managed via 'claude plugin')
  Codex plugin:     sdl@relay (managed via 'codex plugin')
  Copilot skills:   $COPILOT_SKILLS_DIR/$LINK_NAME

To update later:
  cd $INSTALL_DIR && git pull
  # Copilot picks up the new skills immediately (they are symlinked).
  # Claude Code fetches the plugin from GitHub independently of this clone:
  #   /plugin marketplace update relay   (then reload when prompted)
  # Codex does the same:
  #   codex plugin marketplace upgrade relay   (then start a new session)

To enable SDL on a project repo:
  $INSTALL_DIR/scripts/sync-to-repo.sh /path/to/repo

To browse a repo's SDL docs as HTML (localhost only):
  python3 $INSTALL_DIR/scripts/sdl-serve.py /path/to/repo

EOF
