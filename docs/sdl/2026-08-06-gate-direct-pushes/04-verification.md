# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-08-06
- **Diff range:** 27ba9da..HEAD (`origin/main...HEAD` at review time)

## Checks performed <!-- SVV-1, SVV-2 -->

### Authentication and authorization (a control decides whether to run at all)

- **Finding:** Verified positive. The skip decision is the security-relevant
  branch in this change, and it is written so that only a positive, specific
  answer skips: the count is filtered to `merged_at != null`, so an open PR
  merely touching the commit does not count as review, and skip requires a value
  that is neither `unknown` nor `0`. Every other outcome — non-zero exit,
  permissions denial, empty output, malformed JSON — collapses to `unknown` and
  validates, printing why it could not tell. Confirmed by reading the `||
  PRS=unknown` fallback and the two-condition guard. Also confirmed the choice
  of signal empirically rather than from documentation: parent count, the
  obvious alternative, misclassifies squash and rebase merges as direct pushes.
  Real squash merges (`astral-sh/ruff@fce9727c8`, `cli/cli@608dff7b8`, both
  single-parent) resolved correctly to their merged PRs via the API, and a
  commit never associated with a PR returned `0`.
- **References:** `.github/workflows/sdl-validate.yml:64-78`

### Input handling (event payload consumed as a diff base)

- **Finding:** Verified positive. `github.event.before` is validated before use
  in two ways: compared against the 40-zero sentinel that GitHub sends on branch
  creation, and tested for reachability with `git cat-file -e "${BEFORE}^{commit}"`,
  which covers a force-push whose prior tip no longer exists. Each produces an
  explicit skip with a stated reason rather than a git error or a silent pass. In
  `validate.py`, `cycle_in_diff` derives slugs only from paths with more than
  three components under `docs/sdl/`, so `INDEX.md` and `baseline.md` cannot be
  read as cycle folders — pinned by test — and requires `.sdl-meta.yml` to
  exist, so an empty directory in the diff does not satisfy the check.
- **References:** `.github/workflows/sdl-validate.yml:79-88`, `plugins/sdl/lib/validate.py:236-250`

### Build, CI, and supply chain

- **Finding:** Verified positive, with one defect found and fixed (below). Both
  changed files execute in every consumer's CI with the consumer's token
  (`baseline:B1`), and this is a deliberate breaking change, so containment is
  the version contract: 2.0.0, `v1` left in place, upgrade documented. Verified
  the `pull_request` path is untouched — the resolve step returns the input base
  and `push=false` for every non-push event, so PR runs execute the same command
  as before. Workflow inputs no longer interpolate into `run:` (T3);
  `permissions:` is declared read-only. Embedded shell was extracted and passed
  through `shellcheck -S warning` clean, and the workflow parses as YAML.
- **References:** `.github/workflows/sdl-validate.yml:16-18,55-61,96-104`, `plugins/sdl/.claude-plugin/plugin.json:5`, `CHANGELOG.md:13-79`

**Not applicable (no code in these areas):** data and persistence, network and transport (no new listener; the one outbound call is to the GitHub API over the runner's own client), cryptography, secrets, logging and observability, concurrency and resource use, dependencies, frontend and browser-facing, native and lower-level.

## Defects found and fixed during review <!-- DM-1 -->

- **`set -e` would have skipped the validator it was configuring.** The "Run
  validator" step first read `[ "$PUSH" = "true" ] && args+=(--push)`. Under
  `set -euo pipefail` a false test makes that line return non-zero, ending the
  step successfully-looking and never invoking `validate.py` — so every
  `pull_request` run, the primary gate, would have silently validated nothing
  while reporting green. Rewritten as an `if` block with a comment recording
  why. This is the same failure shape the cycle exists to fix, reintroduced one
  layer up.
- **`sdl_ref` still defaulted to `v1`, pairing a v2 workflow with a v1
  validator.** `sdl-validate.yml` checks out `savioke/sdl` at `inputs.sdl_ref`
  for the validator code. Left at `v1`, a consumer calling `sdl-validate.yml@v2`
  would run the new workflow against the old `validate.py`, which has no
  `--push` flag — every direct push would die on an argparse error. The failure
  is loud and fails closed (a red gate, not a bypass), but it would have broken
  the release for every consumer on the day they upgraded. Default moved to
  `v2`, with a comment stating that it must track the workflow's own major.
  Found while working out the release procedure, not by a test — recorded in
  02 "Noted for future cycles" as an argument for deriving the ref from
  `github.job_workflow_sha` instead of a hand-maintained default.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

- Unit tests: 144 in `plugins/sdl/lib/` (191 including `scripts/`), up from 135.
  Nine new tests cover the direct-push path and the empty-diff messages,
  including the T2 regression directly: an unrelated pre-existing `branch: main`
  cycle does not clear a later push, while the same diff passes on a PR.
- **End-to-end in a real git repo**, since the unit tests mock git: a direct push
  of code with no cycle fails with the new message; the same push carrying an
  authored cycle passes all four checks; a *second* direct push relying on that
  now-existing cycle fails, confirming T2 is closed in practice and not only in
  the unit; and a docs-only direct push passes with no cycle required.
- `new_cycle.py --slug` exercised in a scratch repo: two same-day cycles on
  `main` scaffold with distinct descriptive slugs, a duplicate slug is still
  refused, and the feature-branch guard still fires.
- `shellcheck -S warning` clean over the workflow's extracted `run:` blocks.
  YAML parses; `permissions` confirmed present and read-only.
- The reported message that prompted this cycle was re-checked against the new
  code: `origin/main and HEAD are the same commit — nothing to compare`.
- Secret scan over the diff: no key, token, password, or private-key material.
  `GH_TOKEN` is bound from `github.token` in `env:` and never echoed.

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | The generated consumer `sdl.yml` hardcodes `branches: [main]`. A repo whose default branch is named otherwise gets no push run and silently retains the pre-2.0 gap — the failure is invisible, since an absent trigger produces no output to notice. | medium | mitigate-later | Detect the default branch during `sync_to_repo.sh` adoption and write it into the generated workflow. Until then the generated file carries a comment telling the adopter to change it. |
| R2  | The whole push path is unexercised against real GitHub events. The PR-association call, the `before` sentinel, and the force-push branch were verified against the live API and in scratch repos, but no actual `push` event has run this workflow. A mistake in the resolve step most likely shows as validating when it should skip (noisy, safe) rather than the reverse. | medium | mitigate-later | Watch the first direct push and the first PR merge after this repo moves to `@v2`; confirm the skip message names the PR and that a direct push is caught. |
| R3a | `sdl_ref` must be bumped by hand at every major, and nothing verifies it matches the workflow's own version. This cycle's near-miss (see Defects) is the first instance; the next major has the same trap. | medium | mitigate-later | Derive the checkout ref from `github.job_workflow_sha` so the two cannot diverge, or add a `check_release.py` assertion that `sdl_ref`'s default matches `plugin.json`'s major. |
| R3  | Only the head commit's PR association is checked. A push containing several commits where just the tip came from a PR would be skipped wholesale. Not reachable through GitHub's merge UI, but reachable by hand. | low | accept | Revisit if a repo adopts a workflow that pushes mixed batches to the default branch. |
| R4  | `validate.py` is stdlib-only, but the gate as a whole now depends on `gh` and the GitHub API at runtime. An API outage makes every push run validate rather than skip — safe, but it means a merge could fail the push run for want of a cycle declaring `branch: main`. | low | accept | Failure direction is toward checking. Revisit if outage-driven noise is ever observed. |

Standing conditions are not repeated here. `baseline:B1` applies at full strength
and is contained by the major-version contract; `baseline:B4` is narrowed by T3
rather than widened; `baseline:B2` fired its "any skill change" trigger and was
re-confirmed in scope — see 02, "Threats inherited".
