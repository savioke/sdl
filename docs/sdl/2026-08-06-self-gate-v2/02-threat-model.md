# 02 — Threat Model

<!-- SR-2: Threat model. SD-1, SD-2: Secure design and defense in depth. -->

## Components and data flows

- `.github/workflows/sdl.yml` — one line changed: the `uses:` ref the caller
  resolves. No inputs, no secrets, no logic. The `on:` triggers are untouched.
- **Flow changed:** this repo's `pull_request` and `push` events now reach the
  2.0.0 reusable workflow instead of the 1.x one. Concretely that adds the
  resolve step and `--push` to runs in this repo, and makes `push` runs on
  `main` non-vacuous for the first time.
- `docs/sdl/baseline.md` — prose only. No component.
- Unchanged: the released artifacts, the marketplace manifest, `validate.py`,
  and `sdl-validate.yml` itself. Nothing a consumer receives changes.

## Threats <!-- SR-2 -->

### T1 — The self-gate stops gating without looking like it stopped

- **Category:** Repudiation (a control that reports success without running)
- **Component / flow:** `sdl.yml` `uses:` ref → the called reusable workflow
- **Description:** This one line decides whether this repo's own changes are
  validated at all, and by which version of the validator. A wrong ref is not
  self-announcing: the job is still named `validate`, still appears on every PR,
  and a reviewer scanning the checks list sees what they expect. The specific
  live instance is the one this cycle fixes — `@v1` was correct when written and
  became wrong the moment 2.0.0 shipped, and the evidence that it had gone wrong
  was a green check reading `no substantive code changes` on a merge that
  changed 21 files and 817 lines.
- **Likelihood / Impact:** medium / medium
- **Mitigation:** The ref was verified against the tree it names rather than
  against the tag name: `git show v2:.github/workflows/sdl-validate.yml`
  contains the resolve step and passes `--push`, and `git show
  v2:plugins/sdl/lib/validate.py` contains `cycle_in_diff` — so `@v2` is the
  2.0.0 gate and not a mislabelled tag. `@v2` is the moving major alias, the
  same ref consumers pin, so this repo cannot drift onto a build consumers never
  receive.
- **Mitigation type:** preventive
- **Defense in depth notes:** SD-2 — a ref that does not resolve is a hard
  workflow failure in GitHub, not a skipped job, so the loud failure mode covers
  typos; what it does not cover is a ref that resolves to the *wrong existing*
  tag, which is why the tree was read. And the change verifies itself: the PR
  carrying it is gated by `@v2`, so a `@v2` that cannot validate this repo
  cannot merge the commit that adopts it. `check_release.py --mode released`
  independently confirms `v2.0.0 = 059cf28b7` and that the marketplace manifest
  names the same release.

## Threats inherited from prior cycles <!-- SR-2 -->

- **`baseline:B5`** (moving major alias) applies unchanged in kind — this repo
  moves from one moving alias to another, not from a pinned ref to a moving one.
  Its wording is updated by this cycle to name `@v2`.
- **`baseline:B1`** (validator/workflow changes reach every consumer's CI) is
  *not* engaged: nothing consumers receive changes. What changes is that this
  repo now sits on the consumer side of that boundary, which strengthens B1's
  existing mitigation rather than widening it.
- **`2026-08-06-gate-direct-pushes:T1`** (a direct push mistaken for a reviewed
  one) and **`:T2`** (a stale cycle vouching for every push) now apply to this
  repo for real rather than in principle. Not re-litigated; this cycle is the
  first place they are live.
- **`2026-08-06-gate-direct-pushes:R3a`** (`sdl_ref` is a hand-maintained
  default that must track the workflow's own major) is the reason this ref bump
  is not the only version-coupled edit at a major. It stays open; see below.

## Out-of-scope threats

- What the `@v2` gate does once called — modelled in full by
  `2026-08-06-gate-direct-pushes`; this cycle only changes who calls it.
- Compromise of the `v2` alias itself (tag force-push by a repo admin): owned by
  GitHub repo permissions and `baseline:B5`, unchanged here.
- Documentation drift in `baseline.md` is not modelled as a threat — an
  inaccurate baseline misleads future cycles, but the correction is the change,
  not a control over it.
- The other savioke repos still calling `@v1`: they keep the pre-2.0 behavior
  (no direct-push gating) until re-pointed, which is a gap in those repos, owned
  by the maintainer and tracked outside this cycle.

## Noted for future cycles

- Every major now requires two coordinated edits in this repo — `sdl.yml`'s
  `uses:` ref and `sdl-validate.yml`'s `sdl_ref` default — and neither is
  checked against the other or against `plugin.json`. A `check_release.py`
  assertion that both name the current major would make the omission loud;
  deriving the validator checkout from `github.job_workflow_sha` would remove
  half of it entirely (`gate-direct-pushes:R3a`).
- The self-gate can only ever adopt a major *after* that major ships, so there
  is always a window in which this repo runs the previous gate. Today the window
  is closed by hand and by memory. If it is ever missed, nothing notices.
