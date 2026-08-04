# 01 — Requirements

## Summary

The SDL gate workflow generated for every participating repo declares `on: [pull_request, push]`. A tag push is a push event, so the gate also runs on tags — where it has nothing to validate. Cutting `v1.0.0` produced two spurious `validate` runs on top of the merge. This narrows the trigger to `push: branches: [main]`, matching what `self-check.yml` already does.

## Scope

In scope: the `push` trigger in this repo's `.github/workflows/sdl.yml` and in the copy that `plugins/sdl/lib/sync_to_repo.sh` writes into consumer repos; version 1.0.1 and its changelog entry. Out of scope: `sdl.yml` files already written into consumer repos — `sync_to_repo.sh` refuses to overwrite an existing one, so those are the owning repo's to update (the changelog says so).

## Assets touched <!-- SR-1 -->

`sync_to_repo.sh` is shipped content: it authors the workflow that invokes the gate in every consumer's CI. Standing integrity assets per `baseline.md`.

## Trust boundaries crossed <!-- SR-2 -->

None new. Narrows when an existing boundary is crossed (the gate runs on fewer events); it does not move one.

## Data classification <!-- SR-1 -->

None. Public repo, no secrets — per `baseline.md`.

## External inputs introduced <!-- SR-2 -->

None.

## Security requirements <!-- SR-3, SR-4 -->

- No event that today reaches the gate with a reviewable diff may stop reaching it. `pull_request` is untouched, and `push` to `main` is retained.
- The generated workflow and this repo's own must stay identical in trigger, so this repo keeps dogfooding what consumers run.

## Related prior cycles

- `2026-08-03-release-process` — cutting `v1.0.0` under it is what surfaced this.
- `2026-07-10-plugin-self-adopt` — moved the workflow-authoring logic into `sync_to_repo.sh`, where the trigger is defined.

## Carried-forward residual risks

None.
