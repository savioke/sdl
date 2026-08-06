#!/usr/bin/env python3
"""Tests for cycle_stamp. Stdlib only; git is mocked."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cycle_stamp as cs  # noqa: E402

TEMPLATE = """\
# 04 — Verification

## Review pass

- **Reviewer:** <agent + dev name(s)>
- **Date:**
- **Diff range:** <merge-base..HEAD>

## Checks performed

### New SQL queries

- **Finding:** parameterized at `api/users.py:88`

## Residual risks

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | something   | low      | accept      | —                    |
"""

VALUES = {
    "Reviewer": "sdl-review (Claude) + Joe Cooper",
    "Date": "2026-08-06",
    "Diff range": "92cb993..HEAD",
}


class Stamp(unittest.TestCase):
    def test_all_three_fields_are_filled(self):
        out, missing = cs.stamp(TEMPLATE, VALUES)
        self.assertEqual(missing, [])
        self.assertIn("- **Reviewer:** sdl-review (Claude) + Joe Cooper", out)
        self.assertIn("- **Date:** 2026-08-06", out)
        self.assertIn("- **Diff range:** 92cb993..HEAD", out)

    def test_the_review_itself_is_never_touched(self):
        out, _ = cs.stamp(TEMPLATE, VALUES)
        self.assertIn("- **Finding:** parameterized at `api/users.py:88`", out)
        self.assertIn("| R1  | something   | low      | accept      | —", out)
        self.assertIn("### New SQL queries", out)

    def test_restamping_replaces_rather_than_appends(self):
        once, _ = cs.stamp(TEMPLATE, VALUES)
        twice, _ = cs.stamp(once, {**VALUES, "Date": "2026-09-01"})
        self.assertIn("- **Date:** 2026-09-01", twice)
        self.assertNotIn("2026-08-06", twice)
        self.assertEqual(twice.count("- **Date:**"), 1)

    def test_a_missing_field_is_reported_not_invented(self):
        out, missing = cs.stamp(TEMPLATE.replace("- **Date:**\n", ""), VALUES)
        self.assertEqual(missing, ["Date"])
        self.assertNotIn("2026-08-06", out)

    def test_a_value_containing_backticks_survives_substitution(self):
        # re.sub would treat a backslash in the replacement specially; the
        # lambda form avoids it. Guard against a regression to a plain string.
        out, _ = cs.stamp(TEMPLATE, {**VALUES,
                                     "Diff range": r"92cb993..HEAD (`a\b...HEAD`)"})
        self.assertIn(r"92cb993..HEAD (`a\b...HEAD`)", out)


class Reviewer(unittest.TestCase):
    def test_agent_and_git_user_are_combined(self):
        with mock.patch.object(cs, "git", return_value="Joe Cooper"):
            self.assertEqual(cs.reviewer("Claude"), "sdl-review (Claude) + Joe Cooper")

    def test_an_unset_git_user_does_not_crash(self):
        with mock.patch.object(cs, "git", return_value=""):
            self.assertEqual(cs.reviewer("Codex"), "sdl-review (Codex) + unknown")


class DiffRange(unittest.TestCase):
    def test_merge_base_is_resolved_to_a_short_sha(self):
        with mock.patch.object(cs, "git", side_effect=["a" * 40, "aaaaaaa"]):
            self.assertEqual(cs.diff_range("origin/main"),
                             "aaaaaaa..HEAD (`origin/main...HEAD` at review time)")

    def test_no_merge_base_falls_back_to_the_symbolic_range(self):
        # A shallow CI clone can have no common ancestor available.
        with mock.patch.object(cs, "git", return_value=""):
            self.assertEqual(cs.diff_range("origin/main"), "origin/main...HEAD")


if __name__ == "__main__":
    unittest.main()
