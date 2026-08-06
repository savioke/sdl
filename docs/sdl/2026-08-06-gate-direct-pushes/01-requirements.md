# 01 — Requirements

<!-- SR-1: Product security context. SR-2: Threat model inputs. -->

## Summary

The gate has never validated a direct push. On a push to the default branch it
diffed `origin/main` against `HEAD` — the same commit, because the push had
already landed — found nothing, and reported "no substantive code changes."
Green on every push in every repo, forever. Code reaching `main` without a pull
request was therefore ungoverned, and the standing assumption that all changes
land via PR (`baseline.md`, standing security requirements) had nothing enforcing
it. This cycle makes the push run real: it skips commits that arrived through a
merged PR, validates the rest against the previous commit, and requires a direct
push carrying code to carry its own SDL cycle.

## Scope

In scope: base and event resolution in `sdl-validate.yml`, a `--push` mode in
`validate.py` that resolves the cycle from the diff rather than the branch, an
honest message for an empty diff, `new_cycle.py --slug` so successive cycles on
one branch are possible at all, the generated consumer workflow's comment, and
skill and developer-guide guidance for the direct-push path.

Out of scope: branch protection, which is the actual prevention for direct
pushes — this gate detects after the fact and cannot block a push that already
landed. Also out of scope: repos whose default branch is not named `main`; the
generated workflow still hardcodes `branches: [main]` and now says so in a
comment.

## Assets touched <!-- SR-1 -->

`\.github/workflows/sdl-validate.yml` and `plugins/sdl/lib/validate.py` — both
named in `baseline.md` as integrity assets, and both executing in **every
consumer repo's CI with that repo's `GITHUB_TOKEN`**. This is the highest
blast-radius surface the baseline identifies (`baseline:B1`).

New for this cycle: the workflow makes an **authenticated GitHub API call**
(`repos/{repo}/commits/{sha}/pulls`) using the caller's token, and its result
decides whether validation runs at all. That is a new input to a gate decision,
from outside the checkout.

## Trust boundaries crossed <!-- SR-2 -->

No new boundary in the baseline's terms, but one existing crossing gains a
dependency: the gate's verdict in a consumer repo now depends on a GitHub API
response, not only on the checkout. The reusable workflow remains publicly
callable by any repo (`baseline:B4`), and now declares
`permissions: contents: read, pull-requests: read`.

## Data classification <!-- SR-1 -->

Unchanged. No secrets, no PII. The API call reads pull-request metadata for the
calling repo using that repo's own token; nothing is written and nothing leaves
the runner. The token is never echoed — it is passed to `gh` through the
environment.

## External inputs introduced <!-- SR-2 -->

- `github.event.before` — the commit the branch pointed at before the push. Used
  as the diff base. Validated as reachable before use; all-zeros (branch
  creation) is handled explicitly.
- The PR-association API response. Consumed as a count of merged PRs; any error
  or unparseable result is treated as "unknown" and resolves to validating.

## Security requirements <!-- SR-3, SR-4 -->

- A code change reaching the default branch without PR review must not pass the
  gate silently.
- Uncertainty must resolve toward validating. A failed or ambiguous PR lookup
  may never be read as "already gated."
- The push path must not re-implement the PR path's rules. Anything already
  validated as a PR is skipped, not re-judged under different logic.
- No previously-passing pull request may fail as a result of this change.
- Workflow inputs must not be interpolated into shell; any repo may call this
  workflow.

## Related prior cycles

- `2026-08-04-fix-gate-tag-triggers` — established that a push-triggered run
  diffing against `origin/main` yields a vacuous pass. It fixed tags; this cycle
  applies the same finding to the default branch.
- `2026-08-06-determinism-wins` — added the tooling this builds on, and the
  cycle whose merge surfaced the misleading message.
- `2026-06-10-adopt-sdl-governance` — the adoption exemption the push path must
  not break.

## Carried-forward residual risks

None claimed. Nine items are open per `open_risks.py`; none is addressed here.
