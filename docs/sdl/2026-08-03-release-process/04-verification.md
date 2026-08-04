# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-08-03
- **Diff range:** f670bdf (main)..working tree, pre-commit

## Checks performed <!-- SVV-1, SVV-2 -->

Mitigations were exercised, not just read: `release.sh` was run against a throwaway fixture (a bare origin, a fake marketplace repo, and a stubbed `gh`) so every refusal path and the full happy path executed for real.

### Command execution / external inputs (new shell script) <!-- T2 -->

- **Finding:** verified by execution. With `version` set to `1.0.0; touch /tmp/PWNED_BY_SDL`, the release aborted at the semver gate and the file was never created; `../../evil` and `1.0` were likewise refused before any git operation. The validated string is the only source of `$tag` and `$alias_tag`, the latter by parameter expansion rather than re-parsing.
- **References:** `scripts/release.sh:57-60`; refusal messages reproduced in all three cases.

### Command execution / privileged operations (release path) <!-- T3 -->

- **Finding:** verified by execution. Refusals fire before any mutation: dirty tree, wrong branch, `main` ahead of/behind `origin/main`, missing `CHANGELOG.md` entry, and pre-existing `v1.0.0` each aborted with a specific message and left no tag, commit, or remote change. Re-running after a successful release refused with "Released versions are immutable". The happy path produced exactly the intended four artifacts: `v1.0.0` and `v1` at the same commit in the origin, an annotated tag whose message is the changelog entry, and a marketplace commit setting `version` 1.0.0 and `source.ref` `v1.0.0` with the file's key order and formatting preserved.
- **References:** `scripts/release.sh:44-51`, `:65-78`, `:185-188`, `:204-209`, `:210-228`.

### File I/O with user-controlled paths <!-- T3 -->

- **Finding:** verified. The only writes outside the repo are into a `mktemp -d` directory removed by an `EXIT` trap; the manifest path is a constant joined to that directory, never derived from input. The manifest rewrite refuses (non-zero, no commit) if no plugin entry matches the name.
- **References:** `scripts/release.sh:32-34`, `:143-144`, `:210-215`.

### External HTTP calls <!-- T1 -->

- **Finding:** verified by unit test. HTTPS with default certificate verification, a 30 s timeout, and a 1 MB cap applied *before* parsing; oversize bodies are refused unparsed. Transport failure, HTTP error, oversize, malformed JSON, and **non-UTF-8 bytes** all return an error value rather than raising, and released mode downgrades an unreachable manifest to a note while still failing on a fetched-and-disagreeing one — confirmed by two tests asserting opposite outcomes for those two cases.
- **Non-UTF-8 bodies, raised in PR review as a suspected crash:** not a defect. The `body.decode("utf-8")` is inside the `try`, and `UnicodeDecodeError` subclasses `ValueError`, which the handler catches — so an undecodable body already returned `(None, "UnicodeDecodeError fetching <url>")`. Confirmed by executing `fetch_manifest` against three undecodable bodies rather than by reading the hierarchy. No behavior change was needed, but the coverage was implicit enough that a careful reader concluded the opposite, so it is now explicit: a comment names both `ValueError` subclasses that reach the handler and why, and a regression test asserts the three cases. The test was negative-controlled — narrowing the handler to `json.JSONDecodeError` makes all three subcases error with the escaped exception.
- **References:** `scripts/check_release.py:150-177`, `:268-275`; `scripts/test_check_release.py` (`FetchManifest`, `test_non_utf8_body_returns_error_not_exception`, `test_unreachable_marketplace_warns_but_does_not_fail`, `test_disagreeing_marketplace_fails`).

### CI / supply chain <!-- T3 -->

- **Finding:** verified. The new `release` job runs `check_release.py` only, which performs no writes and needs no `permissions:` grant beyond the default read; no secret is referenced by any workflow in this repo. Drift detection was exercised end to end against the fixture: after a successful release the released-mode check reported consistent, and committing a change to `plugins/sdl/lib/validate.py` without releasing was reported as "1 shipped file(s) changed since v1.0.0 and are not released". Released mode runs on the daily schedule rather than on push — see the deadlock defect below.
- **References:** `.github/workflows/self-check.yml` (`release` job, `schedule` trigger), `scripts/check_release.py:217-277`.

### Defects found and fixed during review

#### Release deadlock: green-CI precondition vs. released-mode check

- **Finding:** released mode originally ran on every push to `main`. After a merge, the declared version has no tag yet, so the check failed and `main` went red — while `release.sh` refuses to release a commit whose checks are not green (SR-3). The two rules were mutually exclusive: every merge would have blocked the release that was supposed to follow it, and the only way out would have been `SDL_RELEASE_SKIP_CI=1` on every release, hollowing out the precondition. Found when walking the merge-to-release sequence end to end, after the tooling was otherwise complete.
- **Fix:** released mode now runs only on `schedule` and `workflow_dispatch`. Between a merge and its release, every released-mode condition is transient by design (no tag, manifest not yet bumped, shipped files newer than the tag), so the check has nothing true to say until the release has happened. On the daily run, an outstanding release is a genuine signal. PR mode is unaffected and still gates every PR.
- **References:** `.github/workflows/self-check.yml` (`release` job, `Released state is consistent` step condition and comment); `docs/releasing.md`, "What CI checks"; residual risk R5.

#### Diff range: shipped-change detection

- **Finding:** shipped-change detection originally used a two-dot diff (`base..HEAD`), which compares trees rather than the branch's own changes: any change `main` made to `plugins/sdl/` after the branch point would have been attributed to the PR, demanding a version bump for a diff that shipped nothing. Found while running PR mode against this branch, fixed to three-dot (matching `validate.py`), and regression-tested with a fixture where the base branch ships something after the branch point.
- **References:** `scripts/check_release.py:135-142`; `scripts/test_check_release.py::PrMode::test_shipped_change_made_on_the_base_after_branching_is_not_ours`.

#### Unchecked types when reading the fetched manifest (T1)

- **Finding:** raised in PR review. `check_manifest` treated the parsed manifest as well-shaped after `json.loads` succeeded: `(entry.get("source") or {}).get("ref")` raises `AttributeError` on any truthy non-dict `source`, and `manifest.get("plugins", [])` raises if the top level is not an object or `plugins` is not a list. The T1 mitigation stopped one step short — it made *parsing* total but not *reading*, so a manifest that parsed and then disagreed in shape crashed the daily job instead of reporting drift, which is the failure mode T1 exists to prevent. Not merely hypothetical: the marketplace schema permits `source` to be a bare URL string, so a legitimate manifest in that form crashed the check.
- **Fix:** every access is type-checked before use — top level, `plugins`, each entry, and `source`. A non-object `source` now yields a distinct message naming the type received rather than a confusing `ref None`. Seven test cases added covering a string source, other scalar and list sources, a missing source, a non-object top level, a non-list `plugins`, non-object entries within `plugins`, and a non-string `version`. `fetch_manifest`'s return type was corrected from `dict | None` to `object` — the annotation had asserted the very guarantee that was missing.
- **References:** `scripts/check_release.py:78-122`, `:150`; `scripts/test_check_release.py::MalformedManifest`; threat T1 mitigation text in `02-threat-model.md`.

#### A manifest body of literal `null` was classified as an outage (T1)

- **Finding:** found while fixing the defect above, in the same code path. `check_released` discriminated on `if manifest is None` to decide whether the fetch had failed. `json.loads("null")` returns `None`, so a served body of `null` was indistinguishable from a transport failure: the check would report "marketplace manifest unreachable, not checked: None" and skip the comparison entirely. That inverts T1's intended failure direction — a manifest that *was* successfully fetched and *does* disagree would be silently downgraded to a note, and the note names no cause.
- **Fix:** discriminate on `fetch_error is not None` instead. The value and the error are now independent, so a `null` body reaches `check_manifest` and is reported as drift, while a genuine fetch failure is still only a note. Two tests assert the opposite outcomes.
- **References:** `scripts/check_release.py:268-275`; `scripts/test_check_release.py::ReleasedMode::test_a_manifest_body_of_literal_null_is_drift_not_an_outage`, `::test_a_genuine_fetch_failure_is_still_only_a_note`.

#### PR mode crashed on a base version that is present but not orderable

- **Finding:** raised in PR review, reproduced against a scratch repo. In `check_pr`, `base_version is None` was the only guard before `new <= old`, so a base whose `plugin.json` declared a version that exists but does not parse (`1.0`, `1.0.0-rc1`, `v1.0.0`, `latest`) made `old` `None` and raised `TypeError: '<=' not supported between instances of 'tuple' and 'NoneType'`. The guard that *was* there — `if new is None` — was dead code: the head version is parsed and returned on at the top of the function, so `new` could never be `None`. The check guarded the operand that was already safe and left the reachable one open. Impact is a required PR check failing with a traceback instead of an actionable message, on a diff whose author did not write the offending history; the likely trigger is a base branch predating strict versioning, i.e. exactly the onboarding case.
- **Fix:** parse both sides once (`head_parsed`, `base_parsed`) and guard on `base_parsed is None`, which now covers "no `plugin.json`", "no version", and "version not orderable" identically — a note and a skipped increase check, per the reviewer's suggestion. The note names the offending value so the skip is not silent. The dead `new is None` branch is gone; an unparseable *head* version is still an error, since that is the author's own work.
- **Verified:** the original reproduction now reports `no comparable version at main ('1.0'); skipping increase check` and exits 0. Negative-controlled — restoring the old condition makes all six subcases of the new test error with the original `TypeError`.
- **References:** `scripts/check_release.py:181-214`; `scripts/test_check_release.py::PrMode::test_unorderable_base_version_skips_the_check_instead_of_crashing`, `::test_base_without_a_plugin_json_at_all_still_skips`, `::test_unparseable_head_version_is_still_an_error`.

#### The marketplace manifest edit could strand a release past the point of no return (T3)

- **Finding:** raised in PR review as a clarity issue — the rewrite assumed each `plugins[]` entry was an object and `entry["source"]` was absent or an object, so a malformed manifest would raise `AttributeError`/`TypeError` with little context. Investigating the consequence made it a correctness defect rather than a message-quality one: the rewrite was step 6, *after* step 5 had pushed `vX.Y.Z` and force-moved `vX`. Since `release.sh` refuses to re-release an existing immutable tag, a raise there left the release half-done — tags published, manifest untouched, and the script unable to run again. That also broke this script's own documented invariant, "all refusals happen before any mutation" (03, secure coding practices). A latent hole beyond the reported ones: `entry.setdefault("source", {})["ref"]` raises on an explicit `"source": null`, because the key exists and `setdefault` returns the `None`.
- **Fix:** the parse, the type checks, and the entry lookup moved into a `manifest_py` shell function called in two modes, and the manifest is now cloned and validated at step 3 — before the CI check, before the confirmation prompt, and before any tag exists. `check` and `write` run identical validation, so a manifest that passes the preflight cannot fail the write for shape reasons. Checks: top level is an object, `plugins` is an array, exactly one entry matches the plugin name (zero lists the names that *were* found; more than one is refused rather than silently taking the first, as the old `break` did), and `source` is an object. A missing or null `source` is refused rather than synthesized — writing a bare `{"ref": …}` would publish a manifest that resolves to nothing. The step-7 failure message now names the exact manual repair and says not to re-run. The confirmation banner gained the manifest's current version and ref, so the change is visible before it is approved.
- **Verified by execution.** A fixture (bare origin, fake marketplace repo, stubbed `gh`) ran eleven malformed manifests — string/null/missing/list `source`, non-array `plugins`, missing `plugins`, array top level, non-object entries, no matching plugin, duplicate entries, invalid JSON — plus the happy path. Every refusal aborted with **no tag in the origin**, and the happy path produced both tags and a correctly rewritten manifest with key order and formatting preserved. Negative-controlled: with the preflight removed, all eleven push `v1.0.0` and `v1` and *then* fail, reproducing the stranded state exactly.
- **References:** `scripts/release.sh:79-144` (preflight and `manifest_py`), `:210-215` (write, with the recovery message); `docs/releasing.md`, "What the script does".

**Not applicable (no code in these areas):** persistence/SQL, deserialization of untrusted formats, cryptography, authn/authz, secrets handling, logging/PII, frontend, native, dependency additions.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

- `shellcheck scripts/*.sh plugins/sdl/lib/*.sh` — clean (CI-enforced).
- `python -m unittest discover -s scripts -p 'test_*.py'` — 47 tests, pass.
- Existing suite `lib.test_validate lib.test_check_pins lib.test_new_cycle lib.test_gen_index` — 78 tests, pass; unaffected by this cycle.
- `gen_index.py --check` — current. `plugin.json` and the marketplace manifest parse as JSON.
- No dependency changes, no SBOM delta.

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | Releases are unsigned until the maintainer configures `user.signingkey`. `release.sh` warns and continues rather than blocking, so the attributability control that `baseline:B1` names as its revisit path is not yet in force. Setup is documented (`docs/releasing.md`, "Tag signing"). | medium | mitigate-later | verify at the next release that the tag is signed; make signing mandatory when a second maintainer joins |
| R2  | The first release is the first real exercise of the procedure against GitHub: `gh api .../check-runs` output shape and `gh repo clone` behavior were verified against a stub, not the live API. A mismatch stops the release with an error; it cannot half-release, since the tag push precedes the manifest edit and each step is idempotent-by-refusal. | low | mitigate-later | confirm during the 1.0.0 release; fix forward if the API shape differs |
| R3  | `plugin-self-adopt:R1` remains open and is retargeted from 0.7.0 to `v1.0.0`: the plugin-cache execution path has still never been exercised from a published release. This cycle changes what the marketplace serves (an immutable tag rather than `main`), so the untested path changed shape. | low | mitigate-later | the planned end-to-end test when the next repo is onboarded |
| R4  | The Copilot/clone channel still tracks `main`, so those developers can run skills that no release has shipped. Accepted while that population is one or two people who update deliberately. | low | accept | revisit if the clone-based population grows; point `install.sh` at the latest tag |
| R5  | "Merged but never released" is detected by the daily scheduled run rather than instantly, so shipped content can sit undelivered for up to a day before anything says so. This is the cost of the deadlock fix below; releasing immediately after merge is what actually prevents it. | low | accept | revisit if releases routinely lag merges — a scheduled run more than once a day is the cheap tightening |
