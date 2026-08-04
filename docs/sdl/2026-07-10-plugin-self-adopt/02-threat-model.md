# 02 — Threat Model

<!-- SR-2: Threat model. SD-1, SD-2: Secure design and defense in depth. -->

## Components and data flows

- `plugins/sdl/lib/sync_to_repo.sh` (new) — scaffolds a target repo: writes `.github/workflows/sdl.yml`, `docs/sdl/.gitkeep`, copies `templates/baseline.md`. Runs on developer workstations with developer privileges; now distributed through the plugin package (fetched from `main`) as well as clones.
- `scripts/sync-to-repo.sh` (rewritten) — thin `exec` delegate to the plugin copy, path-relative to itself. Clone-based entry point only.
- `sdl-baseline` SKILL.md (modified) — new step 0 instructs agents to run the script when `docs/sdl/` is absent and the user explicitly asked to adopt SDL.
- Generated `sdl.yml` — consumer-repo CI workflow pinning `savioke/sdl/.github/workflows/sdl-validate.yml@${SDL_REF}` (default `v1`).

## Threats <!-- SR-2 -->

### T1 — SDL_REF injection into the generated workflow

- **Category:** Tampering
- **Component / flow:** environment → `sync_to_repo.sh` heredoc → consumer repo's committed CI workflow.
- **Description:** `SDL_REF` is interpolated into generated YAML. A crafted value containing a newline could append arbitrary workflow content (extra jobs/steps) that then runs in the consumer's CI with its `GITHUB_TOKEN`. Realistic vector is not an attacker with shell env control (they already execute code) but a confused or prompt-injected agent passing a hostile value when invoking the script per the skill instructions.
- **Likelihood / Impact:** low / medium
- **Mitigation:** the script validates `SDL_REF` against `^[A-Za-z0-9._/-]+$` before interpolation and exits on mismatch; newlines, quotes, and YAML syntax cannot pass. The `uses:` target repo path is hardcoded — only the ref is variable.
- **Mitigation type:** preventive
- **Defense in depth notes:** the generated file is written, not committed — a human still reviews and commits it; a hostile ref within the allowed charset still resolves only within `savioke/sdl`.

### T2 — Unsolicited SDL scaffolding of a repo

- **Category:** Tampering
- **Component / flow:** `sdl-baseline` skill trigger → agent runs the scaffold script in the current repo.
- **Description:** Previously the skill exited silently when `docs/sdl/` was absent; now it can create it. A skill that misfires (probabilistic trigger) could scaffold CI workflow files into a repo whose owner never opted into SDL, wiring it to an external reusable workflow.
- **Likelihood / Impact:** low / low
- **Mitigation:** precondition requires an explicit user request ("initialize SDL", "add SDL to this repo") before scaffolding; absent that, the skill still exits silently. The script never overwrites existing files and never commits — the user reviews and commits the three files themselves.
- **Mitigation type:** preventive
- **Defense in depth notes:** generated workflow is 5 lines and pinned to `@v1`; a misfire is visible in `git status` and trivially reverted.

## Threats inherited from prior cycles <!-- SR-2 -->

- **2026-07-09-split-marketplace:T1 (marketplace manifest repoints the plugin source)** — blast radius nuance: the package now carries a shell script agents are instructed to execute, alongside the Python tools and skill instructions it already carried. No change in kind (skills already drive shell with developer privileges); mitigation and disposition unchanged, standing risk baseline:B7.
- **2026-07-09-split-marketplace:T2 (plugin-relative path resolution escapes the plugin)** — extends to the new `<plugin-root>/lib/sync_to_repo.sh` invocation in `sdl-baseline`. Same anchor ("two levels above this SKILL.md", `$CLAUDE_PLUGIN_ROOT` in Claude Code) and same mitigation; additionally the script dies if `templates/baseline.md` is absent from the resolved root, so a mis-resolution fails loudly rather than scaffolding from an unexpected tree.
- **baseline:B3 (workstation scripts)** — logic moved, not grown: the plugin copy is the old `sync-to-repo.sh` minus the install-dir requirement plus ref validation; the repo-root delegate holds no logic. `accept` unchanged.

## Out-of-scope threats

- Marketplace manifest integrity (delivery of this script from `main`) — baseline:B7, owner: maintainer; revisit triggers recorded in baseline.
- What `sdl-validate.yml@v1` does with the consumer's `GITHUB_TOKEN` — the standing "this repo → consumer CI" boundary in the baseline, unchanged by this cycle.

## Noted for future cycles

- `sync_to_repo.sh` is local-only by design (heredoc + local template copy). If it ever fetches templates or refs over the network, that becomes a new supply-chain flow needing its own threat stanza.
- `self-check.yml` now shellchecks `plugins/sdl/lib/*.sh`, so future shell added to the plugin is gated automatically.
