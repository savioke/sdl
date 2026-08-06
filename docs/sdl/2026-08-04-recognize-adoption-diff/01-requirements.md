# 01 — Requirements

## Summary

A repo's SDL adoption PR cannot pass the gate. The PR installs `.github/workflows/sdl.yml`, which `code_changed()` counts as code, so `check_cycle_present` demands a `docs/sdl/*/.sdl-meta.yml` naming the branch — a cycle that by definition does not exist yet, on a repo that has run none. The first field report (an external repo enrolled purely through the marketplace path) hit exactly this; the only workarounds were a decoy cycle documenting the act of enrolling, or an admin merge over a red check. Both teach the wrong lesson about the gate. The validator now recognizes the adoption diff — one that adds the generated workflow and `docs/sdl/baseline.md` and touches nothing else outside `docs/sdl/` — and validates it against the baseline, which *is* the adoption artifact.

## Scope

In scope: `check_cycle_present` plus the new `check_adoption`, `is_adoption_workflow`, and `added_files` in `plugins/sdl/lib/validate.py`; the missing-cycle failure message; unit tests; the `sdl-baseline` skill and `sync_to_repo.sh` closing instructions (fill the baseline *before* the adoption commit); `developer-guide.md` and `admin-setup.md`; version 1.1.0 and its changelog entry.

Out of scope: the `[warn]` for an unfilled baseline on ordinary PRs (unchanged); already-enrolled repos (unaffected — the exemption is unreachable once `baseline.md` is in the base branch); tolerating a scaffold-then-baseline two-PR split, deliberately not supported (see `02`, T3).

## Assets touched <!-- SR-1 -->

`validate.py` is shipped content: it decides pass/fail in every consumer's CI, and this change widens what it accepts. `baseline:B1` is the governing standing risk. `sync_to_repo.sh` and `sdl-baseline/SKILL.md` are shipped too (`baseline:B2`, `baseline:B3`) but change only their human-facing instructions.

## Trust boundaries crossed <!-- SR-2 -->

No new boundary; an existing one moves. The change defines a class of diff that passes the gate with no reviewed SDL cycle behind it. That is the whole security question of this cycle, and `02` concentrates there.

## Data classification <!-- SR-1 -->

None. Public repo, no secrets — per `baseline.md`.

## External inputs introduced <!-- SR-2 -->

Two, both attacker-controllable in the adoption scenario, both already reachable by the validator today:

- The PR's file list, and which of those files are *additions* (`git diff --diff-filter=A`).
- The content of `.github/workflows/sdl.yml` in the PR's tree, parsed line-wise.

## Security requirements <!-- SR-3, SR-4 -->

1. The exemption is reachable at most once per repo, and only while the repo is genuinely adopting.
2. It admits no file the gate would otherwise treat as code, other than the generated `sdl.yml` itself.
3. The `sdl.yml` it admits delegates wholly to the reusable workflow — no inline steps, no other action.
4. It does not accept a stub baseline: waiving the cycle in exchange for an empty document waives the gate for nothing.
5. It widens nothing for a repo that already adopted SDL.
6. Failure messages here name the fix (`sdl-baseline`, `sdl-spec`) rather than describe the internal predicate.

## Related prior cycles

- `2026-06-10-adopt-sdl-governance` — this repo's own adoption, which paid the chicken/egg cost by writing a cycle for it.
- `2026-07-09-dep-update-tier` — the prior precedent for a diff class validated against something other than the four documents; its fail-closed classifier is the model followed here.
- `2026-07-10-plugin-self-adopt`, `2026-08-04-fix-gate-tag-triggers` — prior changes to the generated workflow.

## Carried-forward residual risks

None outstanding from prior cycles. `baseline:B1` is inherited and is why a change of this size carries a full cycle.
