# 02 — Threat Model

## Components and data flows

- `scripts/check_release.py` — gains two read-only checks. `check_validator_ref` reads `.github/workflows/sdl-validate.yml` and compares its `sdl_ref` default against `plugin.json`'s major; `check_caller_ref` does the same for `.github/workflows/sdl.yml`'s `uses:` ref. Both return error strings into the existing `errors` list; neither writes, forks, or fetches.
- `check_pr` — calls the validator-ref check on every run, before the shipped-content early return.
- `check_released` — calls the validator-ref check unconditionally, and the caller-ref check only once `main` has moved past the commit the current alias points at.

## Threats <!-- SR-2 -->

### T1 — The detector fails open and vouches for drift it never read

- **Category:** Tampering
- **Component / flow:** `sdl_ref_default` / `caller_ref` parsing a workflow file.
- **Description:** Both refs are hand-edited YAML. A parse that returns nothing on a shape it does not recognise, and treats "nothing" as "fine", converts the whole check into false assurance: CI prints `release state consistent` over a repo whose gate has been retired. That is worse than the gap it replaces, because the gap is at least known.
- **Likelihood / Impact:** low / medium
- **Mitigation:** every unread outcome is an error, not a skip — a missing file, an input with no `default:`, and a `uses:` line that names no ref each produce their own message. `sdl_ref` is read as the indented block under its own key and stops at the next sibling, so a neighbouring `default:` cannot be substituted for it; `base` sits immediately above `sdl_ref` in the real file and is the concrete case.
- **Mitigation type:** preventive
- **Defense in depth notes:** SD-2 — the unit fixture carries the real two-input shape rather than a minimal one, so a regression in the block scoping is caught by the tests that already existed as well as the new ones.

## Threats inherited from prior cycles <!-- SR-2 -->

`baseline:B5` (this repo moves an alias that consumers execute) is why the two refs matter at all; unchanged in scope, better observed. `2026-08-03-release-process` T3 (CI detects, the maintainer releases) is preserved exactly: both new checks are read-only and run in the same detect-only job.

## Out-of-scope threats

- Consumer repos pinned to a retired alias. Owned by those repos; `self-gate-v2:R2` records that detecting them needs a mechanism this repo does not have.
- A hostile edit to either workflow. Already covered by review and by the gate's treatment of workflow YAML as code; this check makes one class of such an edit noisy rather than silent, which is a side benefit, not the control.

## Noted for future cycles

- `check_caller_ref` is exempt on the release commit itself, which means a repo that never merges anything again would never be told its gate is retired. Acceptable — a repo with no commits has no gate runs to be wrong about — but if released-mode ever runs somewhere other than `main`, revisit the exemption.
- Deriving `sdl_ref` from `github.job_workflow_sha` (R3a's other option) would remove the hand-maintained ref rather than watch it. Still the better end state; this check is what makes the interim safe.
