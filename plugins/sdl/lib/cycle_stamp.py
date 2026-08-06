#!/usr/bin/env python3
"""Fill the mechanical fields of a cycle's verification artifact.

`sdl-review` currently reconstructs four things by hand that git already knows:
the reviewer's name, today's date, the diff range under review, and the commit
that last touched each file in the mitigation table. Each is a shell command
whose output gets transcribed into markdown — work with no judgment in it, and
a place for a wrong SHA to enter an audit record.

  --write CYCLE_DIR   stamps Reviewer / Date / Diff range into
                      CYCLE_DIR/04-verification.md

Only those three fields are written. Findings, categories, and residual risks
are the review itself and are never touched. The per-file commit SHAs are
printed for the 03 mitigation table rather than written, because which file
backs which threat is a judgment this tool cannot make.

Stdlib only.
"""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

VERIFICATION = "04-verification.md"

FIELD_RES = {
    "Reviewer": re.compile(r"^(?P<prefix>-\s*\*\*Reviewer:\*\*).*$", re.MULTILINE),
    "Date": re.compile(r"^(?P<prefix>-\s*\*\*Date:\*\*).*$", re.MULTILINE),
    "Diff range": re.compile(r"^(?P<prefix>-\s*\*\*Diff range:\*\*).*$", re.MULTILINE),
}


def git(*args: str, check: bool = True) -> str:
    out = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {out.stderr.strip()}")
    return out.stdout.strip()


def reviewer(agent: str) -> str:
    name = git("config", "user.name", check=False) or "unknown"
    return f"sdl-review ({agent}) + {name}"


def diff_range(base: str) -> str:
    """The concrete merge-base..HEAD range, with the symbolic form alongside.

    The short SHA is what makes the record reproducible later: `origin/main`
    will have moved on by the time anyone reads it.
    """
    merge_base = git("merge-base", "HEAD", base, check=False)
    if not merge_base:
        return f"{base}...HEAD"
    return f"{git('rev-parse', '--short', merge_base)}..HEAD (`{base}...HEAD` at review time)"


def changed_files(base: str) -> list[str]:
    raw = git("diff", "--name-only", f"{base}...HEAD", check=False)
    return [p for p in raw.splitlines() if p]


def last_commit(path: str) -> str:
    return git("log", "-1", "--format=%h", "--", path, check=False) or "—"


def stamp(text: str, values: dict[str, str]) -> tuple[str, list[str]]:
    """Rewrite each known field in place. Returns the text and what was missed."""
    missing = []
    for label, value in values.items():
        pattern = FIELD_RES[label]
        if not pattern.search(text):
            missing.append(label)
            continue
        text = pattern.sub(lambda m: f"{m.group('prefix')} {value}", text, count=1)
    return text, missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit or write the mechanical fields of an SDL cycle review.")
    parser.add_argument("--base", default="origin/main", help="merge base ref")
    parser.add_argument("--repo", default=".", help="repo root")
    parser.add_argument("--agent", default="Claude",
                        help="agent name for the Reviewer field (default: Claude)")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    parser.add_argument("--write", metavar="CYCLE_DIR", default=None,
                        help=f"stamp the fields into CYCLE_DIR/{VERIFICATION}")
    args = parser.parse_args()

    values = {
        "Reviewer": reviewer(args.agent),
        "Date": args.date or datetime.date.today().isoformat(),
        "Diff range": diff_range(args.base),
    }
    for label, value in values.items():
        print(f"- **{label}:** {value}")

    files = changed_files(args.base)
    if files:
        print(f"\nLast commit per changed file (for the 03 mitigation table):")
        for f in files:
            print(f"  {last_commit(f)}  {f}")

    if args.write:
        target = Path(args.repo) / args.write / VERIFICATION
        if not target.is_file():
            print(f"\n--write: {target} does not exist", file=sys.stderr)
            return 1
        text, missing = stamp(target.read_text(encoding="utf-8"), values)
        target.write_text(text, encoding="utf-8")
        if missing:
            print(f"\nwrote {target} — but no field line found for: "
                  f"{', '.join(missing)}", file=sys.stderr)
            return 1
        print(f"\nstamped {target}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
