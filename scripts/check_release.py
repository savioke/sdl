#!/usr/bin/env python3
"""Detect release drift between this repo, its tags, and the marketplace manifest.

This repo ships executable content over two channels (docs/releasing.md):
consumer CI pins the reusable workflow at the moving `vX` alias, and the Claude
Code and Codex plugins are pinned by marketplace manifests at an immutable
`vX.Y.Z`. Drift between them is invisible until it breaks someone else's CI or
silently withholds a fix from developer machines, so CI checks for it.

Two modes:

    check_release.py --mode pr --base origin/main
        Ran on pull requests. If the diff touches shipped content, the version
        in both plugin manifests must be higher than the base branch's and must
        have a CHANGELOG entry. Enforces "the version bump happens in the
        change PR".

    check_release.py --mode released
        Ran on demand (workflow_dispatch, or locally) and by release.sh after it
        tags. The declared version must have an immutable tag, the `vX`
        alias must point at the same commit, no shipped content may have
        changed since that tag, and both marketplace manifests must pin exactly
        that tag (and the Claude catalog must name the version).

CI deliberately only *detects*; releasing is a maintainer-run script
(scripts/release.sh) so no CI credential can write to the distribution channel
(cycle 2026-08-03-release-process, T3).

Stdlib only. Exit 0 = consistent (warnings permitted), 1 = drift.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Content that reaches a consumer: the plugin package (marketplace channel) and
# the reusable workflow (CI channel). Everything else — this repo's own docs,
# self-check, release tooling — can change without a release.
SHIPPING_PATHS = ("plugins/sdl", ".github/workflows/sdl-validate.yml")

PLUGIN_JSON = "plugins/sdl/.claude-plugin/plugin.json"
CODEX_PLUGIN_JSON = "plugins/sdl/.codex-plugin/plugin.json"
PLUGIN_JSONS = (PLUGIN_JSON, CODEX_PLUGIN_JSON)
CHANGELOG = "CHANGELOG.md"

DEFAULT_MARKETPLACE_REPO = "savioke/relay-plugin-marketplace"
MARKETPLACE_MANIFESTS = (
    (".claude-plugin/marketplace.json", True),
    (".agents/plugins/marketplace.json", False),
)
EXPECTED_SOURCE_KIND = "git-subdir"
EXPECTED_SOURCE_URL = "https://github.com/savioke/sdl.git"
EXPECTED_SOURCE_PATHS = ("plugins/sdl", "./plugins/sdl")
MAX_MANIFEST_BYTES = 1_000_000

# Strict three-part semver. No prerelease or build metadata: the version is a
# git ref name and a plugin cache directory name, and both are happier without.
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_semver(version: str) -> tuple[int, int, int] | None:
    m = SEMVER_RE.match(version.strip())
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def version_from_plugin_json(text: str) -> str | None:
    try:
        v = json.loads(text).get("version")
    except (ValueError, AttributeError):
        return None
    return v if isinstance(v, str) else None


def changelog_has_entry(text: str, version: str) -> bool:
    """A release needs a heading of the form `## <version>` (any suffix, e.g.
    a date), so consumers reading a moved alias can find out what changed."""
    pattern = re.compile(rf"^##\s+v?{re.escape(version)}\b", re.MULTILINE)
    return bool(pattern.search(text))


def manifest_entry(manifest: object, plugin: str) -> dict | None:
    if not isinstance(manifest, dict):
        return None
    plugins = manifest.get("plugins")
    if not isinstance(plugins, list):
        return None
    for entry in plugins:
        if isinstance(entry, dict) and entry.get("name") == plugin:
            return entry
    return None


def check_manifest(manifest: object, plugin: str, version: str,
                   require_declared_version: bool = True) -> list[str]:
    """Errors describing how the fetched manifest disagrees with this version.

    The manifest comes from another repo over the network, so nothing about its
    shape is guaranteed. Type-check before every access: a manifest we cannot
    read is drift to report, not a traceback out of the drift check.
    """
    if not isinstance(manifest, dict) or not isinstance(manifest.get("plugins"), list):
        return ["marketplace manifest is not an object with a `plugins` array"]
    entry = manifest_entry(manifest, plugin)
    if entry is None:
        return [f"marketplace manifest has no plugin named {plugin!r}"]
    errors = []
    declared = entry.get("version")
    if ((require_declared_version and declared != version) or
            (not require_declared_version and declared is not None and
             declared != version)):
        errors.append(
            f"marketplace manifest declares {plugin} {declared!r}, repo says {version!r}")
    # `source` is an object in the git-subdir form this plugin uses, but the
    # marketplace schema also allows a bare URL string, so a non-object here is
    # a real shape we must report rather than assume away.
    source = entry.get("source")
    expected_ref = f"v{version}"
    if not isinstance(source, dict):
        errors.append(
            f"marketplace manifest gives {plugin} a non-object `source` "
            f"({type(source).__name__}); expected an object pinning ref {expected_ref!r} "
            f"(a release must be reachable at exactly one immutable tag)")
    else:
        expected_fields = (
            ("source", EXPECTED_SOURCE_KIND),
            ("url", EXPECTED_SOURCE_URL),
        )
        for field, expected_value in expected_fields:
            if source.get(field) != expected_value:
                errors.append(
                    f"marketplace manifest pins source.{field} "
                    f"{source.get(field)!r}, expected {expected_value!r}")
        if source.get("path") not in EXPECTED_SOURCE_PATHS:
            errors.append(
                f"marketplace manifest pins source.path {source.get('path')!r}, "
                f"expected the plugin subdirectory {EXPECTED_SOURCE_PATHS[0]!r}")
        if source.get("ref") != expected_ref:
            errors.append(
                f"marketplace manifest pins source.ref {source.get('ref')!r}, "
                f"expected {expected_ref!r} "
                f"(a release must be reachable at exactly one immutable tag)")
    return errors


def git(*args: str, repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def git_ok(*args: str, repo: Path) -> bool:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True).returncode == 0


def shipping_changes(repo: Path, since: str, until: str = "HEAD") -> list[str]:
    """Shipped files this branch changed. Three-dot (merge-base..until), the
    same range validate.py gates on: a two-dot tree comparison would report
    changes main made after the branch point as if this branch had made them."""
    out = git("diff", "--name-only", f"{since}...{until}", "--", *SHIPPING_PATHS, repo=repo)
    return [line for line in out.splitlines() if line.strip()]


def file_at_rev(repo: Path, rev: str, path: str) -> str | None:
    try:
        return git("show", f"{rev}:{path}", repo=repo)
    except subprocess.CalledProcessError:
        return None


def fetch_manifest(repo_slug: str, path: str = MARKETPLACE_MANIFESTS[0][0],
                   timeout: int = 30) -> tuple[object, str | None]:
    """Returns (manifest, error). A network failure is an availability problem,
    not evidence of drift — the caller warns rather than failing (SR-8).

    The manifest is whatever the responder served, so it is typed `object`, not
    `dict`: valid JSON is not necessarily an object. `check_manifest` is
    responsible for every type check past this point."""
    url = f"https://raw.githubusercontent.com/{repo_slug}/main/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "sdl-check-release"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            # Bounded read: the body is an externally-hosted document, and a
            # manifest is a few KB. Reading it unbounded would let whoever
            # serves it decide how much memory this CI runner spends.
            body = resp.read(MAX_MANIFEST_BYTES + 1)
            if len(body) > MAX_MANIFEST_BYTES:
                return None, f"manifest at {url} exceeds {MAX_MANIFEST_BYTES} bytes"
            return json.loads(body.decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code} fetching {url}"
    # ValueError covers both ways the body can be unreadable: UnicodeDecodeError
    # from the decode above and JSONDecodeError from the parse, each a subclass.
    # Both are format failures, reported like an outage rather than as drift.
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        return None, f"{e.__class__.__name__} fetching {url}"


def check_pr(repo: Path, base: str, plugin: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    head_text = (repo / PLUGIN_JSON).read_text(encoding="utf-8")
    head_version = version_from_plugin_json(head_text)
    head_parsed = parse_semver(head_version) if head_version is not None else None
    if head_parsed is None:
        return ([f"{PLUGIN_JSON}: version is missing or not X.Y.Z"], notes)

    codex_path = repo / CODEX_PLUGIN_JSON
    codex_version = version_from_plugin_json(
        codex_path.read_text(encoding="utf-8")) if codex_path.is_file() else None
    if codex_version != head_version:
        errors.append(
            f"plugin manifest versions disagree: {PLUGIN_JSON} has {head_version!r}, "
            f"{CODEX_PLUGIN_JSON} has {codex_version!r}")

    if not git_ok("rev-parse", "--verify", f"{base}^{{commit}}", repo=repo):
        return ([f"base ref {base!r} not found — fetch it (checkout with fetch-depth: 0)"],
                notes)

    changed = shipping_changes(repo, base)
    if not changed:
        notes.append(f"no shipped content changed vs {base}; no version bump required")
        return (errors, notes)

    base_text = file_at_rev(repo, base, PLUGIN_JSON)
    base_version = version_from_plugin_json(base_text) if base_text else None
    base_parsed = parse_semver(base_version) if base_version is not None else None
    notes.append(f"{len(changed)} shipped file(s) changed vs {base}")

    # Only the base side can be unusable here — the head version was parsed
    # above and the function returned if it failed. A base with no version, or
    # one we cannot order against (`1.0`, `1.0.0-rc1`, `v1.0.0`), is history the
    # PR author did not write and is not evidence of a missing bump: note it and
    # skip, exactly as for a base with no plugin.json at all. Crashing here
    # would fail the PR with a traceback in place of an actionable message.
    if base_parsed is None:
        notes.append(f"no comparable version at {base} ({base_version!r}); "
                     f"skipping increase check")
    elif head_parsed <= base_parsed:
        errors.append(
            f"shipped content changed but version did not increase "
            f"({base_version} -> {head_version}). Bump it in this PR and add a "
            f"CHANGELOG entry — see docs/releasing.md")

    changelog = repo / CHANGELOG
    if not changelog.is_file():
        errors.append(f"{CHANGELOG} is missing")
    elif not changelog_has_entry(changelog.read_text(encoding="utf-8"), head_version):
        errors.append(f"{CHANGELOG} has no `## {head_version}` entry")

    return (errors, notes)


def check_released(repo: Path, plugin: str, marketplace_repo: str,
                   offline: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    version = version_from_plugin_json((repo / PLUGIN_JSON).read_text(encoding="utf-8"))
    parsed = parse_semver(version) if version else None
    if parsed is None:
        return ([f"{PLUGIN_JSON}: version is missing or not X.Y.Z"], notes)
    codex_path = repo / CODEX_PLUGIN_JSON
    codex_version = version_from_plugin_json(
        codex_path.read_text(encoding="utf-8")) if codex_path.is_file() else None
    if codex_version != version:
        errors.append(
            f"plugin manifest versions disagree: {PLUGIN_JSON} has {version!r}, "
            f"{CODEX_PLUGIN_JSON} has {codex_version!r}")
    tag, alias = f"v{version}", f"v{parsed[0]}"

    changelog = repo / CHANGELOG
    if not changelog.is_file():
        errors.append(f"{CHANGELOG} is missing")
    elif not changelog_has_entry(changelog.read_text(encoding="utf-8"), version):
        errors.append(f"{CHANGELOG} has no `## {version}` entry")

    if not git_ok("rev-parse", "--verify", f"{tag}^{{commit}}", repo=repo):
        errors.append(
            f"no tag {tag} — main declares {version} but it was never released. "
            f"Run scripts/release.sh (see docs/releasing.md)")
        return (errors, notes)

    tag_commit = git("rev-parse", f"{tag}^{{commit}}", repo=repo)
    if not git_ok("merge-base", "--is-ancestor", tag_commit, "HEAD", repo=repo):
        errors.append(f"tag {tag} points at {tag_commit[:9]}, which is not an ancestor "
                      f"of HEAD — the tag was cut from another branch")
    else:
        stale = shipping_changes(repo, tag_commit)
        if stale:
            errors.append(
                f"{len(stale)} shipped file(s) changed since {tag} and are not released: "
                f"{', '.join(stale[:5])}{' …' if len(stale) > 5 else ''}")

    if not git_ok("rev-parse", "--verify", f"{alias}^{{commit}}", repo=repo):
        errors.append(f"no {alias} alias tag — consumer CI pins it and would not resolve")
    else:
        alias_commit = git("rev-parse", f"{alias}^{{commit}}", repo=repo)
        if alias_commit != tag_commit:
            errors.append(
                f"alias {alias} points at {alias_commit[:9]} but {tag} is {tag_commit[:9]} "
                f"— consumer CI is running a different tree than the plugin channel")
    notes.append(f"{tag} = {tag_commit[:9]}")

    if offline:
        notes.append("marketplace checks skipped (--offline)")
        return (errors, notes)

    for path, require_declared_version in MARKETPLACE_MANIFESTS:
        manifest, fetch_error = fetch_manifest(marketplace_repo, path)
        # Discriminate on the error, not on `manifest is None`: a body of
        # literal `null` parses to None and is drift, not an outage.
        if fetch_error is not None:
            notes.append(
                f"marketplace manifest unreachable, not checked ({path}): {fetch_error}")
        else:
            errors.extend(check_manifest(
                manifest, plugin, version,
                require_declared_version=require_declared_version))
            notes.append(f"marketplace manifest checked ({marketplace_repo}/{path})")

    return (errors, notes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect release drift.")
    parser.add_argument("--mode", choices=("pr", "released"), required=True)
    parser.add_argument("--repo", default=".", help="repo root")
    parser.add_argument("--base", default="origin/main", help="base ref for --mode pr")
    parser.add_argument("--plugin", default="sdl", help="plugin name in the manifest")
    parser.add_argument("--marketplace-repo", default=DEFAULT_MARKETPLACE_REPO,
                        metavar="OWNER/REPO")
    parser.add_argument("--offline", action="store_true",
                        help="skip the marketplace fetch")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    for plugin_json in PLUGIN_JSONS:
        if not (repo / plugin_json).is_file():
            print(f"{plugin_json} not found under {repo}", file=sys.stderr)
            return 1

    if args.mode == "pr":
        errors, notes = check_pr(repo, args.base, args.plugin)
    else:
        errors, notes = check_released(repo, args.plugin, args.marketplace_repo,
                                       args.offline)

    for n in notes:
        print(f"[ok]   {n}")
    for e in errors:
        print(f"[FAIL] {e}", file=sys.stderr)
    if errors:
        print(f"\n{len(errors)} release drift issue(s).", file=sys.stderr)
        return 1
    print(f"release state consistent ({args.mode} mode)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
