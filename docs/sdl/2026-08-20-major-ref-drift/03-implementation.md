# 03 — Implementation

## Summary of changes

`check_release.py` gains two read-only checks and calls them from the two modes
it already has. `check_validator_ref` reads `.github/workflows/sdl-validate.yml`
and requires the `sdl_ref` input's `default:` to equal `v<plugin.json major>`;
`check_caller_ref` reads `.github/workflows/sdl.yml` and requires its `uses:`
ref to equal the same alias. The validator ref is asserted in both `pr` and
`released` mode — the reusable workflow and `plugin.json` ship from one commit,
so no state exists in which they may name different majors. The caller ref is
asserted in `released` mode only, and skipped while `main` still sits on the
commit the current alias points at: release step 3 cuts that alias, so on that
commit the caller has nothing valid to have been moved to yet. `docs/releasing.md`
"What CI checks" records both, and the module docstring records them per mode.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1     | Every unread outcome is an error rather than a skip: a missing file, an `sdl_ref` input with no `default:`, and a caller with no matching `uses:` line each return their own message. `sdl_ref` is read as the indented block under its own key and stops at the next sibling key, so the `base` input's `default:` — which sits immediately above it in the real file — cannot be compared in its place. | `scripts/check_release.py:99-121` (`sdl_ref_default`), `:123-143` (`check_validator_ref`), `:145-163` (`check_caller_ref`) | b13f29f |

## Secure coding practices applied <!-- SI-2 -->

Both files are read with `encoding="utf-8", errors="replace"`, matching how the
rest of the repo reads repo-local markdown and YAML, so an undecodable byte
yields a comparison that fails rather than a traceback out of a required check.
The parsing is line-anchored regex over a bounded block; nothing is evaluated,
no path is taken from file content, and neither check writes, forks, or fetches.
Both return `list[str]` into the existing `errors` list, so the exit-code
contract and the `[FAIL]` reporting are unchanged.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None. Standard library only, as before; `plugin.json` is untouched — nothing
shipped changed, so no version bump is due (`docs/releasing.md`, step 2).

## Deviations from spec or threat model

One, recorded rather than left implicit. `self-gate-v2:R2` asks for both refs to
be asserted; the caller ref cannot be asserted unconditionally without failing
`release.sh`'s own final verification on every major, since it runs immediately
after step 3 cuts the alias the caller must move to. The exemption is scoped as
narrowly as the condition allows — `main` sitting exactly on the alias commit —
so the check resumes on the first commit after the release and stays failing
until the gate moves. That is the state R2 describes as undetected today.
