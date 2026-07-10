# 02 — Threat Model

## Components and data flows

- **`plugins/sdl/`** — the plugin, now containing the real `skills/`, `lib/`, `templates/` (previously symlinks out / separate top-level dirs). Delivered two ways: Claude Code fetches it from `main` via the external marketplace manifest; other agents read it from the `~/.sdl-governance` clone through a Copilot symlink.
- **`savioke/relay-plugin-marketplace`** — new external repo; one manifest whose `source` field points Claude Code at `plugins/sdl` here.
- **SKILL.md files (`sdl-spec`, `sdl-review`, `sdl-dep-update`)** — tooling paths changed from `~/.sdl-governance/lib/...` to plugin-relative (`<plugin-root>/lib/...`, two levels above the SKILL.md).
- **`validate.py` `template_dir()`** — search order now file-relative first, clone second.
- **`install.sh` / `sync-to-repo.sh` / workflows / docs** — path and registration-target updates.

## Threats <!-- SR-2 -->

### T1 — Marketplace manifest repoints the plugin source

- **Category:** Tampering
- **Component / flow:** `savioke/relay-plugin-marketplace` manifest → every Claude Code developer machine on next `/plugin marketplace update relay`.
- **Description:** The manifest lives outside this repo's SDL gate, CI, and PR review. Anyone with write access (or a compromised account) can change `source.url`/`path`/`ref` to deliver arbitrary skills — instructions executed by agents with developer privileges — and no check in this repo would notice.
- **Likelihood / Impact:** low / high — org-member-only write access, single small file, but delivery is silent and reaches every Claude dev.
- **Mitigation:** repo is org-controlled with minimal contents (nothing else to legitimately edit, so any diff is suspicious); the plugin source it names is this public, gated repo. Recorded as standing risk baseline:B7 with explicit revisit triggers (more plugins, maintainers, or users → branch protection / sha-pinning / SDL gating).
- **Mitigation type:** preventive (access control), detective (auditable single-file repo)
- **Defense in depth notes:** `sha`-pinning the plugin entry would make delivery reproducible and force an explicit bump per release; deliberately deferred (tracks `main` like the clone always did) until there are external users.

### T2 — Plugin-relative path resolution escapes the plugin

- **Category:** Elevation of privilege
- **Component / flow:** SKILL.md instructions → agent shell execution on developer machines.
- **Description:** Skills now tell the agent to run `python3 <plugin-root>/lib/new_cycle.py` where `<plugin-root>` is derived from the SKILL.md location. If an agent mis-resolves that (e.g. from a repo-local directory an attacker controls instead of the installed plugin), it executes the wrong `new_cycle.py`. The old `~/.sdl-governance` form had the same property with a fixed path; the relative form ties resolution to wherever the skill file actually is, which is the trusted install in both channels.
- **Likelihood / Impact:** low / medium — requires the attacker to already control a directory the agent confuses with the plugin install, at which point they control skill content too (baseline:B2 territory).
- **Mitigation:** the instruction anchors resolution to "this SKILL.md" — a file the harness itself loaded from the install location, not from the target repo; project repos contain no `lib/` or plugin layout to confuse it with.
- **Mitigation type:** preventive
- **Defense in depth notes:** the invoked scripts are stdlib-only and write only into `docs/sdl/`; `validate.py` gates their output in CI regardless of which copy ran.

## Threats inherited from prior cycles <!-- SR-2 -->

- **2026-07-09-marketplace-rename T1 (orphaned registration)** — recurs identically: existing `relay-sdl` registrations stop updating after this merges. Same disposition — one known user (the maintainer) migrates manually (`/plugin marketplace remove relay-sdl`, add `relay`, install `sdl@relay`); fresh installs unaffected. Not re-litigated.
- **baseline:B2 (skill-instruction injection)** — the skills moved and their tooling paths changed; content otherwise unchanged. Still gated as code by the validator ("skills" in path parts still matches `plugins/sdl/skills/`, verified by test suite).
- **baseline:B3 (workstation scripts)** — `install.sh` changes are path/argument-level: Copilot symlink target and marketplace registration argument (local dir → SSH URL into the existing `claude plugin marketplace add` call). No new executable logic. `accept` unchanged.

## Out-of-scope threats

- Compromise of `savioke/sdl` `main` delivering bad plugin code — baseline:B1/B2, owned by PR review and the SDL gate; the marketplace changes the fetch path, not that trust.
- `claude` CLI's fetch/install mechanics (how it clones, where it caches) — Anthropic's surface, not ours.
- Marketplace repo visibility — made public during this cycle (it holds only the manifest referencing this public repo), so `/plugin marketplace add savioke/relay-plugin-marketplace` works without auth. Write access remains org-only (T1's control).

## Noted for future cycles

- Before external users exist: revisit baseline:B7 mitigations — branch protection on the marketplace repo and `sha`-pinning the plugin entry with a bump-on-release step.
- If a second plugin joins the marketplace, its source repo inherits the same B7-shaped exposure; consider SDL-gating the marketplace repo itself at that point.
- If skills ever gain scripts that execute at install time (hooks), the marketplace channel becomes a code-execution vector at install rather than at use; re-threat-model.
