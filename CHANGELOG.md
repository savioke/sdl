# Changelog

What changed in each release of `savioke/sdl`, newest first.

Consumer repos pin the moving `@v1` alias, so a release reaches their CI without
them changing anything — this file is how they find out what moved. Every entry
notes whether it can turn a previously-passing PR red. See `docs/releasing.md`
for the compatibility contract and the release procedure.

Versions are the plugin's (`plugins/sdl/.claude-plugin/plugin.json`); each is
tagged `vX.Y.Z` and, for the current major, aliased by `vX`.

## 1.0.0 — 2026-08-04

First release under the versioning contract in `docs/releasing.md`, and the
first to reach consumers since the `v1` tag was cut. Promoted to 1.0.0 so the
plugin's version and the tag consumers already pin (`@v1`) denote the same
major; 0.6.0 and 0.7.0 were never delivered as releases and are folded in here.

**Not breaking.** Nothing that passed the gate before fails now: the validator
changes below only widen what is accepted, and the one new check emits `[warn]`.

### Gate (reaches consumer CI via `@v1`)

- Dependency-update cycles: a `.sdl-meta.yml` declaring `class: dependency-update`
  is validated against a `dep-update.md` record instead of the four-document
  cycle, provided the whole diff is manifests, lockfiles, and pin-only workflow
  changes. Previously these needed a full cycle.
- Workflow pin changes are accepted only when every changed `uses:` line is
  SHA-pinned with a parseable version comment, the action is unchanged, and the
  major matches — a new, removed, or major-bumped action still requires a full
  cycle.
- New `[warn]` (not a failure): a diff that touches dependency manifests with no
  dependency-update cycle. Slated to become a hard check in a future major.
- Skill and template `.md` files are gated as code, so changes to agent-executable
  instructions require a cycle.
- `sdl-validate.yml` runs on newer pinned actions: `actions/setup-python` v6.3.0
  → v7.0.0 and `actions/checkout` v7.0.0 → v7.0.1. Both still declare
  `runs.using: node24`, so no runner requirement changed; the only breaking
  change in setup-python v7 is removal of the `pip-install` input, which this
  workflow never set and callers cannot reach.

### Plugin (reaches Claude Code via the marketplace)

- The plugin is self-contained: `skills/`, `lib/`, and `templates/` live under
  `plugins/sdl/`, and skills resolve their tooling relative to their own
  `SKILL.md` instead of assuming a `~/.sdl-governance` clone.
- Repo onboarding no longer needs a clone: `plugins/sdl/lib/sync_to_repo.sh`
  ships inside the plugin, and the `sdl-baseline` skill scaffolds an un-adopted
  repo on request before writing the baseline.
- New `sdl-dep-update` skill for routine dependency-update cycles.
- `sdl-review` gained a "Proportionality" section: the SDL artifacts record only
  what changes what an attacker can do, what a control detects, or what risk the
  reader is accepting — findings are one to three sentences, a re-review after PR
  comments does not get an entry per comment, and a concern investigated and found
  not to be a defect is not recorded at all. The `04-verification.md` template
  gained a matching, explicitly optional "Defects found" section. Non-security
  detail in these files buries the security signal.
- Marketplace renamed `relay-sdl` → `relay`; the plugin installs as `sdl@relay`
  from `savioke/relay-plugin-marketplace`.

### Release and supply chain

- `scripts/release.sh` performs the whole release; `scripts/check_release.py`
  fails CI when the repo, its tags, and the marketplace manifest disagree.
- The marketplace manifest now pins `source.ref` to the exact release tag rather
  than `main`, so a declared version identifies exactly one tree.
- Release tags are annotated and signed when a signing key is configured.
- `check_pins.py` verifies every SHA-pinned action against the tag in its
  comment, catching retag-after-pin drift; `self-check` runs daily so drift is
  found without waiting for a push.

### Upgrading

- **Consumer repos:** nothing to do. The next CI run picks this up from `@v1`.
- **Claude Code:** `/plugin marketplace update relay`, then reload. Required —
  the plugin cache is keyed by version, so an install stays on its old copy
  until the version changes.
- **Copilot / clone-based installs:** `cd ~/.sdl-governance && git pull &&
  scripts/install.sh`. Re-running `install.sh` is **required this time**: skills
  moved to `plugins/sdl/skills/`, and a symlink created before that move points
  at a path that no longer exists, which silently leaves the agent with no
  skills. A plain `git pull` is enough for later releases.

## Earlier history

Releases before 1.0.0 were tagged only as the moving `v1` alias and are not
itemized here. See `git log v1` and the cycle records under `docs/sdl/`.
