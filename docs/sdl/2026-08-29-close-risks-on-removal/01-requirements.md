# 01 — Requirements

<!-- SR-1: Product security context. SR-2: Threat model inputs. -->

## Summary

Removing code closes the risk that code carried, but the skills had no rule saying so, and the records they produced showed it: a deleted feature kept a residual-risk row with a "if this comes back" caveat, and functionality that moved to another repo kept a note about what the receiving project would need to do. Neither can ever be closed here — the code they describe will never be fixed, because it is gone — so they accumulate as permanent noise in `open_risks.py` output and in every later cycle's carry-forward interview. This cycle teaches `sdl-review`, `sdl-threat-model`, `sdl-spec`, and `sdl-baseline` one rule: code that no longer exists in this repo is recorded once, in the past tense, and then it is done. The same PR fixes an unrelated flake in `scripts/test_check_release.py`, where git's background housekeeping could still be writing inside `.git` when the fixture's temp directory was removed.

## Scope

In scope: the removal-closure convention across the four cycle skills and the `01`/`02`/`04`/`baseline` templates, one bullet documenting it in `docs/developer-guide.md`, and the `GitFixture` teardown fix in `scripts/test_check_release.py`.

Out of scope: `open_risks.py` and `validate.py` are unchanged. Closure rides the existing `carry_forward:` mechanism, which already drops claimed items from the open list, so no new disposition value and no new parsing. Historical cycle documents are not amended — the whole point is that history stays intact while the *current* register describes only current risks.

## Assets touched <!-- SR-1 -->

The skill definitions under `plugins/sdl/skills/` and the cycle templates under `plugins/sdl/templates/` — the agent-facing instructions the gate treats as code, and the artifacts every consumer repo's audit trail is built from. No runtime code, credentials, or data.

## Trust boundaries crossed <!-- SR-2 -->

None new. Exposure model per `docs/sdl/baseline.md`: this is a docs-and-skills repo whose only privileged surface is CI, and the skill files are the "executable spec" surface the baseline already records.

## Data classification <!-- SR-1 -->

Public. Everything changed here ships in a public plugin.

## External inputs introduced <!-- SR-2 -->

None.

## Security requirements <!-- SR-3, SR-4 -->

1. The convention must not lose evidence. A closed risk keeps a durable record: the one-line past-tense entry in the closing cycle, plus the untouched original cycle documents.
2. Closure must be mechanically visible — an item is off the open list because a cycle claimed it in `carry_forward:`, not because a human stopped mentioning it.
3. Closure applies only to code actually gone from this repo's diff. Code that merely moved within the repo, or was disabled rather than deleted, still carries its risk.
4. The test fixture must not weaken what it asserts: the flake fix stops git housekeeping from racing teardown, it does not relax any check.

## Related prior cycles

- `2026-07-09-faster-maybe` — same goal from the other direction: cut per-cycle overhead so small changes don't accumulate ceremony.
- `2026-08-03-release-process` — owns `scripts/check_release.py` and its tests, which this cycle touches.

## Carried-forward residual risks

None. `open_risks.py` lists twelve open items; all are verification-on-first-real-use deferrals belonging to other cycles, and none is addressed by this change.
