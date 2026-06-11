# 04 — Verification

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-06-11
- **Diff range:** origin/main..HEAD (`fix-update-instructions`)

## Checks performed <!-- SVV-1, SVV-2 -->

### Build, CI, and supply chain

- **Finding:** The `scripts/install.sh` change is confined to the `cat` heredoc footer printed to the user — no new CI step, network fetch, install logic, or privileged operation. baseline:B3 disposition unchanged. `shellcheck` passes (added lines are literal heredoc content). The documented procedure is accurate: `git pull` updates Copilot's symlinked skills immediately; Claude Code's local-clone marketplace does not auto-refresh and additionally needs `/plugin marketplace update savioke` + reload.
- **References:** `scripts/install.sh` "To update later" block; `docs/developer-guide.md` update line; `Plan.md` "Updates:" line.

### Secrets

- **Finding:** No secrets, keys, or tokens introduced. Verified across the full diff.
- **References:** `git diff origin/main` (3 files: one script footer, two docs).

**Not applicable (no code in these areas):** input handling, persistence, network/transport, authn/authz, cryptography, logging, concurrency, dependencies, frontend, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

No SAST/SBOM applies — no code logic or dependencies changed. Repo CI (`self-check.yml`: validator unit tests, `shellcheck`, structure) and the SDL self-gate run on the PR; `shellcheck` covers the edited `install.sh`.

## Residual risks <!-- DM-1 -->

None. Documentation/printed-text change with no new execution surface.
