# 02 — Threat Model

<!-- SR-2: Threat model. SD-1, SD-2: Secure design and defense in depth. -->

## Components and data flows

- `sdl-validate.yml` "Resolve what to validate" — new step. Reads the event
  name, `github.event.before`, `github.sha`, and a GitHub API response, and
  decides skip / validate-as-PR / validate-as-push.
- `sdl-validate.yml` "Run validator" — now receives its arguments through the
  environment rather than by `${{ }}` interpolation into the shell.
- `validate.py --push` — resolves the cycle from the diff (`cycle_in_diff`)
  instead of from `branch:` (`find_cycle_for_branch`).
- **New external input:** `repos/{repo}/commits/{sha}/pulls`, authenticated with
  the caller's `GITHUB_TOKEN`, whose answer decides whether the gate runs.
- **New flow:** direct push → previous-commit diff → cycle-carried-in-push check.
- Unchanged: the entire `pull_request` path, the release channel, and the
  per-cycle checks once a cycle is resolved.

## Threats <!-- SR-2 -->

### T1 — A direct push is mistaken for a reviewed one and skipped

- **Category:** Elevation of privilege (bypass of a required control)
- **Component / flow:** PR-association lookup → skip decision
- **Description:** The whole point of the push run is to catch code that reached
  the branch without PR review. If the lookup wrongly reports that a commit came
  from a merged PR — or if an error is read as "no work to do" — the change is
  skipped and the bypass succeeds silently, which is worse than the prior state
  because the run now *looks* like it checked something.
- **Likelihood / Impact:** low / high
- **Mitigation:** Skip requires a positive answer. The step captures the count of
  associated PRs filtered to `merged_at != null`, and skips only when that count
  is a known non-zero value. A failed call, a missing token, a permissions
  denial, or any unparseable output resolves to the literal `unknown`, which
  falls through to validating and prints why it could not tell. An open PR
  merely touching the commit does not count as review, because it has not merged.
- **Mitigation type:** preventive
- **Defense in depth notes:** SD-2 — branch protection is the actual prevention
  and is out of scope here; this control detects after the fact. Selecting on
  `merged_at` rather than parent count is load-bearing: squash and rebase merges
  produce single-parent commits and would be misread as direct pushes by a
  parent-count test — verified against real squash merges in `cli/cli` and
  `astral-sh/ruff`, both of which the API resolved to their merged PR.

### T2 — A stale cycle vouches for every later direct push

- **Category:** Repudiation (false evidence of review)
- **Component / flow:** `resolve_cycle` → `cycle_in_diff`
- **Description:** A direct push has no source branch for a cycle to declare, so
  the obvious implementation matches `branch: main`. That is unsound: the first
  cycle ever written for a push to `main` would satisfy the check for every
  subsequent push to `main`, indefinitely. The gate would report a cycle found
  and name a real folder, while the code in front of it had no evidence at all.
- **Likelihood / Impact:** medium / high
- **Mitigation:** On `--push` the cycle must appear in the diff being validated:
  `cycle_in_diff` collects cycle slugs from `docs/sdl/<slug>/…` paths in the
  push and requires one with a `.sdl-meta.yml`. Evidence has to arrive with the
  code it describes. Pinned by test, including the specific regression — an
  unrelated pre-existing `branch: main` cycle does not clear a later push.
- **Mitigation type:** preventive
- **Defense in depth notes:** SD-2 — `check_nonstub` still rejects a cycle whose
  artifacts are scaffolding, so carrying an empty folder does not satisfy the
  gate either.

### T3 — Workflow inputs reach the shell

- **Category:** Elevation of privilege (script injection)
- **Component / flow:** `workflow_call` inputs → `run:` block
- **Description:** The workflow interpolated `${{ inputs.base }}` directly into a
  `run:` script. Any repository may call this reusable workflow by design
  (`baseline:B4`), so the input is attacker-controllable, and interpolation
  happens before the shell parses the line — a crafted value executes commands
  in the runner with the calling repo's token.
- **Likelihood / Impact:** low / medium
- **Mitigation:** All values now reach the shell through `env:` and are
  referenced as quoted shell variables, so they are data rather than script
  text. The new resolve step follows the same rule for `github.event.before`,
  `github.sha`, and `github.repository`.
- **Mitigation type:** preventive
- **Defense in depth notes:** SD-2 — the blast radius was always the *caller's*
  own runner and token, not this repo's, so this is closing a self-harm vector
  rather than a cross-tenant one. `permissions:` is now declared explicitly and
  read-only.

## Threats inherited from prior cycles <!-- SR-2 -->

- **`baseline:B1`** (a change to `validate.py` or `sdl-validate.yml` runs in
  every consumer's CI) applies at full strength — both files changed, and this
  is a breaking change to gate behavior. Contained by the major-version
  contract: `v1` does not move, so no repo receives this until it re-points to
  `@v2` deliberately.
- **`baseline:B4`** (publicly-callable reusable workflow) is directly relevant
  and is narrowed by T3's fix rather than widened.
- **`baseline:B2`** (skill-instruction injection) fires its "any skill change"
  trigger: `sdl-spec` gained direct-push guidance. No new tool or capability;
  confirmed in scope, disposition unchanged.
- **`2026-08-04-fix-gate-tag-triggers`** established the vacuous-pass finding for
  tag pushes. This cycle applies it to the default branch; the branch filter it
  added stays, and its rationale comment is updated rather than removed.

## Out-of-scope threats

- Prevention of direct pushes: branch protection, owned by repo configuration.
  This gate detects a push that already landed and cannot block it.
- A malicious `github.event.before` value: it originates from GitHub's event
  payload, not from a user, and is checked for reachability with `git cat-file`
  before use.
- Denial of the gate by exhausting API rate limits: a failed lookup validates
  rather than skips, so the failure mode is more checking, not less.

## Noted for future cycles

- `sdl_ref` is a hand-maintained default that must be bumped in lockstep with
  every major, and nothing checks that it was. `github.job_workflow_sha` is the
  commit of the reusable workflow actually running, so deriving the checkout ref
  from it would make workflow and validator come from one commit by
  construction. Not done here: it is an unverifiable-by-inspection expression in
  the highest-blast-radius file in the repo, and this cycle already changes that
  file substantially.
- The generated `sdl.yml` hardcodes `branches: [main]`. A repo whose default
  branch is named otherwise gets no push run at all, and therefore silently
  keeps the pre-2.0 gap. Detecting the default branch at adoption time would
  close it.
- The push path validates only the head commit's PR association. A push
  containing several commits where only the tip came from a PR would be skipped
  wholesale; not reachable through the GitHub merge UI, but reachable by hand.
- If `check_pins` or any other network-dependent check is ever added to the
  gate itself, revisit T1's "uncertainty validates" rule — it is cheap here
  because validating costs nothing, and would stop being cheap if a network
  failure could fail an honest PR.
