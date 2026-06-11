# 01 — Requirements

## Summary

Reduce the human checkpoints in the SDL process. Three changes: (1) remove the boilerplate Sign-off checklist from `templates/docs-sdl/04-verification.md` — commit history and PR approval already record who is responsible; (2) re-point the four IEC 62443 mapping rows that cited the sign-off checklist (SM-2, SR-5, SD-3, DM-2) plus the audit-report bullet to PR review / CI / git-history evidence; (3) add a "Proceeding through the cycle" principle to all three flow skills (`sdl-spec`, `sdl-threat-model`, `sdl-review`) so the agent advances through SDL steps as a normal part of development instead of asking permission for each, stopping only for genuine open questions. Plugin bumped 0.2.0 → 0.3.0 so Claude Code picks up the changed skills.

## Scope

In scope: edits to the three skill `SKILL.md` files, the `04-verification.md` template, `docs/62443-mapping.md`, `docs/developer-guide.md`, `Plan.md`, and the two plugin-version manifests. Out of scope: any change to the CI validator (`lib/validate.py`), the reusable workflow, or the `@v1` tag — consumer-facing behavior is unchanged. No change to skill *trigger* descriptions (frontmatter).

## Assets touched <!-- SR-1 -->

Standing integrity assets per `baseline.md`: the skill instructions under `skills/` (executed by agents — see baseline:B2) and the artifact templates. No runtime, data, or secret assets.

## Trust boundaries crossed <!-- SR-2 -->

None new. Exposure model per `baseline.md`. The edited skill `.md` files cross the existing **repo → developer/CI agent** boundary (baseline:B2); the version bump crosses the **repo → Claude Code plugin marketplace** distribution path.

## Data classification <!-- SR-1 -->

None new. Public repo, no secrets — per `baseline.md`.

## External inputs introduced <!-- SR-2 -->

None. No new endpoints, inputs, or runtime surfaces.

## Security requirements <!-- SR-3, SR-4 -->

- Removing the sign-off checklist must not remove an actual control. The review and responsibility evidence it nominally represented must still exist elsewhere — PR approval, CI pass, and commit/merge history — and the 62443 mapping must point there instead. No 62443 practice may be left without evidence.
- The autonomy principle must not let the agent fabricate threat content or skip genuine human input. Advancing without asking is bounded by existing skill guardrails: preconditions that halt on TBD requirements or a missing cycle, "don't make up components", "ask one or two pointed questions if architecture is unclear", and "don't propose mitigations the team hasn't agreed to". Transparency is preserved — each skill still reports what it wrote.
- The plugin version bump must be applied in both manifests (`plugin.json` and `marketplace.json`) so the two stay in sync.

## Related prior cycles

- `2026-06-10-adopt-sdl-governance` — established the SDL process, skills, templates, and 62443 mapping this cycle edits.

## Carried-forward residual risks

None. No deferred or mitigate-later residual risks open in related cycles.
