# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-08-06
- **Diff range:** 059cf28..HEAD (`origin/main...HEAD` at review time)

## Checks performed <!-- SVV-1, SVV-2 -->

### Build, CI, and supply chain (a CI ref that selects the gate)

- **Finding:** Verified positive. `@v2` was confirmed to be the 2.0.0 gate by
  reading the tree behind the tag, not by trusting the name: `git show
  v2:.github/workflows/sdl-validate.yml` contains the "Resolve what to validate"
  step, `permissions:`, and the `args+=(--push)` branch, and `git show
  v2:plugins/sdl/lib/validate.py` contains `cycle_in_diff` / `resolve_cycle`.
  `sdl_ref` at `v2` defaults to `v2`, so this repo — which passes no inputs —
  gets a validator from the same major as the workflow calling it, which is the
  R3a near-miss the prior cycle fixed. Independently, `check_release.py --mode
  released` reports `v2.0.0 = 059cf28b7` and confirms the marketplace manifest
  names that release, so the alias, the immutable tag, and the plugin channel
  all point at one commit. `v2.0.0` is an annotated, SSH-signed tag (local `git
  tag -v` cannot complete only because `gpg.ssh.allowedSignersFile` is unset on
  this workstation; the signature block is present).
- **References:** `.github/workflows/sdl.yml:15`, `v2:.github/workflows/sdl-validate.yml:17,48,108`

### Authentication and authorization (unchanged, confirmed unchanged)

- **Finding:** Verified positive by inspection of the whole diff. The caller
  passes no `secrets:`, no `with:`, and no `permissions:` — it is a bare `uses:`
  — so the called workflow runs under its own declared read-only permissions
  (`contents: read`, `pull-requests: read`, added in 2.0.0). Moving from `@v1`
  to `@v2` therefore *narrows* what this repo's gate job can do, since 1.x
  declared no `permissions:` block and inherited the workflow-default token.
- **References:** `.github/workflows/sdl.yml:10-15`

**Not applicable (no code in these areas):** data and persistence, network and
transport, cryptography, secrets, logging and observability, concurrency and
resource use, input handling, dependencies, frontend and browser-facing, native
and lower-level. This diff is one workflow ref and prose.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

- Unit tests: 191 pass (144 in `plugins/sdl/lib/`, 47 in `scripts/`). No test
  changed; none was expected to, since no Python changed.
- Both workflow files parse as YAML; `sdl.yml` still declares exactly one job,
  `validate`, and its `on:` triggers are byte-identical to before.
- `gen_index.py --check` reports `docs/sdl/INDEX.md is current` after
  regeneration for this cycle.
- The validator was run against this branch in both modes after committing (a
  run against uncommitted work compares `base...HEAD` and passes vacuously —
  the failure this repo shipped 2.0.0 to stop reporting):
  - PR path: `cycle found: docs/sdl/2026-08-06-self-gate-v2`, all four checks
    pass.
  - Push path (`--push`): passes on the same diff, because the cycle is carried
    in it — which is the `cycle_in_diff` contract behaving as specified.
- Evidence of the defect this cycle closes, from CI rather than reconstruction:
  run 31082092951, the `push` run on `main` for the 2.0.0 merge, executed
  `validate.py --base "origin/main"` under `@v1` and reported `[ok ] no
  substantive code changes; cycle presence not required` for a merge of 21 files
  and 817 lines. That run is the last one this repo will make under the 1.x gate.
- Secret scan over the diff: no key, token, password, or private-key material.
  The diff adds no `env:`, `with:`, or `secrets:` entry of any kind.

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | `gate-direct-pushes:R2` is only half-closed by this cycle. The PR gate under `@v2` is exercised by this very PR, but the `push`-on-`main` path — the PR-association lookup and the `before` diff base — cannot run until this PR merges, which is after the artifact is written. The first merge is the first real execution. | medium | mitigate-later | Read the `sdl` push run on the merge commit: it must report a skip that names the PR, not a validation. If it validates instead, the lookup is failing safe (noisy) and needs a fix; if it validates *and* fails, treat as a release defect and fix forward. |
| R2  | Adopting a major requires two edits in this repo that nothing cross-checks — `sdl.yml`'s `uses:` ref (this cycle) and `sdl-validate.yml`'s `sdl_ref` default (`gate-direct-pushes:R3a`, still open) — plus the ref in every other consumer repo. Nothing detects a repo left on a retired major; an old alias keeps resolving and keeps reporting green under the old rules. | medium | mitigate-later | Extend `check_release.py` to assert that `sdl.yml`'s ref and `sdl_ref`'s default both name `plugin.json`'s major. Detecting stale *consumers* needs a different mechanism and is not in this repo's reach today. |
| R3  | This repo now takes alias-move risk (`baseline:B5`) in earnest: a bad 2.x release reaches its own CI immediately, with no pinned fallback. Deliberate — it is the whole point of the self-gate — and recorded so it is not mistaken for an oversight. | low | accept | Failure is loud and the remedy is `git tag -f v2 <good-tag>`, documented in `docs/releasing.md`. Revisit if a release ever does break this repo's CI. |

Standing conditions are not repeated here. `baseline:B5` is engaged and its
wording is updated by this cycle; `baseline:B1` is not engaged — nothing
consumers receive changes.
