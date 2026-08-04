# sdl

Central tools repo for our IEC 62443-4-1 aligned Secure Software Development Lifecycle. Single source of truth for skills, templates, and CI workflows used across all org project repos.

**New here?** Read the [developer guide](docs/developer-guide.md) — what SDL asks of you day to day, including the [lightweight path for dependency updates](docs/dependency-updates.md).

## What's here

- **`plugins/sdl/`** — The self-contained plugin: `skills/` (`sdl-baseline`, `sdl-spec`, `sdl-threat-model`, `sdl-review`, `sdl-dep-update`), `lib/` (scaffolding and validation scripts the skills invoke), and `templates/` (artifact stubs). Published as `sdl@relay` via the [Relay plugin marketplace](https://github.com/savioke/relay-plugin-marketplace); other agents consume the same skills from a clone.
- **`.github/workflows/sdl-validate.yml`** — Reusable GitHub Actions workflow each project repo calls via `workflow_call`. CI is the SDL enforcement gate.
- **`scripts/install.sh`** — Full dev setup for non-Claude agents: clones this repo, symlinks skills into Copilot, and also registers the marketplace for Claude Code.
- **`scripts/sync-to-repo.sh`** — Per-project init for clone-based installs; thin delegate to `plugins/sdl/lib/sync_to_repo.sh`, which drops the workflow file and creates `docs/sdl/`.
- **`docs/`** — `62443-mapping.md` (audit-facing), [`developer-guide.md`](docs/developer-guide.md) (dev intro), [`dependency-updates.md`](docs/dependency-updates.md) (supply-chain update policy), `admin-setup.md` (releasing, repo and developer onboarding).

## Install (per developer, once)

**Claude Code**:

```
/plugin marketplace add savioke/relay-plugin-marketplace
/plugin install sdl@relay
```

This installs the skills and helper scripts into Claude's config dir.

Updates: `/plugin marketplace update relay`.

**Copilot or other agents** (also covers Claude Code):

```
gh repo clone savioke/sdl ~/.sdl-governance
~/.sdl-governance/scripts/install.sh
```

This sets up symlinks to the skills and help scripts for agents other than Claude Code.

Updates: `cd ~/.sdl-governance && git pull`. Upgrading a clone made before 1.0.0 also needs one `scripts/install.sh` re-run — skills moved inside the plugin, and the old symlink no longer resolves.

## Enable on a project (per repo, once)

**Claude Code**: ask Claude to "initialize SDL in this repo". The `sdl-baseline` skill scaffolds the CI workflow and `docs/sdl/`, then authors the security baseline — no clone needed.

**Clone-based installs**:

```
~/.sdl-governance/scripts/sync-to-repo.sh /path/to/your/repo
```

Then ask your agent to "initialize the SDL baseline".

## Design

See `Plan.md` for the full design and rationale. Two-line summary: skills (installed globally) handle the work; project repos contain only `docs/sdl/` and a tiny `.github/workflows/sdl.yml` that calls the reusable workflow here. No CLAUDE.md, AGENTS.md, or copilot-instructions.md content is required in project repos — the presence of `docs/sdl/` is the trigger.
