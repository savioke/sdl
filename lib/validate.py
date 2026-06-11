#!/usr/bin/env python3
"""SDL artifact validator.

Structural checks first; semantic checks (threat-ID coverage of new code) added
later once skills are stable enough that violations are rare.

Exit code 0 = pass. Non-zero = fail.

Run from the root of the project repo being validated. Pass --base to set the
merge base; defaults to origin/main.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_FILES = (
    ".sdl-meta.yml",
    "01-requirements.md",
    "02-threat-model.md",
    "03-implementation.md",
    "04-verification.md",
)

CODE_EXTS_NON_DOC = {
    ".py", ".go", ".ts", ".tsx", ".js", ".jsx", ".c", ".h", ".cc", ".cpp",
    ".hpp", ".rs", ".java", ".kt", ".swift", ".rb", ".php", ".cs", ".sh",
    ".sql",
}

# GitHub-executable surface. Workflow and action YAML runs in CI with repo
# secrets in scope; a hostile edit is a supply-chain vector regardless of
# extension. Treated as code even though .yml is not in CODE_EXTS_NON_DOC.
WORKFLOW_DIR_PREFIXES = (".github/workflows/", ".github/actions/")
WORKFLOW_NAMES = {"action.yml", "action.yaml"}

# Skill definitions instruct an agent — an executable spec with no compiler in
# the way, so a hostile edit hijacks behavior. Scoped to skill files only, not
# all markdown (which would sweep in the SDL artifacts themselves).
def is_workflow(p: Path) -> bool:
    return p.as_posix().startswith(WORKFLOW_DIR_PREFIXES) or p.name in WORKFLOW_NAMES


def is_skill(p: Path) -> bool:
    return p.name == "SKILL.md" or ("skills" in p.parts and p.suffix == ".md")


@dataclass
class Result:
    ok: bool
    msg: str

    def __bool__(self) -> bool:
        return self.ok


def run(cmd: list[str], check: bool = True) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True)
    if check and out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}: {out.stderr.strip()}")
    return out.stdout


def current_branch() -> str:
    return run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()


def changed_files(base: str) -> list[Path]:
    raw = run(["git", "diff", "--name-only", f"{base}...HEAD"]).splitlines()
    return [Path(p) for p in raw if p]


def code_changed(files: list[Path]) -> bool:
    return any(
        f.suffix in CODE_EXTS_NON_DOC or is_workflow(f) or is_skill(f)
        for f in files
    )


def find_cycle_for_branch(repo: Path, branch: str) -> Path | None:
    sdl = repo / "docs" / "sdl"
    if not sdl.is_dir():
        return None
    for meta in sdl.glob("*/.sdl-meta.yml"):
        text = meta.read_text(encoding="utf-8", errors="replace")
        if re.search(rf"^branch:\s*{re.escape(branch)}\s*$", text, re.MULTILINE):
            return meta.parent
    return None


def template_dir() -> Path | None:
    """Locate the templates dir from the central install for non-stub comparison."""
    candidates = [
        Path.home() / ".sdl-governance" / "templates" / "docs-sdl",
        Path(__file__).resolve().parent.parent / "templates" / "docs-sdl",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


def is_nonstub(cycle_file: Path, template_file: Path | None) -> bool:
    """A file is non-stub if it differs from the template AND has more than just
    the comment scaffolding filled in. Heuristic: any non-comment, non-blank line
    of substantive prose. Tracks multi-line HTML comments so their body lines are
    not mistaken for content."""
    if template_file and cycle_file.read_bytes() == template_file.read_bytes():
        return False
    text = cycle_file.read_text(encoding="utf-8", errors="replace")
    in_comment = False
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if in_comment:
            if "-->" in s:
                in_comment = False
            continue
        if s.startswith("<!--"):
            if "-->" not in s:
                in_comment = True
            continue
        if s.startswith("#") or s.startswith("|") or s == "---":
            continue
        # A line of actual content.
        return True
    return False


def check_cycle_present(repo: Path, branch: str, files: list[Path]) -> Result:
    if not code_changed(files):
        return Result(True, "no substantive code changes; cycle presence not required")
    cycle = find_cycle_for_branch(repo, branch)
    if cycle is None:
        return Result(False, f"code changed but no docs/sdl/*/.sdl-meta.yml has branch: {branch}")
    return Result(True, f"cycle found: {cycle.relative_to(repo)}")


def check_files_present(cycle: Path) -> Result:
    missing = [f for f in REQUIRED_FILES if not (cycle / f).is_file()]
    if missing:
        return Result(False, f"{cycle.name}: missing files: {', '.join(missing)}")
    return Result(True, f"{cycle.name}: all required files present")


def check_nonstub(cycle: Path, templates: Path | None) -> Result:
    stubs: list[str] = []
    for f in REQUIRED_FILES:
        if f == ".sdl-meta.yml":
            continue
        path = cycle / f
        tmpl = templates / f if templates else None
        if not is_nonstub(path, tmpl):
            stubs.append(f)
    if stubs:
        return Result(False, f"{cycle.name}: stub files: {', '.join(stubs)}")
    return Result(True, f"{cycle.name}: artifacts have content")


def baseline_warning(repo: Path) -> str | None:
    """Non-fatal: a repo running SDL cycles should have a non-stub baseline so
    per-cycle docs stay small. Returns a warning message or None. Does not affect
    exit code (warn-first; may become a hard check in a future major version)."""
    baseline = repo / "docs" / "sdl" / "baseline.md"
    if not baseline.is_file():
        return "no docs/sdl/baseline.md — run the sdl-baseline skill once so cycles can reference standing context instead of re-deriving it"
    if not is_nonstub(baseline, None):
        return "docs/sdl/baseline.md is still a stub — run the sdl-baseline skill to fill it"
    return None


def check_meta_branch(cycle: Path, branch: str) -> Result:
    meta = cycle / ".sdl-meta.yml"
    text = meta.read_text(encoding="utf-8", errors="replace")
    if re.search(rf"^branch:\s*{re.escape(branch)}\s*$", text, re.MULTILINE):
        return Result(True, f"{cycle.name}: meta branch matches")
    return Result(False, f"{cycle.name}: .sdl-meta.yml branch does not match {branch}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SDL artifacts.")
    parser.add_argument("--base", default="origin/main", help="merge base ref")
    parser.add_argument("--repo", default=".", help="repo root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    branch = current_branch()
    files = changed_files(args.base)
    templates = template_dir()

    results: list[Result] = []
    results.append(check_cycle_present(repo, branch, files))

    cycle = find_cycle_for_branch(repo, branch)
    if cycle is not None:
        results.append(check_files_present(cycle))
        results.append(check_meta_branch(cycle, branch))
        if all((cycle / f).is_file() for f in REQUIRED_FILES):
            results.append(check_nonstub(cycle, templates))

    failed = [r for r in results if not r]
    for r in results:
        marker = "ok " if r else "FAIL"
        print(f"[{marker}] {r.msg}")

    if code_changed(files):
        warning = baseline_warning(repo)
        if warning:
            print(f"[warn] {warning}")

    if failed:
        print(f"\n{len(failed)} check(s) failed.", file=sys.stderr)
        return 1
    print(f"\nAll {len(results)} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
