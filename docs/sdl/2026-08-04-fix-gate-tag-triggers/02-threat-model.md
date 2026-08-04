# 02 — Threat Model

## Components and data flows

- `plugins/sdl/lib/sync_to_repo.sh` — authors `.github/workflows/sdl.yml` in a consumer repo; only the `on:` block changes.
- `.github/workflows/sdl.yml` (this repo) — the same change, kept in step.

## Threats <!-- SR-2 -->

None. The change removes trigger events from a read-only validation workflow. It grants no permission, adds no input, and cannot cause the gate to accept a diff it previously rejected: `pull_request` and `push` to `main` are unchanged, and the removed events (tags) carry no diff the gate could have judged.

## Threats inherited from prior cycles <!-- SR-2 -->

`baseline:B1` (a change here reaches every consumer's CI) applies as always and is the reason this one-line change carries a cycle at all. `baseline:B5` (moving `v1`) unchanged.

## Out-of-scope threats

- Consumer repos keep their existing `sdl.yml` until they edit it themselves; that is ownership, not a gap. The stale form is noisy, never permissive.

## Noted for future cycles

- The gate would be more robustly scoped by branch-filtering in `sdl-validate.yml` itself rather than in the caller, but the caller is the file consumers own and edit. Revisit if consumer copies drift far enough that the callee needs to defend itself.
