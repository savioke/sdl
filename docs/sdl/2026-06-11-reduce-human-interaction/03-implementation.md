# 03 — Implementation

## Summary of changes

Documentation- and instruction-only change, no runtime code. Removed the Sign-off checklist from `templates/docs-sdl/04-verification.md`; re-pointed four IEC 62443 evidence rows (SM-2, SR-5, SD-3, DM-2) and the audit-report bullet in `docs/62443-mapping.md` from the sign-off checklist to PR approval / "Checks performed" / threat-model review / git merge history; added a "Proceeding through the cycle" section to all three flow skills (`sdl-spec`, `sdl-threat-model`, `sdl-review`) and reframed their handoff report lines from passive ("will be filled") to active ("you'll fill"); dropped the now-stale sign-off instruction from `sdl-review` and the "sign off the checkboxes" step from `docs/developer-guide.md`; softened the "sign-off" wording in `Plan.md`. Bumped the plugin version 0.2.0 → 0.3.0 in both `plugins/sdl/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Responsibility/review evidence re-pointed to PR approval + git history, not a self-attested checkbox | `docs/62443-mapping.md:31,45,53,78,88` | pending (this branch) |
| T1 | Independent, non-bypassable gate left unchanged — validator still requires all four non-template artifacts | `lib/validate.py` (unchanged by this diff) | n/a |
| T1 | Autonomy principle explicitly scoped to *writing artifacts*, stop-to-ask for genuine open questions | `skills/sdl-spec/SKILL.md` "Proceeding through the cycle"; same section in `skills/sdl-threat-model/SKILL.md` and `skills/sdl-review/SKILL.md` | pending (this branch) |
| T1 | Existing guardrails (halt on TBD, don't fabricate components, ask when unclear) untouched | `skills/*/SKILL.md` (preconditions and tone sections unchanged) | n/a |

## Secure coding practices applied <!-- SI-2 -->

- **Build / CI / supply chain:** No new CI steps, actions, or install-script network fetches. Plugin version bumped consistently in both manifests so distribution stays in sync (verified both read `0.3.0`). Skill-instruction edits (baseline:B2) are scoped instruction text that adds no agent authority beyond writing SDL artifacts; the independent PR + CI gate the agent cannot bypass remains the human checkpoint.
- **Secrets:** Confirmed no secrets, keys, or tokens introduced in any edited file.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None. Validator remains standard-library only per baseline.

## Deviations from spec or threat model

None. Implementation matches `01-requirements.md` and `02-threat-model.md`. Note: skill changes reach installed agents only after `git pull` + `claude plugin` update to 0.3.0 — expected distribution lag, covered by the version bump.
