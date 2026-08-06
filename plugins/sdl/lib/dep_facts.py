#!/usr/bin/env python3
"""Derive the facts for a routine-tier dependency-update record from the diff.

Answers the two questions `sdl-dep-update` would otherwise reason through by
hand, using the same code the gate uses to check the answers:

  1. **Triage** — does this diff qualify for the routine tier, and if not,
     which escalation trigger fired?
  2. **Updates** — the exact old and new versions, as record table rows.

A version in an audit record should never be transcribed by hand. Everything
printed here is read out of the diff.

Coverage is deliberately partial and says so. A GitHub Actions pin carries its
identity and version in the `uses:` line and its pin comment, so those rows are
generated in full. Language-ecosystem manifests are reported as changed but
their rows are left blank for the author: parsing every lockfile format is a
different project, and a guessed version in an attestation is worse than an
empty one.

Two triage triggers are NOT mechanical and remain the author's attestation,
per docs/dependency-updates.md: manifest changes beyond version fields, and an
advisory affecting the new version. Both are named in the output so they are
not quietly forgotten.

Exit 0 = the routine tier applies. Exit 2 = escalate; the reason is on stdout.
Exit 1 = the tool itself failed.

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate import (  # noqa: E402
    DEP_RECORD,
    PIN_LINE_RE,
    changed_files,
    check_dep_class_diff,
    current_branch,
    is_dep_manifest,
    is_workflow,
    run,
)

TABLE_HEADER_RE = re.compile(r"^\|\s*package\s*\|", re.IGNORECASE)

# Which automation opened this. Branch naming is the only signal available from
# the diff alone; --source overrides when the guess is wrong.
BRANCH_SOURCES = (
    ("dependabot/", "dependabot"),
    ("renovate/", "renovate"),
)

ATTESTED_TRIGGERS = (
    "manifest changes beyond version fields (scripts, hooks, build config)",
    "advisory affecting the new version (OSV / GitHub Advisory DB)",
)


class Bump:
    """One dependency moving from one version to another."""

    def __init__(self, package: str, old: str, new: str):
        self.package = package
        self.old = old
        self.new = new

    def row(self, source: str) -> str:
        return f"| {self.package} | {self.old} | {self.new} | {source} |"

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Bump)
                and (self.package, self.old, self.new)
                == (other.package, other.old, other.new))

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Bump({self.package!r}, {self.old!r}, {self.new!r})"


def diff_lines(base: str, path: Path) -> list[str]:
    """Content lines of a file's diff, with the +/- marker kept.

    File headers are exactly "--- a/..." / "+++ b/...": the trailing space is
    what distinguishes them from a content line, which has file text directly
    after the marker. Same disambiguation validate.pin_only_workflow_diff uses.
    """
    out = []
    for line in run(["git", "diff", f"{base}...HEAD", "--", path.as_posix()]).splitlines():
        if line.startswith(("--- ", "+++ ")):
            continue
        if line.startswith(("-", "+")):
            out.append(line)
    return out


def pin_bumps(base: str, path: Path) -> list[Bump]:
    """Version changes for SHA-pinned actions in one workflow file.

    Only pairs an action that appears on both sides of the diff. An unpaired
    add or removal is an escalation trigger, not a bump, and triage rejects the
    diff before this runs — so silence here is correct rather than lossy.
    """
    removed: dict[str, str] = {}
    added: dict[str, str] = {}
    for line in diff_lines(base, path):
        m = PIN_LINE_RE.match(line[1:])
        if not m or m.group("version") is None:
            continue
        side = removed if line.startswith("-") else added
        side[m.group("action")] = m.group("version")
    return [
        Bump(action, removed[action], added[action])
        for action in sorted(added)
        if action in removed and removed[action] != added[action]
    ]


def collect(base: str, files: list[Path]) -> tuple[list[Bump], list[Path]]:
    """Generated bumps, and the manifests whose rows the author must fill."""
    bumps: list[Bump] = []
    manifests: list[Path] = []
    for f in sorted(files, key=lambda p: p.as_posix()):
        if f.as_posix().startswith("docs/sdl/"):
            continue
        if is_dep_manifest(f):
            manifests.append(f)
        elif is_workflow(f):
            bumps.extend(pin_bumps(base, f))
    return bumps, manifests


def guess_source(branch: str) -> str:
    for prefix, name in BRANCH_SOURCES:
        if branch.startswith(prefix):
            return name
    return "human"


def fill_updates_table(text: str, rows: list[str]) -> str:
    """Replace the Updates table body with `rows`, leaving the rest untouched.

    Only the table body is rewritten. The Checks boxes stay unchecked and the
    Notes section stays empty on purpose: those are the author's attestation,
    and a tool must not check a box on someone's behalf.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not TABLE_HEADER_RE.match(line.strip()):
            continue
        body = i + 2  # skip the header and its |---| separator
        end = body
        while end < len(lines) and lines[end].strip().startswith("|"):
            end += 1
        return "\n".join(lines[:body] + rows + lines[end:]) + "\n"
    raise ValueError(f"no '| package |' table header found in {DEP_RECORD}")


def report(bumps: list[Bump], manifests: list[Path], source: str) -> list[str]:
    out = ["", "## Updates", ""]
    out.append("| package | from | to | source |")
    out.append("|---------|------|----|--------|")
    out.extend(b.row(source) for b in bumps)
    if not bumps:
        out.append("<!-- no action pins changed -->")
    out.append("")
    if manifests:
        out.append("Manifests changed — add a row per package yourself, from the "
                   "lockfile diff. This tool does not parse ecosystem lockfiles:")
        out.extend(f"  - {m.as_posix()}" for m in manifests)
        out.append("")
    out.append("Still yours to verify (not mechanically checkable):")
    out.extend(f"  - {t}" for t in ATTESTED_TRIGGERS)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Triage a dependency diff and emit its record table rows.")
    parser.add_argument("--base", default="origin/main", help="merge base ref")
    parser.add_argument("--repo", default=".", help="repo root")
    parser.add_argument("--source", default=None,
                        choices=("dependabot", "renovate", "scanner", "human"),
                        help="who opened this (default: guessed from the branch name)")
    parser.add_argument("--write", metavar="CYCLE_DIR", default=None,
                        help=f"fill the Updates table in CYCLE_DIR/{DEP_RECORD} in place")
    args = parser.parse_args()

    files = changed_files(args.base)
    if not files:
        print(f"no changes against {args.base}")
        return 0

    verdict = check_dep_class_diff(args.base, files)
    if not verdict:
        print(f"ESCALATE: {verdict.msg}")
        print("\nThis diff does not qualify for the routine tier. Report the "
              "trigger and stop; a full cycle starts with the sdl-spec skill.")
        return 2
    print(f"ROUTINE: {verdict.msg}")

    source = args.source or guess_source(current_branch())
    bumps, manifests = collect(args.base, files)
    print("\n".join(report(bumps, manifests, source)))

    if args.write:
        record = Path(args.repo) / args.write / DEP_RECORD if not Path(args.write).is_absolute() \
            else Path(args.write) / DEP_RECORD
        if not record.is_file():
            print(f"\n--write: {record} does not exist — scaffold the cycle first "
                  f"(new_cycle.py --class dependency-update)", file=sys.stderr)
            return 1
        rows = [b.row(source) for b in bumps]
        if not rows:
            print(f"\n--write: nothing to write — no action pin bumps found; "
                  f"fill {DEP_RECORD} by hand from the manifest diff", file=sys.stderr)
            return 1
        text = record.read_text(encoding="utf-8")
        record.write_text(fill_updates_table(text, rows), encoding="utf-8")
        print(f"\nwrote {len(rows)} row(s) to {record}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
