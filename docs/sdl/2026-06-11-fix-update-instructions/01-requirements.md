# 01 — Requirements

## Summary

Correct the "how to update" instructions across the repo. The prior cycle (`2026-06-11-reduce-human-interaction`) bumped the plugin to 0.3.0, which surfaced that `git pull` alone does not deliver new skills to Claude Code: its plugin marketplace is a local clone that does not auto-refresh. Copilot, which reads the symlinked skills, is current immediately after `git pull`; Claude Code additionally needs `/plugin marketplace update savioke` and a reload. This cycle documents that in `scripts/install.sh`, `docs/developer-guide.md`, and `Plan.md`, and corrects `Plan.md`'s inaccurate claim that "every tool sees the new version immediately."

## Scope

In scope: documentation/instruction edits to `scripts/install.sh` (printed footer), `docs/developer-guide.md`, and `Plan.md`. Out of scope: any behavioral change to `install.sh` (no new logic, fetch, or privileged operation); enabling marketplace auto-update (considered and declined — it is the plugin-channel analogue of baseline:B5 and is unverified for local marketplaces).

## Assets touched <!-- SR-1 -->

Documentation and one workstation script's printed text. Standing assets per `baseline.md`; `install.sh` is a baseline:B3 workstation script, touched only in its heredoc-printed text.

## Trust boundaries crossed <!-- SR-2 -->

None new. Exposure model per `baseline.md`.

## Data classification <!-- SR-1 -->

None new. Public repo, no secrets — per `baseline.md`.

## External inputs introduced <!-- SR-2 -->

None.

## Security requirements <!-- SR-3, SR-4 -->

- The `install.sh` edit must not add any new network fetch, privileged operation, or executable logic — printed text and comments only — so baseline:B3's disposition stays unchanged.
- The documented procedure must be accurate: `git pull` updates Copilot immediately; Claude Code also requires `/plugin marketplace update savioke` + reload.

## Related prior cycles

- `2026-06-11-reduce-human-interaction` — bumped the plugin to 0.3.0; this cycle documents how that bump actually reaches each tool.

## Carried-forward residual risks

None. The related cycle's only residual risk (R1, PR-review enforcement) was dispositioned `accept`, not deferred.
