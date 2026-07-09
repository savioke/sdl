#!/usr/bin/env python3
"""Tests for the cycle scaffolder. Stdlib only — run with:

    python3 lib/test_new_cycle.py       # or: python3 -m unittest -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import new_cycle as nc  # noqa: E402


class Slugify(unittest.TestCase):
    def test_basic_normalization(self):
        self.assertEqual(nc.slugify("Fix_Update_Instructions"), "fix-update-instructions")
        self.assertEqual(nc.slugify("faster-maybe"), "faster-maybe")

    def test_strips_prefix_before_last_slash(self):
        self.assertEqual(nc.slugify("feature/user/add-thing"), "add-thing")
        self.assertEqual(nc.slugify("dependabot/github_actions/actions-abc123"),
                         "actions-abc123")

    def test_drops_illegal_characters(self):
        self.assertEqual(nc.slugify("fix: crash! (v2)"), "fixcrashv2")
        self.assertEqual(nc.slugify("héllo wörld"), "hllowrld")

    def test_traversal_attempts_cannot_escape(self):
        # The last path segment is taken first, then non-[a-z0-9-] dropped:
        # a slug can never contain a separator or dot. Inputs that normalize
        # to nothing fail closed with ValueError.
        for hostile in ("../../etc/passwd", "a/../../b", "..", "x/./y", "a\\..\\b"):
            try:
                slug = nc.slugify(hostile)
            except ValueError:
                continue
            self.assertNotIn("/", slug)
            self.assertNotIn("\\", slug)
            self.assertNotIn(".", slug)

    def test_truncates_on_hyphen_boundary(self):
        slug = nc.slugify("a" * 30 + "-" + "b" * 30)
        self.assertEqual(slug, "a" * 30)
        self.assertEqual(nc.slugify("a" * 50), "a" * 40)

    def test_collapses_hyphen_runs_and_trims(self):
        self.assertEqual(nc.slugify("--weird---name--"), "weird-name")

    def test_empty_slug_raises(self):
        for branch in ("...", "///", "日本語", ""):
            with self.assertRaises(ValueError):
                nc.slugify(branch)


class Scaffold(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        (self.repo / "docs" / "sdl").mkdir(parents=True)
        self.templates = Path(self.tmp.name) / "templates"
        self.templates.mkdir()
        for f in nc.FULL_FILES + nc.DEP_FILES:
            (self.templates / f).write_text(f"# {f}\n", encoding="utf-8")

    def scaffold(self, branch="my-branch", cycle_class="full", date="2026-07-09"):
        return nc.scaffold(self.repo, branch, date, cycle_class, self.templates)

    def test_full_cycle_layout(self):
        cycle = self.scaffold()
        self.assertEqual(cycle, self.repo / "docs" / "sdl" / "2026-07-09-my-branch")
        for f in nc.FULL_FILES + (".sdl-meta.yml",):
            self.assertTrue((cycle / f).is_file(), f)
        self.assertFalse((cycle / "dep-update.md").exists())

    def test_meta_content(self):
        meta = (self.scaffold() / ".sdl-meta.yml").read_text(encoding="utf-8")
        self.assertTrue(meta.startswith("# SDL cycle metadata."))
        self.assertIn("slug: 2026-07-09-my-branch\n", meta)
        self.assertIn("branch: my-branch\n", meta)
        self.assertIn("created: 2026-07-09\n", meta)
        self.assertIn("pr: null\n", meta)
        self.assertIn("status: in-progress\n", meta)
        self.assertNotIn("class:", meta)

    def test_meta_keeps_original_branch_name(self):
        cycle = self.scaffold(branch="feature/My_Branch")
        meta = (cycle / ".sdl-meta.yml").read_text(encoding="utf-8")
        self.assertIn("branch: feature/My_Branch\n", meta)
        self.assertIn("slug: 2026-07-09-my-branch\n", meta)

    def test_dep_class_layout(self):
        cycle = self.scaffold(cycle_class="dependency-update")
        self.assertTrue((cycle / "dep-update.md").is_file())
        for f in nc.FULL_FILES:
            self.assertFalse((cycle / f).exists(), f)
        meta = (cycle / ".sdl-meta.yml").read_text(encoding="utf-8")
        self.assertIn("class: dependency-update\n", meta)

    def test_refuses_existing_folder(self):
        (self.repo / "docs" / "sdl" / "2026-07-09-my-branch").mkdir()
        with self.assertRaises(FileExistsError):
            self.scaffold()

    def test_refuses_branch_with_existing_cycle(self):
        self.scaffold()
        with self.assertRaises(FileExistsError):
            self.scaffold(date="2026-07-10")

    def test_missing_template_fails_before_creating(self):
        (self.templates / "02-threat-model.md").unlink()
        with self.assertRaises(FileNotFoundError):
            self.scaffold()
        self.assertFalse((self.repo / "docs" / "sdl" / "2026-07-09-my-branch").exists())

    def test_cycle_stays_under_docs_sdl(self):
        cycle = self.scaffold(branch="weird/../name")
        self.assertEqual(cycle.parent, self.repo / "docs" / "sdl")


if __name__ == "__main__":
    unittest.main(verbosity=2)
