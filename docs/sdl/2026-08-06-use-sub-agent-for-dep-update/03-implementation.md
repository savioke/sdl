# 03 — Implementation

<!-- SI-1: Security implementation review. SI-2: Secure coding standards. -->

## Summary of changes

Three frontmatter keys on `sdl-dep-update` (`model: sonnet`, `context: fork`, `background: true`) move the routine-tier record out of the operator's conversation and into a backgrounded subagent on a smaller model. Two instruction edits adapt the skill to that context: the triage step now stops and names `sdl-spec` instead of invoking an interview skill it cannot run detached, and a new step 5 states that the skill's final message *is* the report and specifies what it must contain. Supporting changes are the plugin version bump to 1.2.0, its `CHANGELOG.md` entry, and a note in the developer guide so Dependabot-PR users expect a task notification rather than inline output. No executable surface other than the skill file changed: `plugins/sdl/lib/`, `plugins/sdl/templates/`, `.github/`, and `scripts/` have zero diff lines.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Report step requires naming which checks ran, what each returned, and anything unverified — so the notification is checkable against the record rather than asserting success. Human read-before-push attestation preserved and now documented alongside the new invocation behavior. | `plugins/sdl/skills/sdl-dep-update/SKILL.md:67-73`, `docs/developer-guide.md:80,82` | this branch |
| T2 | Triage step stops and reports the trigger, names `sdl-spec` as the operator's next step, and explicitly forbids running it from the detached agent. | `plugins/sdl/skills/sdl-dep-update/SKILL.md:31-34` | this branch |

## Secure coding practices applied <!-- SI-2 -->

- **Fail-safe escalation.** The escalation path was changed in the direction that fails closed: the agent stops and surfaces rather than attempting a degraded interview. The prior instruction would have failed in an unspecified way from a background agent.
- **No privilege or capability increase.** The skill declares no `allowed-tools` before or after, reads the same inputs, writes the same artifacts, and runs against the same checkout with the same workstation privileges.
- **Gate untouched.** `validate.py` and both workflows have zero diff lines, so no consumer's PR outcome can change as a result of this cycle — verified by `git diff --stat` over `plugins/sdl/lib/`, `plugins/sdl/templates/`, `.github/`, and `scripts/`.
- **Graceful degradation across agents.** The three new keys are ignored by runners that do not implement them, so Codex, Antigravity, and Copilot continue to run the skill inline with no behavior change and no error.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None. No manifest or lockfile in this repo changed. `plugins/sdl/.claude-plugin/plugin.json` version 1.1.0 → 1.2.0 is this plugin's own release identifier, not a dependency bump; the validator remains standard-library only per the baseline's standing requirements.

## Deviations from spec or threat model

None. One scope decision is worth recording rather than leaving implicit: `effort:` was deliberately *not* set, so the skill runs at Sonnet's default. Changing execution context and model tier in one cycle is already two variables; adding a third would make a quality regression hard to attribute. `effort` remains available as a separate dial once this has run against real Dependabot PRs.
