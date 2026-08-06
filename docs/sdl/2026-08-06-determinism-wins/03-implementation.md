# 03 — Implementation

<!-- SI-1: Security implementation review. SI-2: Secure coding standards. -->

## Summary of changes

Three new stdlib-only tools under `plugins/sdl/lib/`. `dep_facts.py` classifies
a dependency diff (exit 0 routine, exit 2 escalate with the trigger named) and
generates the record's Updates table from that diff; `open_risks.py` reports the
residual risks earlier cycles left open, subtracting those a later cycle claimed
in `carry_forward:`; `cycle_stamp.py` fills the reviewer, date, and diff range in
`04-verification.md` and prints the per-file commit SHAs for `03`. `PIN_LINE_RE`
in `validate.py` gained a `version` capture group wrapping its existing `major`
group — additive, matching exactly the same strings — so a record's versions and
the gate's check read the same parse. Three skills now call the tools instead of
describing the work in prose. This repo's `self-check.yml` switched from a
hand-listed test set to discovery and smoke-runs `--help` for every tool. No
check in `validate.py` changed, so no previously-passing PR can fail.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Both writers are bounded and fail loudly: the table writer replaces only the rows between the header separator and the first non-table line and raises on a missing anchor; the stamper rewrites three labelled lines with `count=1` and reports any label it could not find, exiting non-zero. Neither appends; neither touches attestation. | `plugins/sdl/lib/dep_facts.py:146-162`, `plugins/sdl/lib/cycle_stamp.py:72-81,114-120` | this branch |
| T2 | Coverage limits are printed on every run, not left to documentation: changed manifests named under an explicit "does not parse ecosystem lockfiles", both non-mechanical triggers listed under "Still yours to verify", an explicit marker when no pin bumps were found, and `--write` refusing rather than writing an empty table. | `plugins/sdl/lib/dep_facts.py:61-64,165-181,221-223` | this branch |
| T3 | The regex fails closed — a `uses:` line not positively recognized as a SHA pin with a parseable version comment is rejected as a non-pin change and escalates. Sharing is confined to pin identification: the gate's record check reads the written markdown with separate code and never consults `PIN_LINE_RE`. Regex change is additive. | `plugins/sdl/lib/validate.py:88-95,102-131,150-178` | this branch |

## Secure coding practices applied <!-- SI-2 -->

- **Fail loudly, never silently.** Every writer's failure mode is an exception or
  a non-zero exit, not a no-op that reports success: a missing table header
  raises, a missing field line exits 1, and `--write` with nothing to write
  refuses and says why. A tool that quietly does nothing to an audit artifact is
  the worst available outcome, because it looks like it worked.
- **Never author an attestation.** No tool checks a Checks box, writes a Note, or
  touches a finding or residual-risk row. The generated content is fact read out
  of the diff; the attested content stays human.
- **Say what you did not check.** `report()` names the two triggers no classifier
  can see and lists manifests it cannot parse, on every run — the design answer
  to T2, in code rather than in a doc.
- **No new dependency surface.** All three are standard library only, per the
  baseline's standing requirement, and none opens a network connection.
- **Gate untouched.** `validate.py`'s checks are unchanged; the only edit is an
  additive capture group. Verified by the pre-existing validator suite passing
  unmodified, and by `git diff` over the checking functions.
- **CI that cannot silently skip.** Test discovery replaces a hand-listed module
  set, so a future `lib/test_*.py` runs without anyone remembering to add it.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None. No manifest or lockfile changed. All three tools are standard library
only. `plugins/sdl/.claude-plugin/plugin.json` 1.2.0 → 1.3.0 is this plugin's own
release identifier, not a dependency bump.

## Deviations from spec or threat model

None. Two scope decisions are worth recording rather than leaving implicit:

- **`dep_facts` does not parse ecosystem lockfiles.** Guessing a version for an
  audit record is worse than leaving the row blank, and each ecosystem's format
  is its own project. The tool names the manifests it saw and hands those rows
  back to the author. This is the deliberate cause of half of T2.
- **`--write` fills the Updates table but not the Checks boxes**, even though
  filling both would be faster. The boxes are the attestation the routine tier
  rests on; a tool that checks them would remove the only thing making the record
  evidence rather than a form.
