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
import os
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


def is_workflow(p: Path) -> bool:
    return p.as_posix().startswith(WORKFLOW_DIR_PREFIXES) or p.name in WORKFLOW_NAMES


# Skill definitions instruct an agent — an executable spec with no compiler in
# the way, so a hostile edit hijacks behavior. Scoped to skill files only, not
# all markdown (which would sweep in the SDL artifacts themselves).
def is_skill(p: Path) -> bool:
    return p.name == "SKILL.md" or ("skills" in p.parts and p.suffix == ".md")


# Adoption cycle class. A repo's first SDL PR adds the CI workflow — which the
# gate counts as code — and the baseline, but no feature cycle exists yet and
# none should: the baseline *is* the adoption artifact. Without this the gate
# demands a decoy cycle for the very PR that installs it.
ADOPTION_WORKFLOW = ".github/workflows/sdl.yml"
BASELINE = "docs/sdl/baseline.md"

# The generated caller delegates everything to the reusable workflow. Any other
# uses:, or any inline run:, means the PR is shipping CI behavior of its own
# under the adoption exemption — that needs a cycle like any other code.
SDL_CALLER_RE = re.compile(
    r"^\s*(?:-\s+)?uses:\s*savioke/sdl/\.github/workflows/sdl-validate\.yml@[\w./-]+\s*$"
)
INLINE_RUN_RE = re.compile(r"^\s*(?:-\s+)?run:")


# Dependency-update cycle class (docs/dependency-updates.md). Exact filenames
# only — fail closed on anything not positively identified as a manifest or
# lockfile. Manifest *content* can still carry executable config (npm scripts,
# resolved URLs); that residual is accepted at the routine tier and owned by
# policy, not the classifier (cycle 2026-07-09-dep-update-tier, T3).
DEP_MANIFEST_NAMES = {
    "package.json", "package-lock.json", "npm-shrinkwrap.json", "yarn.lock",
    "pnpm-lock.yaml", "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
    "Gemfile", "Gemfile.lock", "requirements.txt", "constraints.txt",
    "Pipfile", "Pipfile.lock", "poetry.lock", "uv.lock", "pyproject.toml",
    "composer.json", "composer.lock", ".github/dependabot.yml",
}

DEP_RECORD = "dep-update.md"

# A pinned uses: line — 40-hex SHA required, version comment optional at parse
# time (its absence fails the routine tier separately, with a clearer message).
PIN_LINE_RE = re.compile(
    r"^\s*(?:-\s+)?uses:\s*"
    r"(?P<action>[\w.-]+/[\w.-]+)(?:/[\w./-]+)?"
    r"@(?P<sha>[0-9a-fA-F]{40})"
    r"\s*(?:#\s*v?(?P<major>\d+)(?:[.\w-]*))?\s*$"
)


def is_dep_manifest(p: Path) -> bool:
    return p.name in DEP_MANIFEST_NAMES or p.as_posix() in DEP_MANIFEST_NAMES


def pin_only_workflow_diff(base: str, path: Path) -> Result:
    """Accept a workflow diff only if every changed line is a SHA-pinned uses:
    line, every added action has a removed counterpart (same owner/repo — a new
    or swapped action is not a routine update), and majors match per action."""
    diff = run(["git", "diff", f"{base}...HEAD", "--", path.as_posix()])
    removed: dict[str, set[str]] = {}
    added: dict[str, set[str]] = {}
    for line in diff.splitlines():
        # File headers are exactly "--- a/..." / "+++ b/..."; content lines are
        # "-"/"+" followed directly by file text, so the space disambiguates.
        if line.startswith(("--- ", "+++ ")):
            continue
        if not line.startswith(("-", "+")):
            continue
        m = PIN_LINE_RE.match(line[1:])
        if not m:
            return Result(False, f"{path}: non-pin change: {line[1:].strip()[:80]!r}")
        if m.group("major") is None:
            return Result(False, f"{path}: pin for {m.group('action')} lacks a parseable version comment")
        bucket = removed if line.startswith("-") else added
        bucket.setdefault(m.group("action"), set()).add(m.group("major"))
    for action, majors in added.items():
        if action not in removed:
            return Result(False, f"{path}: new action {action} — not a routine update")
        if majors != removed[action]:
            return Result(False, f"{path}: major version bump for {action} — requires a full cycle")
    for action in removed:
        if action not in added:
            return Result(False, f"{path}: action {action} removed — CI behavior change, not a routine update")
    return Result(True, f"{path}: pin-only workflow change")


def check_dep_class_diff(base: str, files: list[Path]) -> Result:
    """The whole diff must be dependency-shaped for the routine tier to apply."""
    for f in files:
        if f.as_posix().startswith("docs/sdl/"):
            continue
        if is_dep_manifest(f):
            continue
        if is_workflow(f):
            r = pin_only_workflow_diff(base, f)
            if not r:
                return r
            continue
        return Result(False, f"{f} is neither a dependency manifest nor a workflow — full cycle required")
    return Result(True, "diff is dependency-only")


def parse_version_major(version: str) -> str | None:
    m = re.match(r"v?(\d+)", version.strip())
    return m.group(1) if m else None


def check_dep_record(cycle: Path, templates: Path | None) -> Result:
    """dep-update.md must exist, have content, and declare only non-major bumps."""
    record = cycle / DEP_RECORD
    if not record.is_file():
        return Result(False, f"{cycle.name}: missing {DEP_RECORD}")
    tmpl = templates / DEP_RECORD if templates else None
    if not is_nonstub(record, tmpl):
        return Result(False, f"{cycle.name}: {DEP_RECORD} is a stub")
    rows = []
    for line in record.read_text(encoding="utf-8", errors="replace").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not line.strip().startswith("|"):
            continue
        if cells[0].lower() in ("package", "") or set(cells[0]) <= {"-", " ", ":"}:
            continue
        rows.append(cells)
    if not rows:
        return Result(False, f"{cycle.name}: {DEP_RECORD} declares no updates")
    for cells in rows:
        name, old, new = cells[0], cells[1], cells[2]
        old_major, new_major = parse_version_major(old), parse_version_major(new)
        if old_major is None or new_major is None:
            return Result(False, f"{cycle.name}: {DEP_RECORD}: unparseable versions for {name}")
        if old_major != new_major:
            return Result(False, f"{cycle.name}: {DEP_RECORD}: major bump declared for {name} — requires a full cycle")
    return Result(True, f"{cycle.name}: {DEP_RECORD} declares {len(rows)} non-major update(s)")


def cycle_class(cycle: Path) -> str | None:
    meta = cycle / ".sdl-meta.yml"
    if not meta.is_file():
        return None
    m = re.search(r"^class:\s*(\S+)\s*$",
                  meta.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
    return m.group(1) if m else None


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
    # GitHub Actions checks out a detached merge commit for `pull_request`
    # events, so `git rev-parse --abbrev-ref HEAD` returns "HEAD" and never
    # matches a cycle's `branch:` field. Prefer the CI-provided source-branch
    # name when present; fall back to git for `push` events and local runs.
    head_ref = os.environ.get("GITHUB_HEAD_REF", "").strip()
    if head_ref:
        return head_ref
    return run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()


def changed_files(base: str) -> list[Path]:
    raw = run(["git", "diff", "--name-only", f"{base}...HEAD"]).splitlines()
    return [Path(p) for p in raw if p]


def added_files(base: str) -> set[str]:
    raw = run(["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD"]).splitlines()
    return {p for p in raw if p}


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
    """Locate the templates dir for non-stub comparison: next to this file
    (plugin install or checkout), else the clone at ~/.sdl-governance."""
    candidates = [
        Path(__file__).resolve().parent.parent / "templates" / "docs-sdl",
        Path.home() / ".sdl-governance" / "plugins" / "sdl" / "templates" / "docs-sdl",
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


def is_adoption_workflow(repo: Path) -> bool:
    """True if the repo's sdl.yml is the generated caller and nothing more."""
    path = repo / ADOPTION_WORKFLOW
    if not path.is_file():
        return False
    saw_caller = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if INLINE_RUN_RE.match(line):
            return False
        if "uses:" in line:
            if not SDL_CALLER_RE.match(line):
                return False
            saw_caller = True
    return saw_caller


def check_adoption(repo: Path, base: str, files: list[Path], templates: Path | None) -> Result | None:
    """Recognize the PR that adopts SDL, which cannot have a cycle yet.

    Returns None when the diff is not adoption-shaped, so the caller falls back
    to the ordinary cycle requirement. Narrow on purpose: it fires only while
    baseline.md is being ADDED, so a repo gets it once and never again, and the
    only non-doc file it admits is the generated workflow, also newly added.
    """
    added = added_files(base)
    if BASELINE not in added:
        return None
    for f in files:
        p = f.as_posix()
        if p.startswith("docs/sdl/"):
            continue
        if p == ADOPTION_WORKFLOW and p in added:
            continue
        return None
    tmpl = templates.parent / "baseline.md" if templates else None
    if not is_nonstub(repo / BASELINE, tmpl if tmpl and tmpl.is_file() else None):
        return Result(False, "adoption PR: docs/sdl/baseline.md is still a stub — "
                             "run the sdl-baseline skill to fill it")
    if not is_adoption_workflow(repo):
        return Result(False, f"adoption PR: {ADOPTION_WORKFLOW} is not the generated SDL caller — "
                             "a PR that also changes CI behavior needs a cycle")
    return Result(True, "adoption PR: baseline authored, no cycle required")


def check_cycle_present(repo: Path, branch: str, files: list[Path],
                        base: str, templates: Path | None) -> Result:
    if not code_changed(files):
        return Result(True, "no substantive code changes; cycle presence not required")
    cycle = find_cycle_for_branch(repo, branch)
    if cycle is not None:
        return Result(True, f"cycle found: {cycle.relative_to(repo)}")
    adoption = check_adoption(repo, base, files, templates)
    if adoption is not None:
        return adoption
    return Result(False, f"code changed but no SDL cycle declares this branch — no "
                         f"docs/sdl/*/.sdl-meta.yml has 'branch: {branch}'. Run the sdl-spec skill.")


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
    results.append(check_cycle_present(repo, branch, files, args.base, templates))

    cycle = find_cycle_for_branch(repo, branch)
    if cycle is not None:
        results.append(check_meta_branch(cycle, branch))
        cls = cycle_class(cycle)
        if cls == "dependency-update":
            results.append(check_dep_class_diff(args.base, files))
            results.append(check_dep_record(cycle, templates))
        elif cls is not None:
            results.append(Result(False, f"{cycle.name}: unknown cycle class {cls!r}"))
        else:
            results.append(check_files_present(cycle))
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

    # Warn-first: manifest/lockfile-only diffs pass the gate today (not "code"),
    # but at fleet scale they should carry a dependency-update record too.
    # Becomes a hard check in a future major version (see docs/dependency-updates.md).
    if cycle is None and not code_changed(files) and any(is_dep_manifest(f) for f in files):
        print("[warn] dependency manifests changed with no dependency-update cycle — "
              "see docs/dependency-updates.md")

    if failed:
        print(f"\n{len(failed)} check(s) failed.", file=sys.stderr)
        return 1
    print(f"\nAll {len(results)} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
