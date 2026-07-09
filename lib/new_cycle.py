#!/usr/bin/env python3
"""Scaffold an SDL cycle folder deterministically.

Replaces the agent-performed steps of sdl-spec §1–2: slug normalization,
folder creation, template copy, .sdl-meta.yml population. Run from the root
of the repo being governed:

    python3 <governance>/lib/new_cycle.py                      # full cycle
    python3 <governance>/lib/new_cycle.py --class dependency-update

Refuses to overwrite an existing folder or re-scaffold a branch that already
has a cycle. Prints the created folder path on success.
"""

from __future__ import annotations

import argparse
import datetime
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import current_branch, find_cycle_for_branch, template_dir  # noqa: E402

FULL_FILES = (
    "01-requirements.md",
    "02-threat-model.md",
    "03-implementation.md",
    "04-verification.md",
)
DEP_FILES = ("dep-update.md",)

SLUG_MAX = 40


def slugify(branch: str) -> str:
    """Normalize a branch name to a cycle slug (sdl-spec rules). The output
    alphabet is [a-z0-9-], so the result cannot traverse paths."""
    s = branch.rsplit("/", 1)[-1].lower().replace("_", "-")
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    if len(s) > SLUG_MAX:
        cut = s[:SLUG_MAX]
        if s[SLUG_MAX] != "-" and "-" in cut:
            cut = cut[: cut.rindex("-")]
        s = cut.strip("-")
    if not s:
        raise ValueError(f"branch {branch!r} normalizes to an empty slug")
    return s


META_HEADER = (
    "# SDL cycle metadata. Maintained by sdl-* skills; humans rarely edit.\n"
    "# Practice refs: SM-1 (development process), SM-5 (change management).\n"
)


def meta_text(slug: str, branch: str, created: str, cycle_class: str) -> str:
    lines = [
        f"slug: {slug}",
        f"branch: {branch}",
        f"created: {created}",
        "pr: null",
        "status: in-progress",
    ]
    if cycle_class != "full":
        lines.append(f"class: {cycle_class}")
    lines += ["related_cycles: []", "carry_forward: []"]
    return META_HEADER + "\n" + "\n".join(lines) + "\n"


def scaffold(repo: Path, branch: str, created: str, cycle_class: str,
             templates: Path) -> Path:
    existing = find_cycle_for_branch(repo, branch)
    if existing is not None:
        raise FileExistsError(
            f"branch {branch!r} already has a cycle: {existing.relative_to(repo)}")
    slug = f"{created}-{slugify(branch)}"
    cycle = repo / "docs" / "sdl" / slug
    if cycle.exists():
        raise FileExistsError(f"{cycle.relative_to(repo)} already exists")
    files = DEP_FILES if cycle_class == "dependency-update" else FULL_FILES
    missing = [f for f in files if not (templates / f).is_file()]
    if missing:
        raise FileNotFoundError(f"templates missing from {templates}: {', '.join(missing)}")
    cycle.mkdir(parents=True)
    for f in files:
        shutil.copy(templates / f, cycle / f)
    (cycle / ".sdl-meta.yml").write_text(
        meta_text(slug, branch, created, cycle_class), encoding="utf-8")
    return cycle


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold an SDL cycle folder.")
    parser.add_argument("--repo", default=".", help="repo root")
    parser.add_argument("--branch", default=None,
                        help="branch name (default: current branch)")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    parser.add_argument("--class", dest="cycle_class", default="full",
                        choices=("full", "dependency-update"), help="cycle class")
    parser.add_argument("--templates", default=None, help="templates directory")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / "docs" / "sdl").is_dir():
        print(f"{repo} has no docs/sdl/ — not an SDL-governed repo", file=sys.stderr)
        return 1
    try:
        branch = args.branch or current_branch()
    except RuntimeError as e:
        print(f"cannot determine branch ({e}); pass --branch", file=sys.stderr)
        return 1
    created = args.date or datetime.date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", created):
        print(f"--date must be YYYY-MM-DD, got {created!r}", file=sys.stderr)
        return 1
    templates = Path(args.templates) if args.templates else template_dir()
    if templates is None or not templates.is_dir():
        print("templates directory not found; pass --templates", file=sys.stderr)
        return 1

    try:
        cycle = scaffold(repo, branch, created, args.cycle_class, templates)
    except (FileExistsError, FileNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 1
    print(cycle.relative_to(repo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
