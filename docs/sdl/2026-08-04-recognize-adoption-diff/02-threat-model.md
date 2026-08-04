# 02 — Threat Model

## Components and data flows

- `check_cycle_present` (`validate.py`) — unchanged for the two existing outcomes (docs-only diff passes, matching cycle passes); on the no-cycle path it now consults `check_adoption` before failing.
- `check_adoption` — reads the PR's file list, the set of *added* paths (`git diff --name-only --diff-filter=A base...HEAD`), the checked-out `docs/sdl/baseline.md`, and the checked-out `.github/workflows/sdl.yml`. Returns `None` (not adoption — fall through to the ordinary requirement), a passing `Result`, or a failing one.
- `is_adoption_workflow` — line-wise parse of `sdl.yml`. Rejects any `run:` and any `uses:` that is not the sdl reusable workflow.

The adversary model is the one that matters for a gate: **the author of the PR being validated controls all of this input**, including the workflow's content and which files the diff adds. Nothing here is trusted; every predicate has to hold against a diff crafted to satisfy it.

## Threats <!-- SR-2 -->

### T1 — Adoption exemption used to land unreviewed CI behavior

- **Category:** Elevation of privilege / Tampering
- **Component / flow:** `check_adoption` → `is_adoption_workflow`
- **Description:** The exemption's whole purpose is to let a `.github/workflows/` file through without a cycle. A PR that satisfies the shape but ships a workflow of its own design gets arbitrary steps running in CI with the repo's `GITHUB_TOKEN`, reviewed by no one — the exact scenario `code_changed()` treats workflows as code to prevent. This is the primary threat of the change.
- **Likelihood / Impact:** low / high
- **Mitigation:** the admitted workflow must be the generated caller: `is_adoption_workflow` requires at least one `uses:` matching `savioke/sdl/.github/workflows/sdl-validate.yml@<ref>` and rejects the file if *any* line carries an inline `run:` or a `uses:` that does not match. The match is on the whole line, so a trailing comment or a decorated ref fails rather than passes — fail-closed in the same spirit as the dependency classifier (`2026-07-09-dep-update-tier`, T1). A caller-only workflow has no steps of its own to subvert; its behavior is entirely the reusable workflow's, which lives here and is gated here.
- **Mitigation type:** preventive
- **Defense in depth notes:** the path allowlist (T2) admits only `.github/workflows/sdl.yml`, so a second workflow file cannot ride along; and the file must be an *addition*, so this cannot be used to edit an existing gate.

### T2 — Code smuggled into the adoption PR

- **Category:** Tampering
- **Component / flow:** `check_adoption` path allowlist
- **Description:** If "adopting SDL" waived the cycle for the whole diff, the cheapest way to land unreviewed code in any repo would be to bundle it with the enrollment.
- **Likelihood / Impact:** low / high
- **Mitigation:** the loop is an allowlist over every changed path, not a sample: anything outside `docs/sdl/` that is not the added `.github/workflows/sdl.yml` returns `None`, and the ordinary "no cycle" failure stands. Files under `docs/sdl/` are the artifacts themselves and are never code (`is_skill` deliberately excludes them — pinned by an existing test).
- **Mitigation type:** preventive
- **Defense in depth notes:** the exemption is a pass on *one* check, not a bypass of `main()`; it does not touch the dependency-class path or the artifact checks.

### T3 — Exemption reused after adoption

- **Category:** Elevation of privilege
- **Component / flow:** `check_adoption` gating on `BASELINE in added`
- **Description:** A once-per-repo waiver that is in fact reachable on every later PR is not a waiver, it is a hole. An enrolled repo's PRs must not be able to re-enter it.
- **Likelihood / Impact:** low / high
- **Mitigation:** the exemption requires `docs/sdl/baseline.md` to be an *addition* in this diff. On any repo that has adopted, the baseline is already in the base branch, so it can never appear as added and the function returns `None` on its first check. The workflow must likewise be an addition, so the interesting variant — delete the baseline in a docs-only PR (which passes the gate today), then "re-adopt" — still cannot reach the exemption: on that second PR `sdl.yml` is modified, not added. Deleting `sdl.yml` to make it re-addable is itself a workflow change, which needs a cycle.
- **Mitigation type:** preventive
- **Defense in depth notes:** the requirement is on the *diff*, not on repo state, so it cannot be satisfied by editing files in the PR.

### T4 — Stub baseline traded for the waiver

- **Category:** Repudiation
- **Component / flow:** `check_adoption` → `is_nonstub`
- **Description:** Accepting the scaffold's placeholder baseline would waive the cycle in exchange for a document asserting nothing, and would leave the repo permanently without the standing context every later cycle references — with the evidence trail claiming it was reviewed at adoption.
- **Likelihood / Impact:** medium / low
- **Mitigation:** `is_nonstub` against the shipped `templates/baseline.md` (byte-equality) plus the comment-scaffolding heuristic already used for cycle artifacts. A stub is a hard failure naming the `sdl-baseline` skill, not a fall-through.
- **Mitigation type:** preventive
- **Defense in depth notes:** the existing `baseline_warning` still fires on later PRs, so a baseline that is gutted after adoption is visible in CI output.

## Threats inherited from prior cycles <!-- SR-2 -->

`baseline:B1` (a validator change runs in every consumer's CI) applies with more force than usual: this is a gate-widening change, the class the compatibility contract calls minor precisely because it cannot fail a passing PR — but which can, if wrong, pass a PR that should have failed. The unit tests added in `03` pin every rejection case for that reason, mirroring `2026-07-09-dep-update-tier` T1's treatment of the dependency classifier.

## Out-of-scope threats

- A repo that never adopts SDL is ungated regardless; the exemption changes nothing for it. Owned by onboarding, not the validator.
- Deleting `.github/workflows/sdl.yml` disables the gate for subsequent PRs. Pre-existing (the deletion itself is a workflow change and needs a cycle, but nothing stops a merge with the check absent); owned by branch protection on the consuming repo, per `baseline:B1`.
- `git diff --diff-filter=A` reflects the checkout CI performs; a caller checking out something other than the PR merge commit already breaks every other check. Owned by `sdl-validate.yml`.

## Noted for future cycles

- `is_adoption_workflow` hard-codes `savioke/sdl`. A fork of the governance repo generating its own caller falls out of the exemption and back to needing a cycle. Fail-closed and correct today (there is one governance repo); revisit if a fork is ever supported, taking the org from the caller rather than a constant.
- The exemption recognizes a diff shape rather than a declared class, unlike `class: dependency-update` in `.sdl-meta.yml`. That is forced — there is no meta file to declare anything in yet. If a third such class appears, consider whether shape-matching generalizes or whether adoption should write a marker file.
