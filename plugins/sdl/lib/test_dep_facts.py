#!/usr/bin/env python3
"""Tests for dep_facts. Stdlib only; git is mocked.

The property under test throughout: what lands in the record is what is in the
diff. A row this tool invents, or a version it drops, is an audit defect.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dep_facts as df  # noqa: E402
import validate as v  # noqa: E402

SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40


def diff(*lines: str) -> str:
    return "\n".join(("diff --git a/w.yml b/w.yml", "--- a/w.yml", "+++ b/w.yml", *lines))


class PinBumps(unittest.TestCase):
    def bumps(self, *lines: str) -> list[df.Bump]:
        with mock.patch.object(df, "run", return_value=diff(*lines)):
            return df.pin_bumps("origin/main", Path("w.yml"))

    def test_paired_bump_is_read_from_the_diff(self):
        self.assertEqual(
            self.bumps(f"-      - uses: actions/checkout@{SHA_A} # v7.0.0",
                       f"+      - uses: actions/checkout@{SHA_B} # v7.0.1"),
            [df.Bump("actions/checkout", "v7.0.0", "v7.0.1")],
        )

    def test_several_actions_are_reported_in_a_stable_order(self):
        got = self.bumps(
            f"-      - uses: actions/setup-python@{SHA_A} # v6.2.0",
            f"+      - uses: actions/setup-python@{SHA_B} # v6.3.0",
            f"-      - uses: actions/checkout@{SHA_B} # v7.0.0",
            f"+      - uses: actions/checkout@{SHA_C} # v7.0.1",
        )
        self.assertEqual([b.package for b in got],
                         ["actions/checkout", "actions/setup-python"])

    def test_subdirectory_action_keeps_owner_repo_identity(self):
        self.assertEqual(
            self.bumps(f"-      - uses: github/codeql-action/init@{SHA_A} # v3.1.0",
                       f"+      - uses: github/codeql-action/init@{SHA_B} # v3.2.0"),
            [df.Bump("github/codeql-action", "v3.1.0", "v3.2.0")],
        )

    def test_added_action_with_no_counterpart_yields_no_row(self):
        # An unpaired add is a new trust relationship. Triage rejects the diff
        # before this runs; inventing a from-version here would paper over it.
        self.assertEqual(
            self.bumps(f"+      - uses: actions/cache@{SHA_A} # v4.0.0"), [])

    def test_pin_without_a_version_comment_yields_no_row(self):
        self.assertEqual(
            self.bumps(f"-      - uses: actions/checkout@{SHA_A}",
                       f"+      - uses: actions/checkout@{SHA_B}"), [])

    def test_sha_only_change_is_not_a_version_bump(self):
        # Same version on both sides: a re-pin, not an update. No row.
        self.assertEqual(
            self.bumps(f"-      - uses: actions/checkout@{SHA_A} # v7.0.0",
                       f"+      - uses: actions/checkout@{SHA_B} # v7.0.0"), [])

    def test_file_headers_are_not_parsed_as_content(self):
        # "--- a/w.yml" must not be mistaken for a removed line.
        self.assertEqual(
            self.bumps(f"-      - uses: actions/checkout@{SHA_A} # v7.0.0",
                       f"+      - uses: actions/checkout@{SHA_B} # v7.0.1"),
            [df.Bump("actions/checkout", "v7.0.0", "v7.0.1")],
        )


class SharedRegexWithTheGate(unittest.TestCase):
    """The generator and the validator must read a pin the same way."""

    def test_version_group_is_the_whole_comment_version(self):
        m = v.PIN_LINE_RE.match(f"      - uses: actions/checkout@{SHA_A} # v7.0.1")
        self.assertEqual(m.group("version"), "v7.0.1")
        self.assertEqual(m.group("major"), "7")

    def test_unprefixed_version_still_parses(self):
        m = v.PIN_LINE_RE.match(f"      - uses: actions/checkout@{SHA_A} # 7.0.1")
        self.assertEqual(m.group("version"), "7.0.1")
        self.assertEqual(m.group("major"), "7")

    def test_an_unrecognized_comment_does_not_parse(self):
        """The regex fails closed, which is what bounds 02:T3.

        Both callers depend on this: a comment the regex cannot read must not
        become a version in a record, and must not pass the gate's pin check.
        It is rejected as a non-pin change instead, which escalates.
        """
        for comment in ("# v7.0.0 (pinned 2026-01)", "# renovate: v8.0.0",
                        "# latest", "# see PR 41"):
            line = f"      - uses: actions/checkout@{SHA_A} {comment}"
            self.assertIsNone(v.PIN_LINE_RE.match(line), comment)

    def test_a_pin_the_regex_rejects_escalates_rather_than_passing(self):
        with mock.patch.object(v, "run", return_value=diff(
                f"-      - uses: actions/checkout@{SHA_A} # latest",
                f"+      - uses: actions/checkout@{SHA_B} # latest")):
            result = v.pin_only_workflow_diff("origin/main", Path("w.yml"))
        self.assertFalse(result)
        self.assertIn("non-pin change", result.msg)


class Collect(unittest.TestCase):
    def test_sdl_artifacts_and_manifests_are_separated(self):
        files = [Path("docs/sdl/x/dep-update.md"), Path("package-lock.json"),
                 Path(".github/workflows/ci.yml")]
        with mock.patch.object(df, "run", return_value=diff(
                f"-      - uses: actions/checkout@{SHA_A} # v7.0.0",
                f"+      - uses: actions/checkout@{SHA_B} # v7.0.1")):
            bumps, manifests = df.collect("origin/main", files)
        self.assertEqual(bumps, [df.Bump("actions/checkout", "v7.0.0", "v7.0.1")])
        self.assertEqual(manifests, [Path("package-lock.json")])


class GuessSource(unittest.TestCase):
    def test_automation_branches_are_recognized(self):
        self.assertEqual(df.guess_source("dependabot/github_actions/actions-abc"),
                         "dependabot")
        self.assertEqual(df.guess_source("renovate/actions-checkout-7.x"), "renovate")

    def test_anything_else_is_a_human(self):
        self.assertEqual(df.guess_source("bump-checkout"), "human")


RECORD = """\
# Dependency update record

## Updates

| package | from | to | source |
|---------|------|----|--------|
|         |      |    |        |

## Checks

- [ ] Pins/hashes verified against upstream
- [ ] Advisory lookup for the new versions

## Notes
"""


class FillUpdatesTable(unittest.TestCase):
    def test_body_is_replaced_and_the_rest_survives(self):
        out = df.fill_updates_table(
            RECORD, ["| actions/checkout | v7.0.0 | v7.0.1 | dependabot |"])
        self.assertIn("| actions/checkout | v7.0.0 | v7.0.1 | dependabot |", out)
        self.assertNotIn("|         |      |    |        |", out)
        self.assertIn("| package | from | to | source |", out)
        self.assertIn("|---------|------|----|--------|", out)

    def test_attestation_is_left_for_the_author(self):
        # A tool must never check a box on someone's behalf.
        out = df.fill_updates_table(RECORD, ["| a/b | v1 | v2 | human |"])
        self.assertIn("- [ ] Pins/hashes verified against upstream", out)
        self.assertIn("- [ ] Advisory lookup for the new versions", out)
        self.assertNotIn("- [x]", out)
        self.assertTrue(out.rstrip().endswith("## Notes"))

    def test_rewriting_an_already_filled_table_replaces_it(self):
        once = df.fill_updates_table(RECORD, ["| a/b | v1 | v2 | human |"])
        twice = df.fill_updates_table(once, ["| a/b | v1 | v3 | human |"])
        self.assertIn("| a/b | v1 | v3 | human |", twice)
        self.assertNotIn("| a/b | v1 | v2 | human |", twice)

    def test_missing_header_is_an_error_not_a_silent_no_op(self):
        with self.assertRaises(ValueError):
            df.fill_updates_table("# Record\n\nno table here\n", ["| a | b | c | d |"])


class RoundTripThroughTheValidator(unittest.TestCase):
    """A generated record must satisfy the gate that reads it back."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.cycle = Path(self._tmp.name) / "2026-01-01-bump"
        self.cycle.mkdir()

    def write(self, bumps):
        rows = [b.row("dependabot") for b in bumps]
        (self.cycle / v.DEP_RECORD).write_text(
            df.fill_updates_table(RECORD, rows), encoding="utf-8")

    def test_generated_rows_pass_check_dep_record(self):
        self.write([df.Bump("actions/checkout", "v7.0.0", "v7.0.1"),
                    df.Bump("actions/setup-python", "v6.2.0", "v6.3.0")])
        result = v.check_dep_record(self.cycle, None)
        self.assertTrue(result, result.msg)
        self.assertIn("2 non-major", result.msg)

    def test_a_major_bump_still_fails_the_gate_when_generated(self):
        # The generator has no veto: it reports what the diff says, and the
        # validator rejects it independently.
        self.write([df.Bump("actions/setup-python", "v6.3.0", "v7.0.0")])
        result = v.check_dep_record(self.cycle, None)
        self.assertFalse(result)
        self.assertIn("major bump", result.msg)


class Report(unittest.TestCase):
    def test_non_mechanical_triggers_are_always_named(self):
        out = "\n".join(df.report([df.Bump("a/b", "v1.0", "v1.1")], [], "dependabot"))
        for trigger in df.ATTESTED_TRIGGERS:
            self.assertIn(trigger, out)

    def test_manifests_are_flagged_as_the_authors_to_fill(self):
        out = "\n".join(df.report([], [Path("go.mod")], "human"))
        self.assertIn("go.mod", out)
        self.assertIn("does not parse ecosystem lockfiles", out)

    def test_no_pin_bumps_is_stated_rather_than_left_blank(self):
        out = "\n".join(df.report([], [], "human"))
        self.assertIn("no action pins changed", out)


if __name__ == "__main__":
    unittest.main()
