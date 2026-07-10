# sdl

Central tools repo for our IEC 62443-4-1 aligned Secure Software Development Lifecycle. Single source of truth for skills, templates, and CI workflows used across all org project repos.

**New here?** Read the [developer guide](docs/developer-guide.md) — what SDL asks of you day to day, including the [lightweight path for dependency updates](docs/dependency-updates.md).

## What's here

- **`plugins/sdl/`** — The self-contained plugin: `skills/` (`sdl-baseline`, `sdl-spec`, `sdl-threat-model`, `sdl-review`, `sdl-dep-update`), `lib/` (scaffolding and validation scripts the skills invoke), and `templates/` (artifact stubs). Published as `sdl@relay` via the [Relay plugin marketplace](https://github.com/savioke/relay-plugin-marketplace); other agents consume the same skills from a clone.
- **`.github/workflows/sdl-validate.yml`** — Reusable GitHub Actions workflow each project repo calls via `workflow_call`. CI is the SDL enforcement gate.
- **`scripts/install.sh`** — Full dev setup for non-Claude agents: clones this repo, symlinks skills into Copilot, and also registers the marketplace for Claude Code.
- **`scripts/sync-to-repo.sh`** — Per-project init: drops the workflow file and creates `docs/sdl/`.
- **`docs/`** — `62443-mapping.md` (audit-facing), [`developer-guide.md`](docs/developer-guide.md) (dev intro), [`dependency-updates.md`](docs/dependency-updates.md) (supply-chain update policy), `admin-setup.md` (releasing, repo and developer onboarding).

## Install (per developer, once)

**Claude Code only** (the common case) — no clone needed. In Claude Code:

```
/plugin marketplace add savioke/relay-plugin-marketplace
/plugin install sdl@relay
```

Updates: `/plugin marketplace update relay`.

**Copilot or other agents** (also covers Claude Code):

```
gh repo clone savioke/sdl ~/.sdl-governance
~/.sdl-governance/scripts/install.sh
```

Updates: `cd ~/.sdl-governance && git pull`.

## Enable on a project (per repo, once)

```
~/.sdl-governance/scripts/sync-to-repo.sh /path/to/your/repo
```

## Design

See `Plan.md` for the full design and rationale. Two-line summary: skills (installed globally) handle the work; project repos contain only `docs/sdl/` and a tiny `.github/workflows/sdl.yml` that calls the reusable workflow here. No CLAUDE.md, AGENTS.md, or copilot-instructions.md content is required in project repos — the presence of `docs/sdl/` is the trigger.
