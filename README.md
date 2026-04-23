# sdl

Central tools repo for our IEC 62443-4-1 aligned Secure Software Development Lifecycle. Single source of truth for skills, templates, and CI workflows used across all org project repos.

## What's here

- **`skills/`** — Claude Code / Copilot skills: `sdl-spec`, `sdl-threat-model`, `sdl-review`. Author once, both tools consume.
- **`templates/docs-sdl/`** — The four artifact stubs and `.sdl-meta.yml` copied into each new SDL cycle folder.
- **`workflows/sdl-validate.yml`** — Reusable GitHub Actions workflow each project repo calls via `workflow_call`.
- **`hooks/`** — Optional pre-commit and prepare-commit-msg hooks. Opt-in per repo via `sync-to-repo.sh`.
- **`scripts/install.sh`** — One-shot dev setup: clones this repo and symlinks skills into Claude Code and Copilot.
- **`scripts/sync-to-repo.sh`** — Per-project init: drops the workflow file, creates `docs/sdl/`, installs hook shims.
- **`docs/`** — `62443-mapping.md` (audit-facing), `developer-guide.md` (dev intro), `admin-setup.md` (deploy keys, key rotation, repo onboarding).
- **`marketplace.json` + `plugins/sdl/`** — Claude Code plugin marketplace path. Same skills, served via the marketplace UX.

## Install (per developer, once)

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
