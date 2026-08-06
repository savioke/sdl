# 01 — Requirements

<!-- SR-1: Product security context. SR-2: Threat model inputs. -->

## Summary

`sdl-dep-update` gains frontmatter that runs it as a backgrounded subagent on Sonnet (`context: fork`, `background: true`, `model: sonnet`) instead of expanding inline into the operator's conversation on the primary model. The routine tier exists to make dependency updates cheap; authoring the record inline still spent primary-model context on a lockfile bump and blocked the operator's turn, which was most of what made the cheapest tier of work feel expensive. Two instructions change to match the detached execution context.

## Scope

In scope: frontmatter and two instruction edits in `plugins/sdl/skills/sdl-dep-update/SKILL.md`; plugin version bump 1.1.0 → 1.2.0; `CHANGELOG.md` entry; a note in `docs/developer-guide.md` describing the new invocation behavior.

Out of scope, deliberately: the same treatment for `sdl-review` — a fresh-context fork changes what the reviewer knows, which wants measurement rather than reasoning; `sdl-spec` and `sdl-threat-model`, which are interview-shaped and cannot run detached; moving triage, the updates table, or the advisory lookup into deterministic tooling (separate cycles); and refreshing `baseline.md`'s agent list, which still names Claude Code / Copilot only.

## Assets touched <!-- SR-1 -->

`plugins/sdl/skills/sdl-dep-update/SKILL.md` — a baseline integrity asset (agent-executed instructions, `baseline:B2`, whose stated revisit trigger is "any skill change"). No other executable surface: `validate.py`, the templates, and both workflows are untouched. `plugin.json`'s `version` is what the release channel resolves; `CHANGELOG.md` and `docs/developer-guide.md` are documentation.

## Trust boundaries crossed <!-- SR-2 -->

None new. Exposure model per baseline: skill instructions execute on developer workstations and in CI with the invoking developer's privileges. That is unchanged — the fork runs in the same place, with the same privileges, against the same repo checkout.

What changes *inside* that existing boundary is who interprets the instructions and whether a human observes it happening: a different model authors the record, detached from the operator's attention. That is a supervision property of an attestation artifact rather than a new boundary, and it is this cycle's principal threat-model input.

## Data classification <!-- SR-1 -->

Unchanged; none. No secrets, no PII, no customer data — public repo per baseline. The artifacts the skill writes (`dep-update.md`, `.sdl-meta.yml`) are public audit records, as before.

## External inputs introduced <!-- SR-2 -->

None. The forked skill reads what the inline one read: the diff against the merge base, manifests and lockfiles, cycle templates, and the upstream advisory and release-note lookups the skill already performed. No new endpoint, consumer, or runtime input.

## Security requirements <!-- SR-3, SR-4 -->

- The record remains an honest attestation: no box checked for a check that was not run. Detachment must not weaken this.
- The human attestation step is preserved — the operator reads the record before pushing (`docs/developer-guide.md`), and `validate.py` gates the PR regardless of which agent authored it.
- Escalation must not silently degrade: a triage trigger that fires stops the routine tier and surfaces, rather than being swallowed by a background agent.
- The change is inert on agents that do not implement the frontmatter, so consumers on Codex, Antigravity, or Copilot see no behavior change.
- Gate behavior is unchanged: `validate.py` and both workflows have zero diff lines this cycle.

## Related prior cycles

- `2026-07-09-dep-update-tier` — introduced the routine tier, this skill, and the `class: dependency-update` validator path this change runs inside.
- `2026-07-09-faster-maybe` — the prior pass at moving mechanical work out of the model in these same skills (`new_cycle.py`, `gen_index.py`, the `sdl-spec` fast path). Same intent, different lever.

## Carried-forward residual risks

None. No open `defer` / `mitigate-later` item in a related cycle is addressed here; `dep-update-tier:R2` (consumers can skip `check_pins`) is untouched and remains open in its source cycle.
