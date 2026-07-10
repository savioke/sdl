# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** Claude Code (Fable 5) + Joe Cooper
- **Date:** 2026-07-09
- **Diff range:** main..split-marketplace

## Checks performed <!-- SVV-1, SVV-2 -->

### Plugin self-containment (this cycle's SR: nothing under `plugins/sdl/` references outside it)

- **Finding:** pass. All former symlinks replaced by real files; `find plugins/sdl -type l` is empty; skill tooling references are `<plugin-root>`-relative; `template_dir()` resolves file-adjacent first.
- **References:** `plugins/sdl/skills/*/SKILL.md`, `plugins/sdl/lib/validate.py:224`

### Skill / validator path changes still gate as code

- **Finding:** pass. `is_code()` matches on `"skills" in p.parts` regardless of prefix, so `plugins/sdl/skills/*.md` still gates; confirmed by the 78-test suite passing unmodified after the move.
- **References:** `plugins/sdl/lib/validate.py:52`

### New shell in workstation scripts

- **Finding:** pass. Diff to `install.sh`/`sync-to-repo.sh` is target paths and one registration argument; no new fetch, privilege, or control flow. `shellcheck` clean.
- **References:** `scripts/install.sh:40,55-62`, `scripts/sync-to-repo.sh:52`

### Manifest integrity (marketplace + plugin)

- **Finding:** pass with an unverified item (R1). `claude plugin validate` passes on both `plugins/sdl` and the marketplace repo; the manifest `source` points at the public canonical repo/path/ref. What could not be verified locally: end-to-end marketplace install (`/plugin install sdl@relay`) — both repos must be pushed first, and validating from a live session would have mutated the maintainer's plugin state mid-change.
- **References:** `relay-plugin-marketplace:.claude-plugin/marketplace.json`

**Not applicable (no code in these areas):** SQL, HTTP endpoints, deserialization, crypto, file I/O with user paths, external service calls, logging of user data, auth surfaces.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

- `python -m unittest` (78 tests) — pass at new layout.
- `python plugins/sdl/lib/gen_index.py --check` — INDEX current.
- `shellcheck scripts/*.sh` — clean.
- `claude plugin validate` — plugin and marketplace both pass (plugin `author` warning fixed this cycle).
- `python plugins/sdl/lib/validate.py --base main` — run pre-PR; see R1 for the one check that needs the push.

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1 | End-to-end `sdl@relay` install untested until both repos are pushed; a `git-subdir` materialization surprise (e.g. path handling) would break Claude-only installs at first use. Test immediately after push: remove `relay-sdl`, add `relay`, install, invoke a skill. | medium | mitigate-later | next cycle if broken; close in PR notes if the post-push test passes |
| R2 | Marketplace manifest ungated outside this repo (baseline:B7): accepted standing risk, revisit triggers recorded in baseline. | medium | accept | baseline:B7 |
