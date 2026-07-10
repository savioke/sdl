# 03 — Implementation

<!-- SI-1: Security implementation review. SI-2: Secure coding standards. -->

## Summary of changes

The marketplace manifest left this repo for `savioke/relay-plugin-marketplace` (marketplace `relay`, plugin entry `git-subdir` → `https://github.com/savioke/sdl.git` path `plugins/sdl` ref `main`, version 0.6.0). In this repo: `skills/`, `lib/`, and `templates/` moved under `plugins/sdl/` as real files, replacing the out-of-tree symlinks; the three skills that shell out now derive tooling paths from their own SKILL.md location; `validate.py.template_dir()` prefers file-adjacent templates; `install.sh` symlinks Copilot at the new path and registers the marketplace by its public HTTPS URL; `sync-to-repo.sh`, both workflows, and all docs updated; plugin version bumped to 0.6.0 with an `author` field. Docs now lead with the two-command Claude Code install.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Manifest points only at the public gated repo; risk registered with revisit triggers | `relay-plugin-marketplace:.claude-plugin/marketplace.json` (`source`); `docs/sdl/baseline.md` B7 | this branch |
| T2 | Path resolution anchored to the SKILL.md the harness loaded, uniform across channels | `plugins/sdl/skills/sdl-spec/SKILL.md:26,35`, `sdl-review/SKILL.md:87`, `sdl-dep-update/SKILL.md:49,60` | this branch |
| T2 (depth) | Validator prefers its own shipped templates over clone state | `plugins/sdl/lib/validate.py:224` (`template_dir` order) | this branch |
| inherited B3 | `install.sh` changes stay path/argument-level; no new logic | `scripts/install.sh:40,55-62` | this branch |

## Secure coding practices applied <!-- SI-2 -->

- Self-containment enforced structurally: no symlink under `plugins/sdl/` points outside it; everything the skills invoke ships inside the plugin.
- `validate.py` code-classification (`"skills" in p.parts`) confirmed path-independent, so skill edits still gate as code at the new location (`plugins/sdl/lib/validate.py:52`).
- Shell edits `shellcheck`-clean; JSON manifests machine-validated (`claude plugin validate` on both plugin and marketplace).
- No new dependencies; validator remains stdlib-only.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None.

## Deviations from spec or threat model

The plugin `version` also moved to 0.6.0 in the external manifest — a duplication accepted and documented (`docs/admin-setup.md` release step 5) rather than automated, matching the single-maintainer scale.
