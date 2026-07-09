#!/usr/bin/env python3
"""Verify that SHA-pinned GitHub Actions match their version comments.

For every `uses: owner/repo[/path]@<40-hex-sha> # vX.Y.Z` in the given workflow
files (default: .github/workflows/*.yml|yaml), resolve the commented tag via the
GitHub API and fail if it does not resolve to the pinned SHA. Also fails on
unpinned refs and pins with no parseable version comment — the pin comment is
load-bearing evidence, not decoration.

Detects retag-after-pin drift and comment/SHA mismatches; it cannot detect a
release that was already compromised when pinned (see cycle
2026-07-09-dep-update-tier, out-of-scope threats).

Stdlib only. Uses GITHUB_TOKEN from the environment if present (rate limits
only); the token is never printed. Exit 0 = all pins verified.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

API = "https://api.github.com"

USES_RE = re.compile(
    r"^\s*(?:-\s+)?uses:\s*"
    r"(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)(?:/[\w./-]+)?"
    r"@(?P<ref>[^\s#]+)"
    r"\s*(?:#\s*(?P<comment>.*\S))?\s*$"
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
VERSION_RE = re.compile(r"^v?\d+(\.\d+)*$")


@dataclass
class Pin:
    file: str
    line: int
    action: str  # owner/repo
    ref: str
    version: str | None  # parsed from the trailing comment, or None


def parse_pins(text: str, filename: str) -> list[Pin]:
    pins = []
    for n, line in enumerate(text.splitlines(), 1):
        m = USES_RE.match(line)
        if not m:
            continue
        action = f"{m.group('owner')}/{m.group('repo')}"
        if m.group("owner").startswith(".") or m.group("ref").startswith("docker"):
            continue  # local action or docker ref — nothing to verify upstream
        comment = m.group("comment") or ""
        version = comment.split()[0] if comment else ""
        pins.append(Pin(filename, n, action, m.group("ref"),
                        version if VERSION_RE.match(version) else None))
    return pins


def resolve_tag(action: str, tag: str, token: str | None) -> str:
    """Return the commit SHA a tag points to, following annotated tags."""
    req = urllib.request.Request(
        f"{API}/repos/{action}/commits/{tag}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "sdl-check-pins",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["sha"]


def verify(pins: list[Pin], token: str | None) -> list[str]:
    errors = []
    cache: dict[tuple[str, str], str] = {}
    for p in pins:
        where = f"{p.file}:{p.line}"
        if not SHA_RE.match(p.ref):
            errors.append(f"{where}: {p.action}@{p.ref} is not pinned to a commit SHA")
            continue
        if p.version is None:
            errors.append(f"{where}: {p.action} pin has no parseable version comment")
            continue
        key = (p.action, p.version)
        try:
            if key not in cache:
                cache[key] = resolve_tag(p.action, p.version, token)
        except urllib.error.HTTPError as e:
            errors.append(f"{where}: {p.action}@{p.version}: tag lookup failed (HTTP {e.code})")
            continue
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as e:
            errors.append(f"{where}: {p.action}@{p.version}: tag lookup failed ({e.__class__.__name__})")
            continue
        if cache[key].lower() != p.ref.lower():
            errors.append(
                f"{where}: {p.action} pinned to {p.ref} but tag {p.version} "
                f"resolves to {cache[key]}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify action pins match upstream tags.")
    parser.add_argument("files", nargs="*", type=Path,
                        help="workflow files (default: .github/workflows/*.yml|yaml)")
    parser.add_argument("--repo", default=".", help="repo root")
    parser.add_argument("--exempt", action="append", default=[], metavar="OWNER/REPO",
                        help="action allowed to use a mutable ref (e.g. an org-owned "
                             "reusable workflow accepted as a moving tag)")
    args = parser.parse_args()

    files = args.files or sorted(
        p for ext in ("yml", "yaml")
        for p in (Path(args.repo) / ".github" / "workflows").glob(f"*.{ext}")
    )
    pins = []
    for f in files:
        pins.extend(p for p in parse_pins(f.read_text(encoding="utf-8", errors="replace"), str(f))
                    if p.action not in args.exempt)
    if not pins:
        print("no third-party action pins found")
        return 0

    errors = verify(pins, os.environ.get("GITHUB_TOKEN") or None)
    for e in errors:
        print(f"[FAIL] {e}", file=sys.stderr)
    ok = len(pins) - len(errors)
    print(f"{ok}/{len(pins)} pin(s) verified against upstream tags")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
