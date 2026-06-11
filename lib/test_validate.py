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
        self.assertFalse(v.check_cycle_present(self.repo, "feature/login", files))
        self.make_cycle("2026-06-10-feature", "feature/login")
        self.assertTrue(v.check_cycle_present(self.repo, "feature/login", files))

    def test_check_cycle_present_docs_only_passes_without_cycle(self):
        self.assertTrue(v.check_cycle_present(self.repo, "feature/login", [P("README.md")]))

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


if __name__ == "__main__":
    unittest.main()
