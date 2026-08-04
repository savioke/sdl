#!/usr/bin/env bash
# Release this repo. One command, no arguments, same every time.
#
# Reads the version from plugins/sdl/.claude-plugin/plugin.json (bumped in the
# change PR, not here), then:
#   1. verifies main is clean, pushed, and green
#   2. creates the immutable annotated tag vX.Y.Z (signed when a key is set up)
#   3. force-moves the vX alias that consumer CI pins
#   4. points the marketplace manifest at that exact tag
#
# Immutable tags are never rewritten: if vX.Y.Z already exists the release is
# refused. Only the alias moves. See docs/releasing.md.
#
# Escape hatches, for exceptional situations only — say why in the PR or commit:
#   SDL_RELEASE_SKIP_CI=1   release a commit whose checks are not green
#   SDL_RELEASE_YES=1       skip the confirmation prompt
#   SDL_MARKETPLACE_REPO    release to a different marketplace repo (testing)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKETPLACE_REPO="${SDL_MARKETPLACE_REPO:-savioke/relay-plugin-marketplace}"
PLUGIN_NAME="sdl"
PLUGIN_JSON="$REPO_ROOT/plugins/sdl/.claude-plugin/plugin.json"
CHANGELOG="$REPO_ROOT/CHANGELOG.md"
MANIFEST_PATH=".claude-plugin/marketplace.json"

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

tmpdir=""
cleanup() { [[ -n "$tmpdir" && -d "$tmpdir" ]] && rm -rf "$tmpdir"; }
trap cleanup EXIT

# --- 1. Preconditions -------------------------------------------------------

command -v git >/dev/null || die "git not found."
command -v gh  >/dev/null || die "gh not found. Install the GitHub CLI and 'gh auth login'."
command -v python3 >/dev/null || die "python3 not found."
gh auth status >/dev/null 2>&1 || die "gh is not authenticated. Run 'gh auth login'."

cd "$REPO_ROOT"
branch="$(git rev-parse --abbrev-ref HEAD)"
[[ "$branch" == "main" ]] || die "on branch '$branch'; releases are cut from main."
[[ -z "$(git status --porcelain)" ]] || die "working tree is dirty. Commit or stash first."

log "Fetching origin"
git fetch --quiet --tags origin
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || \
  die "main and origin/main differ. Pull/push first — a release must be reproducible from the remote."

# --- 2. Version, tag names, changelog --------------------------------------

version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("version",""))' "$PLUGIN_JSON")"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || \
  die "plugin.json version '$version' is not X.Y.Z. Fix it in a PR, not here."
tag="v$version"
alias_tag="v${version%%.*}"

[[ -f "$CHANGELOG" ]] || die "CHANGELOG.md is missing."
notes="$(python3 - "$CHANGELOG" "$version" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
start = re.search(rf"^##\s+v?{re.escape(sys.argv[2])}\b.*$", text, re.MULTILINE)
if not start:
    sys.exit(1)
rest = text[start.end():]
end = re.search(r"^##\s+", rest, re.MULTILINE)
print((rest[:end.start()] if end else rest).strip())
PY
)" || die "CHANGELOG.md has no '## $version' entry. Add one in a PR, not here."

if git rev-parse -q --verify "refs/tags/$tag" >/dev/null || \
   git ls-remote --exit-code --tags origin "refs/tags/$tag" >/dev/null 2>&1; then
  die "$tag already exists. Released versions are immutable — bump the version in a PR instead."
fi

# --- 3. CI must be green ----------------------------------------------------

sha="$(git rev-parse HEAD)"
slug="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
if [[ "${SDL_RELEASE_SKIP_CI:-}" == "1" ]]; then
  warn "SDL_RELEASE_SKIP_CI=1 — releasing a commit whose checks were not verified."
else
  log "Checking CI status for ${sha:0:9}"
  runs="$(gh api "repos/$slug/commits/$sha/check-runs" \
            -q '.check_runs[] | "\(.status):\(.conclusion // "pending"):\(.name)"' 2>/dev/null || true)"
  [[ -n "$runs" ]] || die "no checks found for ${sha:0:9}. Wait for CI, or set SDL_RELEASE_SKIP_CI=1."
  while IFS= read -r run; do
    [[ -n "$run" ]] || continue
    status="${run%%:*}"; rest="${run#*:}"; conclusion="${rest%%:*}"; name="${rest#*:}"
    [[ "$status" == "completed" ]] || die "check '$name' is still $status. Wait for CI to finish."
    case "$conclusion" in
      success|skipped|neutral) ;;
      *) die "check '$name' concluded '$conclusion'. Fix it, or set SDL_RELEASE_SKIP_CI=1." ;;
    esac
  done <<< "$runs"
  log "All checks green"
fi

# --- 4. Confirm -------------------------------------------------------------

cat <<EOF

Release $tag from ${sha:0:9} ($slug)

  create tag        $tag              (immutable, annotated)
  move alias        $alias_tag  -> ${sha:0:9}   (consumer CI pins this)
  marketplace       $MARKETPLACE_REPO
                    version -> $version, source.ref -> $tag

Changelog:
$(printf '%s\n' "$notes" | sed 's/^/  /')

EOF
if [[ "${SDL_RELEASE_YES:-}" != "1" ]]; then
  read -r -p "Proceed? [y/N] " reply
  [[ "$reply" == "y" || "$reply" == "Y" ]] || die "Aborted."
fi

# --- 5. Tag and push --------------------------------------------------------

if [[ -n "$(git config --get user.signingkey || true)" ]]; then
  sign_flag="-s"
else
  sign_flag="-a"
  warn "No user.signingkey configured — the tag will be annotated but unsigned."
  warn "Consumer CI executes this tag; set up tag signing (docs/releasing.md)."
fi

log "Creating $tag"
printf '%s\n\n%s\n' "$tag" "$notes" | git tag "$sign_flag" -F - "$tag"

# Immutable tag first: the alias must never point at something unpushed.
log "Pushing $tag"
git push --quiet origin "refs/tags/$tag"
log "Moving $alias_tag"
git tag -f "$sign_flag" -m "$alias_tag -> $tag" "$alias_tag" >/dev/null
git push --quiet --force origin "refs/tags/$alias_tag"

# --- 6. Marketplace manifest ------------------------------------------------

log "Updating $MARKETPLACE_REPO"
tmpdir="$(mktemp -d)"
gh repo clone "$MARKETPLACE_REPO" "$tmpdir" -- --quiet --depth 1
python3 - "$tmpdir/$MANIFEST_PATH" "$PLUGIN_NAME" "$version" "$tag" <<'PY'
import json, sys
path, plugin, version, tag = sys.argv[1:5]
with open(path, encoding="utf-8") as fh:
    manifest = json.load(fh)
for entry in manifest.get("plugins", []):
    if entry.get("name") == plugin:
        entry["version"] = version
        entry.setdefault("source", {})["ref"] = tag
        break
else:
    sys.exit(f"no plugin named {plugin!r} in {path}")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2)
    fh.write("\n")
PY

if [[ -z "$(git -C "$tmpdir" status --porcelain)" ]]; then
  log "Manifest already at $version / $tag — nothing to commit"
else
  git -C "$tmpdir" commit --quiet -am "$PLUGIN_NAME $version (source.ref $tag)"
  git -C "$tmpdir" push --quiet
  log "Manifest updated"
fi

# --- 7. Verify --------------------------------------------------------------

# Local-only: raw.githubusercontent caches the manifest for a few minutes, so
# the marketplace half is verified by this repo's CI on the next push.
python3 "$REPO_ROOT/scripts/check_release.py" --mode released --offline --repo "$REPO_ROOT"

cat <<EOF

Released $tag.

  Consumers on @$alias_tag pick it up on their next CI run.
  Claude Code developers: /plugin marketplace update relay, then reload.
  Copilot / clone-based developers: cd ~/.sdl-governance && git pull && scripts/install.sh

EOF
