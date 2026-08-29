# 03 — Implementation

<!-- SI-1: Security implementation review. SI-2: Secure coding standards. -->

## Summary of changes

`sdl-review` gains two bullets that forbid opening a residual risk for code the diff deletes and require closure instead: one past-tense line in a new "Risks closed by removal" section of `04-verification.md`, plus the item's ref added to `carry_forward:` so `open_risks.py` stops listing it, plus dropping the row from `baseline.md` for a `B` item. `sdl-threat-model` refuses removed code a stanza, an out-of-scope line, or a future-cycle signpost, and closes obsolete inherited threats in one line. `sdl-spec` gains a fourth carry-forward triage answer for "the code it applied to was deleted". `sdl-baseline` skips migrating items whose code is already gone. The `01`, `02`, `04`, and `baseline.md` templates carry the same rule as authoring comments, and `docs/developer-guide.md` states it once for humans. Separately, `scripts/test_check_release.py`'s `GitFixture` disables git's auto-gc and maintenance and tolerates a teardown race, fixing an intermittent `OSError: Directory not empty: .git` in the `release` job.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Closure is scoped to code "this diff deletes" and requires two correlated, reviewable edits — the past-tense line and the `carry_forward:` ref — with history left unamended. `open_risks.py`/`validate.py` untouched. | `plugins/sdl/skills/sdl-review/SKILL.md:104`, `:111`; `plugins/sdl/templates/docs-sdl/04-verification.md:51` | 08d87dd |
| T2 | The single closing line is the handoff record; the receiving repo owns the risk from there. No tracking of another repo's obligations is kept here. | `plugins/sdl/skills/sdl-review/SKILL.md:105`; `plugins/sdl/skills/sdl-threat-model/SKILL.md:84`; `plugins/sdl/templates/docs-sdl/04-verification.md:57` | 08d87dd |

## Secure coding practices applied <!-- SI-2 -->

- Evidence preservation: no instruction anywhere in the change permits editing or deleting a prior cycle's documents. The templates and `developer-guide.md` say so explicitly, alongside the pre-existing "don't delete cycle folders, ever" rule.
- No new mechanism: closure reuses `carry_forward:`, so the gate, the open-list arithmetic, and the artifact requirements are unchanged and no new parser accepts new input.
- Test integrity: the fixture fix disables git housekeeping (`scripts/test_check_release.py:262-263`) and tolerates a lost teardown race (`:255`); no assertion, timeout, or check was relaxed. 55/55 tests pass locally.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None. Standard library only; `tempfile.TemporaryDirectory(ignore_cleanup_errors=...)` requires Python 3.10+, and CI pins `python-version: '3.x'`.

## Deviations from spec or threat model

None. T2's mitigation is partial by design, as `02` states; it is carried as R1 in `04`.
