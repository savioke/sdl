# 01 — Requirements

<!-- SR-1: Product security context. SR-2: Threat model inputs. -->

## Summary

Make the Claude Code plugin self-sufficient for repo adoption. Today `scripts/sync-to-repo.sh` hard-requires a clone at `~/.sdl-governance` (`$SDL_INSTALL_DIR`), but plugin-only users have no clone — the marketplace package ships only `plugins/sdl/` (lib, skills, templates), so they cannot onboard a repo at all. Move the scaffolding logic into the plugin (`plugins/sdl/lib/sync_to_repo.sh`, resolving the baseline template relative to its own location), make `scripts/sync-to-repo.sh` a thin delegate for clone-based users, and teach the `sdl-baseline` skill to scaffold an un-adopted repo before authoring the baseline, so "initialize SDL in this repo" works end-to-end from a marketplace install.

## Scope

In scope:

- New `plugins/sdl/lib/sync_to_repo.sh` — writes `.github/workflows/sdl.yml`, `docs/sdl/.gitkeep`, and `docs/sdl/baseline.md` (from the plugin's own `templates/baseline.md`) into a target repo.
- `scripts/sync-to-repo.sh` becomes a delegate to the plugin copy (path-relative to itself, so any clone location works).
- `sdl-baseline` SKILL.md: new scaffolding step when `docs/sdl/` is absent, using `${CLAUDE_PLUGIN_ROOT}` (Claude Code) or the clone path (other agents).
- README install/enable instructions; plugin version bump.

Out of scope: changes to `validate.py`, the reusable workflow, other skills, and the marketplace manifest repo (`savioke/relay-plugin-marketplace` needs no change — it fetches from `main`).

## Assets touched <!-- SR-1 -->

Integrity assets per baseline: `scripts/sync-to-repo.sh` (existing), `plugins/sdl/lib/` (new shell script alongside the Python tools), `plugins/sdl/skills/sdl-baseline/SKILL.md`. The script writes files into an arbitrary target repo with the developer's privileges (baseline trust boundary "this repo → developer workstation (scripts)").

## Trust boundaries crossed <!-- SR-2 -->

No new boundary. The existing "repo → developer workstation" boundary gains a second distribution path for the same logic: previously the scaffolding script reached workstations only via clone; now it also ships in the plugin package fetched from `main`. The generated `sdl.yml` pins `savioke/sdl@v1` exactly as before (`SDL_REF` overridable via env, unchanged behavior).

## Data classification <!-- SR-1 -->

Public. No secrets, PII, or customer data; the script handles paths and static template content only.

## External inputs introduced <!-- SR-2 -->

- Script arguments: target repo path (validated: must contain `.git/`).
- Environment: `SDL_REF` (existing behavior, interpolated into the generated workflow file), `CLAUDE_PLUGIN_ROOT` (used by the skill to locate the script, not read by the script itself).
- No network input: the script generates the workflow from a heredoc and copies a local template; it fetches nothing.

## Security requirements <!-- SR-3, SR-4 -->

- `set -euo pipefail`; refuse non-git targets; never overwrite existing `sdl.yml` or `baseline.md` (preserve current fail-safe behavior).
- Quote all path expansions; pass `shellcheck` (enforced by self-check CI).
- Generated workflow must keep pinning `savioke/sdl` by ref (`@v1` default) — no floating `main` reference in consumer CI.
- Single source of truth: the repo-root script must delegate, not duplicate, so the two distribution paths cannot drift.

## Related prior cycles

- `2026-07-09-split-marketplace` — created the plugin packaging this cycle extends.
- `2026-07-09-marketplace-rename` — marketplace naming the install flow references.
- `2026-06-10-adopt-sdl-governance` — original `sync-to-repo.sh` design.

## Carried-forward residual risks

- `2026-07-09-split-marketplace` R1 (end-to-end `sdl@relay` install untested, mitigate-later): closed by evidence — on 2026-07-10 the marketplace was added and `sdl@relay` 0.6.0 installed on a real workstation; skills and templates materialized correctly in the plugin cache and loaded into a session. This cycle's gap analysis (missing `sync-to-repo.sh` for plugin-only users) came out of that test.
