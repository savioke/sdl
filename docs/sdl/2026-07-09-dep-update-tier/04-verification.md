# 04 — Verification

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-07-09
- **Diff range:** main..HEAD (branch dep-update-tier)

## Checks performed <!-- SVV-1, SVV-2 -->

### Input handling (adversarial diff and record parsing)

- **Finding:** New parsers run against attacker-authored PR content in consumer CI. Verified: all regexes anchored, no nested quantifiers (`lib/validate.py:72-78`, `lib/check_pins.py:32-40`); pin-shape bypass attempts rejected (swapped `owner/repo`, trailing shell after version comment, comment-less pins, unpinned refs, non-pin lines — each pinned as a test in `lib/test_validate.py:246-315`); diff-header parsing cannot be spoofed by dash-shaped YAML content (`lib/validate.py:92-94`, test at `lib/test_validate.py:302-305`). Classifier fails closed on anything unrecognized (`lib/validate.py:116-134`); declaring the class on a non-qualifying diff hard-fails (`lib/validate.py:330-336`).
- **References:** as cited; 55 unit tests pass (`python3 -m unittest lib.test_validate lib.test_check_pins`).

### Network and transport (`check_pins.py`)

- **Finding:** Single outbound call type: `GET api.github.com/repos/<action>/commits/<tag>` via stdlib `urllib` — TLS with default certificate verification, 30 s timeout (`lib/check_pins.py:77`), per-pin error handling for HTTP, network, and response-shape failures without leaking headers (`lib/check_pins.py:95-101`), per-(action, tag) response cache. Live run verified 8/8 pins in this repo's workflows against upstream tags.
- **References:** `lib/check_pins.py:67-110`, `.github/workflows/self-check.yml:24-31`.

### Secrets

- **Finding:** `GITHUB_TOKEN` read from env, sent only in the `Authorization` header, never printed or included in error output (error strings carry file:line, action, version, and error class only). No secrets in source.
- **References:** `lib/check_pins.py:73`, `lib/check_pins.py:95-101`, `lib/check_pins.py:127`.

### Command execution

- **Finding:** New `git diff` invocation uses list argv, no shell, `--` path separator; inputs come from git's own output, not user strings.
- **References:** `lib/validate.py:88`, existing `run()` helper `lib/validate.py:64-68`.

### Build, CI, and supply chain

- **Finding:** New `pins` job uses the SHA-pinned checkout, no `permissions:` widening, read-only token use. New skill and template are gated as code by the existing validator rules (`is_skill`). Plugin manifests bumped consistently (0.4.0). No new third-party dependencies — both new modules are stdlib-only, preserving the baseline's no-dependency requirement for the validator.
- **References:** `.github/workflows/self-check.yml:24-31`, `lib/validate.py:51-52`, `plugins/sdl/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`.

### Threat-mitigation cross-check

- **Finding:** T1 and T2 mitigations verified in code (table in `03-implementation.md`, all locations checked). T3 is explicitly *not* code-mitigated — its control is policy (`docs/dependency-updates.md`) plus ecosystem integrity tooling; recorded as residual R1 rather than claimed as mitigated. Review closed one T1 gap found during verification (removal-only pin changes, `lib/validate.py:110-112`, test `lib/test_validate.py:283-288`).

**Not applicable (no code in these areas):** persistence, authentication/authorization, cryptography, logging of user data, concurrency, frontend, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

`self-check.yml`: 55 unit tests across both modules (run locally, green), `shellcheck` (no shell changes), structure checks extended to the new files, JSON manifest parse checks, and the new `pins` job (verified live: 8/8). No third-party dependencies to scan.

## Residual risks <!-- DM-1 -->

| ID | Description | Severity | Disposition | Carry-forward target |
|----|-------------|----------|-------------|----------------------|
| R1 | Routine tier cannot see lockfile/manifest *content* (resolved URLs, integrity hashes, npm scripts); relies on ecosystem integrity mode, trusted automation, and human merge review (T3) | medium | accept | revisit if fleet contributor base widens or an ecosystem lacks integrity tooling |
| R2 | `check_pins` runs only in this repo's CI; consumers get it by policy adoption, not via `sdl-validate.yml` — a consumer can skip it silently | low | defer | future cycle: gated `check_pins` step in `sdl-validate.yml` (see 02, noted-for-future) |
| R3 | Warn-first means manifest-only diffs still pass consumer gates with no record until the warning becomes a hard check | low | accept | flip to hard fail in next major version of the gate |
