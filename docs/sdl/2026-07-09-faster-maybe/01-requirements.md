# 01 — Requirements

<!-- SR-1: Product security context. SR-2: Threat model inputs. -->

## Summary

Cut the per-cycle overhead of the SDL process so small changes don't feel like bureaucracy — the failure mode being avoided is developers hesitating to make changes, which is worse for security than slow paperwork. Two parts: (1) deterministic tools for the mechanical steps every cycle repeats — `lib/new_cycle.py` scaffolds a cycle folder (slug normalization, template copy, `.sdl-meta.yml`) and `lib/gen_index.py` regenerates `docs/sdl/INDEX.md` from cycle metadata — replacing agent tool-call loops with tested scripts; (2) a single-pass authoring fast path in the flow skills: when the change is small and already implemented, one skill invocation authors all four artifacts from the diff with no interview, instead of three sequential skill passes. Motivated by cycle `2026-07-09-marketplace-rename`, where a ~22-line cosmetic diff took several minutes of process. The evidence bar does not move: same four artifacts, same validator, same gate.

## Scope

In scope: `lib/new_cycle.py` and `lib/gen_index.py` with unit tests; edits to `skills/sdl-spec/SKILL.md`, `skills/sdl-review/SKILL.md`, and `skills/sdl-dep-update/SKILL.md` to use the tools and describe the single-pass fast path; plugin version bump so installs pick up the changed skills.

Out of scope: any change to `lib/validate.py` or the gate's pass/fail behavior; a third "micro" cycle class (considered and deferred — revisit only if a fast full cycle is still too slow in practice); addressing dep-update-tier R2 (`check_pins` in `sdl-validate.yml`), which remains deferred at its source cycle.

## Assets touched <!-- SR-1 -->

New integrity assets `lib/new_cycle.py` and `lib/gen_index.py` — they run on developer workstations and in agent sessions, and they write files into consumer repos (`docs/sdl/`). Skill instructions (baseline:B2 assets) in `skills/`. Standing assets per `baseline.md`.

## Trust boundaries crossed <!-- SR-2 -->

This repo → developer workstation (existing boundary per `baseline.md`): the new scripts execute with developer privileges in consumer repos, taking the git branch name — text an arbitrary PR author can choose — as input to filesystem paths.

## Data classification <!-- SR-1 -->

None new. Public repo, no secrets — per `baseline.md`.

## External inputs introduced <!-- SR-2 -->

The git branch name (attacker-influenceable in fork/PR contexts) becomes input to `new_cycle.py` slug/path construction. `gen_index.py` consumes cycle-folder markdown/YAML content, which is repo-controlled but written by prior agent sessions.

## Security requirements <!-- SR-3, SR-4 -->

- Both tools stay Python standard-library only (baseline standing requirement — no dependency supply chain).
- `new_cycle.py` slug normalization must make path traversal impossible by construction (output restricted to `[a-z0-9-]`), and the tool must refuse to overwrite an existing cycle folder. Unit-tested.
- `gen_index.py` must write only `docs/sdl/INDEX.md`, produce deterministic output (stable ordering), and not let cycle-file content break the generated table (e.g. `|` in summaries).
- The single-pass fast path must produce the same four artifacts to the same standard — it compresses orchestration, not evidence. Skill wording must not license skipping checks; `validate.py` is unchanged and still gates.
- Skill edits are baseline:B2 assets: gated as code by the validator, reviewed in the PR diff.

## Related prior cycles

- `2026-06-11-reduce-human-interaction` — same motivation (remove process friction) and same skill files; established the "proceed without permission-seeking" principle this cycle extends to single-pass authoring.
- `2026-07-09-dep-update-tier` — precedent for sizing process to change shape; its motivation section records the boilerplate cost this cycle attacks for full cycles.

## Carried-forward residual risks

None taken on. `2026-07-09-dep-update-tier` R2 (consumers can silently skip `check_pins`; disposition: defer) is out of scope here — it concerns `sdl-validate.yml`, which this cycle does not touch. It remains open at its source cycle.
