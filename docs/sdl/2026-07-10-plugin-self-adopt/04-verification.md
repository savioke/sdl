# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-07-10
- **Diff range:** 26a66c3 (main)..working tree, pre-commit

## Checks performed <!-- SVV-1, SVV-2 -->

### Command execution / external inputs (new shell script)

- **Finding:** verified. Target path argument validated as a git repo before any write (`plugins/sdl/lib/sync_to_repo.sh:27`); all expansions quoted; `SDL_REF` env var allowlisted before interpolation into generated YAML (`:19`) — functional test confirmed a newline-bearing value is rejected and `v1.2.3` accepted.
- **References:** `plugins/sdl/lib/sync_to_repo.sh:19,27`, `scripts/sync-to-repo.sh:5`

### File I/O with user-controlled paths

- **Finding:** verified. Writes are confined to the validated target repo (`.github/workflows/`, `docs/sdl/`); existing files never overwritten (`sync_to_repo.sh:36`, `:57`); template source checked to exist under the resolved plugin root before use (`:29`). Functional tests: scaffold from simulated plugin cache, idempotent re-run, non-git target refused.
- **References:** `plugins/sdl/lib/sync_to_repo.sh:27-29,36,49-51,57`

### CI / supply chain

- **Finding:** verified. Generated consumer workflow pins `savioke/sdl@v1` by default (`sync_to_repo.sh:45`); shellcheck coverage extended to the plugin's shell (`self-check.yml:43`); new script added to required-files structure check (`self-check.yml:70`). Skill-instruction change (agent-executable spec) is gated as code by `validate.py` — this cycle exists because of that gate.
- **References:** `plugins/sdl/lib/sync_to_repo.sh:45`, `.github/workflows/self-check.yml:43,70`, `plugins/sdl/skills/sdl-baseline/SKILL.md:12-22`

**Not applicable (no code in these areas):** persistence/SQL, deserialization, cryptography, network/transport, authn/authz, secrets, logging/PII, frontend, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

- `shellcheck scripts/*.sh plugins/sdl/lib/*.sh` — clean, run locally; enforced by `self-check.yml` on PR.
- `python -m unittest` suite (78 tests) — pass; `gen_index.py --check` current.
- No dependency changes, no SBOM delta.

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | Plugin-cache execution path tested against a simulated cache layout, not a published release: after 0.7.0 reaches `main` and the marketplace updates, run "initialize SDL in this repo" on a fresh repo end-to-end (same shape as split-marketplace R1, which this cycle closed). | low | mitigate-later | verify after release; next cycle if broken |
| R2  | T2's guard against unsolicited scaffolding is a prose precondition an agent follows probabilistically, not a code check. Accepted: the script cannot commit, misfires are visible in `git status`, and inherits baseline:B2 (skill-instruction integrity). Revisit if a misfire is ever observed. | low | accept | — |
