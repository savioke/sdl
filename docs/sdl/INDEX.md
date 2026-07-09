# SDL Cycle Index

| Slug | Branch | PR | Status | Created | Summary |
|------|--------|----|--------|---------|---------|
| 2026-06-10-adopt-sdl-governance | adopt-sdl-governance | — | merged | 2026-06-10 | Adopt SDL governance for the sdl repo itself (dogfooding): self-gate workflow, repo baseline, first cycle. |
| 2026-06-10-pin-actions-sha | pin-actions-sha | — | merged | 2026-06-10 | Pin third-party actions to commit SHAs + Dependabot; closes baseline:B6. |
| 2026-06-11-reduce-human-interaction | reduce-human-interaction | 8 | merged | 2026-06-11 | Reduce human checkpoints in the SDL process: remove the sign-off boilerplate, re-point affected 62443 evidence to PR/CI/git, and have skills advance through the cycle without asking permission. |
| 2026-06-11-fix-update-instructions | fix-update-instructions | 9 | merged | 2026-06-11 | Correct the update instructions: `git pull` makes Copilot current but Claude Code's local-clone marketplace also needs `/plugin marketplace update`. |
| 2026-06-11-sdl-report-viewer | sdl-report-viewer | 10 | merged | 2026-06-11 | Lightweight localhost HTML viewer for a repo's docs/sdl cycles; viewer lives in the governance install, nothing added to consumer repos. |
| 2026-07-09-actions-3e1200532a | dependabot/github_actions/actions-3e1200532a | 11 | merged | 2026-07-09 | Dependabot bump: actions/checkout v6.0.3→v7.0.0, actions/setup-python v6.2.0→v6.3.0; retroactive docs, SHAs verified upstream. |
| 2026-07-09-dep-update-tier | dep-update-tier | 12 | merged | 2026-07-09 | Tiered dependency-update process: routine-tier dep-update.md records with a fail-closed diff classifier, check_pins SHA↔tag verification, escalation to full cycles for majors. |
| 2026-07-09-marketplace-rename | marketplace-rename | 13 | review | 2026-07-09 | Rename the Claude Code plugin marketplace from `savioke` to `relay` following the company rename. |
