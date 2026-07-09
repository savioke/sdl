# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-07-09
- **Diff range:** f93872d..HEAD (origin/main merge base, working tree included — the install.sh revert hunk is pending commit at review time)

## Checks performed <!-- SVV-1, SVV-2 -->

### New install scripts (build, CI, and supply chain)

- **Finding:** `scripts/install.sh` modified — verified string-only per hunk: install target `sdl@relay` at `scripts/install.sh:56-57`, printed footer at `:67`, printed update command at `:75`. No new network fetch, integrity-relevant step, privileged operation, or control flow. baseline:B3 disposition unchanged. An interim commit (b2fc1a4) added `plugin uninstall`/`marketplace remove` calls; the final diff reverts them — confirmed absent from the reviewed tree. `shellcheck` and `bash -n` pass.
- **References:** `scripts/install.sh:56-57,67,75`

### Plugin/marketplace manifest integrity (supply chain)

- **Finding:** `.claude-plugin/marketplace.json` changes confined to identity fields (`name`, `displayName`, `owner.name`, `description`). The plugin entry's `source: ./plugins/sdl`, name, and version are untouched, so the installed artifact is unchanged. `relay` is valid (kebab-case) and not an Anthropic-reserved marketplace name. JSON validates.
- **References:** `.claude-plugin/marketplace.json:3-8`

### Documentation accuracy of the security-relevant procedure

- **Finding:** the documented update command matches the renamed manifest everywhere it appears: `docs/developer-guide.md:28`, `Plan.md:132`, `scripts/install.sh:75` all say `/plugin marketplace update relay`. Remaining `savioke` references verified to be GitHub org/repo paths only (clone URLs, reusable-workflow ref, `check_pins.py --exempt`), which are correct as-is.
- **References:** `docs/developer-guide.md:28`, `Plan.md:132`, `docs/admin-setup.md:3`

**Not applicable (no code in these areas):** input handling, data and persistence, network and transport, authentication and authorization, cryptography, secrets, logging and observability, concurrency and resource use, dependencies, frontend, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

- `shellcheck scripts/install.sh` — clean.
- `python3 -m json.tool .claude-plugin/marketplace.json` — valid.
- `python3 -m pytest lib/ -q` — 55 passed (validator unaffected by this diff, run as regression).
- CI: `self-check.yml` unit tests + this repo's own SDL gate (`sdl.yml`).

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | T1 mitigation is procedural (manual migration of the two existing installs); nothing in the repo verifies it happened. If skipped, those installs keep stale `sdl@savioke` skills silently. | low | accept | none — self-resolving once the maintainer migrates; revisit only if pre-rename installs ever exist on machines the maintainer does not control |
