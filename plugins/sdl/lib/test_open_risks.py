#!/usr/bin/env python3
"""Tests for open_risks. Stdlib only; fixtures are temp cycle folders."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import open_risks as orisk  # noqa: E402

VERIFICATION = """\
# 04 — Verification

## Checks performed

| Category | Result |
|----------|--------|
| R2D2     | not a risk row |

## Residual risks

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | unsigned releases | medium | mitigate-later | next release |
| R2  | consumers can skip check_pins | low | defer | future cycle |
| R3  | shape-matching is brittle | low | accept | — |
"""

STUB = """\
## Residual risks

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  |             |          | accept | defer | mitigate-later |  |
"""


def meta(branch="b", status="review", carry="[]"):
    return f"slug: s\nbranch: {branch}\nstatus: {status}\ncarry_forward: {carry}\n"


class ParseRisks(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.cycle = Path(self._tmp.name) / "2026-01-01-x"
        self.cycle.mkdir()

    def write(self, text=VERIFICATION):
        (self.cycle / "04-verification.md").write_text(text, encoding="utf-8")

    def test_risk_rows_are_read_with_their_fields(self):
        self.write()
        risks = orisk.parse_risks(self.cycle, "review")
        self.assertEqual([r.rid for r in risks], ["R1", "R2", "R3"])
        self.assertEqual(risks[0].severity, "medium")
        self.assertEqual(risks[0].disposition, "mitigate-later")
        self.assertEqual(risks[0].target, "next release")
        self.assertEqual(risks[0].ref, "2026-01-01-x:R1")

    def test_other_tables_are_not_mistaken_for_the_register(self):
        # "R2D2" is not a risk ID, and that table has the wrong shape anyway.
        self.write()
        self.assertNotIn("R2D2", [r.rid for r in orisk.parse_risks(self.cycle, "review")])

    def test_template_scaffolding_is_not_a_risk(self):
        self.write(STUB)
        self.assertEqual(orisk.parse_risks(self.cycle, "review"), [])

    def test_missing_file_is_not_an_error(self):
        self.assertEqual(orisk.parse_risks(self.cycle, "review"), [])

    def test_disposition_is_matched_case_insensitively(self):
        self.write(VERIFICATION.replace("mitigate-later", "Mitigate-Later"))
        self.assertEqual(orisk.parse_risks(self.cycle, "review")[0].disposition,
                         "mitigate-later")


class ParseMeta(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.cycle = Path(self._tmp.name) / "c"
        self.cycle.mkdir()

    def write(self, text):
        (self.cycle / ".sdl-meta.yml").write_text(text, encoding="utf-8")

    def test_empty_inline_list_claims_nothing(self):
        self.write(meta())
        self.assertEqual(orisk.parse_meta(self.cycle), ("review", set()))

    def test_inline_list_is_parsed(self):
        self.write(meta(carry="[baseline:B5, 2026-01-01-x:R1]"))
        status, claimed = orisk.parse_meta(self.cycle)
        self.assertEqual(claimed, {"baseline:B5", "2026-01-01-x:R1"})

    def test_block_list_is_parsed(self):
        self.write("status: merged\ncarry_forward:\n  - baseline:B7\n  - 2026-01-01-x:R2\n")
        status, claimed = orisk.parse_meta(self.cycle)
        self.assertEqual(status, "merged")
        self.assertEqual(claimed, {"baseline:B7", "2026-01-01-x:R2"})

    def test_missing_meta_is_not_an_error(self):
        self.assertEqual(orisk.parse_meta(self.cycle), ("unknown", set()))


class Collect(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.sdl = Path(self._tmp.name)

    def cycle(self, name, verification=VERIFICATION, carry="[]"):
        d = self.sdl / name
        d.mkdir()
        (d / "04-verification.md").write_text(verification, encoding="utf-8")
        (d / ".sdl-meta.yml").write_text(meta(carry=carry), encoding="utf-8")
        return d

    def open_refs(self):
        risks, claimed = orisk.collect(self.sdl)
        return {r.ref for r in risks
                if r.disposition in orisk.OPEN_DISPOSITIONS and r.ref not in claimed}

    def test_deferred_and_mitigate_later_are_open_accepted_is_not(self):
        self.cycle("2026-01-01-x")
        self.assertEqual(self.open_refs(), {"2026-01-01-x:R1", "2026-01-01-x:R2"})

    def test_a_claimed_risk_is_no_longer_open(self):
        self.cycle("2026-01-01-x")
        self.cycle("2026-02-02-y", verification="# nothing\n",
                   carry="[2026-01-01-x:R1]")
        self.assertEqual(self.open_refs(), {"2026-01-01-x:R2"})

    def test_a_later_cycle_can_claim_across_cycles_in_any_order(self):
        # The claiming cycle sorts before the claimed one by name.
        self.cycle("2026-02-02-y")
        self.cycle("2026-01-01-x", verification="# nothing\n",
                   carry="[2026-02-02-y:R2]")
        self.assertEqual(self.open_refs(), {"2026-02-02-y:R1"})

    def test_a_stray_file_in_docs_sdl_is_ignored(self):
        self.cycle("2026-01-01-x")
        (self.sdl / "INDEX.md").write_text("| a | b |\n", encoding="utf-8")
        self.assertEqual(len(self.open_refs()), 2)


class Truncate(unittest.TestCase):
    def test_short_strings_are_untouched(self):
        self.assertEqual(orisk.truncate("abc", 10), "abc")

    def test_long_strings_are_elided(self):
        out = orisk.truncate("a" * 50, 10)
        self.assertEqual(len(out), 10)
        self.assertTrue(out.endswith("…"))


if __name__ == "__main__":
    unittest.main()
