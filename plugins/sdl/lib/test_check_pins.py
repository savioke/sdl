#!/usr/bin/env python3
"""Tests for check_pins. Stdlib only; network is mocked."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_pins as cp  # noqa: E402

SHA_A = "a" * 40
SHA_B = "b" * 40

WORKFLOW = f"""\
name: x
jobs:
  j:
    steps:
      - uses: actions/checkout@{SHA_A} # v7.0.0
      - uses: ./local/action
      - uses: docker://alpine:3.20
      - name: reusable
        uses: savioke/sdl/.github/workflows/sdl-validate.yml@v1
      - uses: actions/setup-python@{SHA_B}
"""


class ParsePins(unittest.TestCase):
    def setUp(self):
        self.pins = cp.parse_pins(WORKFLOW, "w.yml")

    def test_local_and_docker_refs_skipped(self):
        self.assertEqual([p.action for p in self.pins],
                         ["actions/checkout", "savioke/sdl", "actions/setup-python"])

    def test_version_parsed_from_comment(self):
        self.assertEqual(self.pins[0].version, "v7.0.0")

    def test_missing_comment_gives_none(self):
        self.assertIsNone(self.pins[2].version)

    def test_reusable_workflow_action_is_owner_repo(self):
        self.assertEqual(self.pins[1].action, "savioke/sdl")
        self.assertEqual(self.pins[1].ref, "v1")

    def test_non_version_comment_gives_none(self):
        pins = cp.parse_pins(f"uses: a/b@{SHA_A} # pinned last tuesday", "w.yml")
        self.assertIsNone(pins[0].version)


class Verify(unittest.TestCase):
    def pin(self, ref=SHA_A, version="v7.0.0"):
        return cp.Pin("w.yml", 1, "actions/checkout", ref, version)

    def test_matching_sha_passes(self):
        with mock.patch.object(cp, "resolve_tag", return_value=SHA_A):
            self.assertEqual(cp.verify([self.pin()], None), [])

    def test_mismatched_sha_fails(self):
        with mock.patch.object(cp, "resolve_tag", return_value=SHA_B):
            errors = cp.verify([self.pin()], None)
        self.assertEqual(len(errors), 1)
        self.assertIn("resolves to", errors[0])

    def test_unpinned_ref_fails_without_network(self):
        with mock.patch.object(cp, "resolve_tag", side_effect=AssertionError("no network")):
            errors = cp.verify([self.pin(ref="v7")], None)
        self.assertIn("not pinned", errors[0])

    def test_missing_version_fails_without_network(self):
        with mock.patch.object(cp, "resolve_tag", side_effect=AssertionError("no network")):
            errors = cp.verify([self.pin(version=None)], None)
        self.assertIn("no parseable version comment", errors[0])

    def test_resolution_cached_per_action_and_tag(self):
        calls = []

        def fake(action, tag, token):
            calls.append((action, tag))
            return SHA_A

        with mock.patch.object(cp, "resolve_tag", side_effect=fake):
            cp.verify([self.pin(), self.pin()], None)
        self.assertEqual(calls, [("actions/checkout", "v7.0.0")])


if __name__ == "__main__":
    unittest.main()
