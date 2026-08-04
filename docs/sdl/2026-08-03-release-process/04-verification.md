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
- **References:** `scripts/check_release.py:150-177`, `:268-275`; `scripts/test_check_release.py` (`FetchManifest`, `test_non_utf8_body_returns_error_not_exception`, `test_unreachable_marketplace_warns_but_does_not_fail`, `test_disagreeing_marketplace_fails`).

### CI / supply chain <!-- T3 -->

- **Finding:** verified. The new `release` job runs `check_release.py` only, which performs no writes and needs no `permissions:` grant beyond the default read; no secret is referenced by any workflow in this repo. Drift detection was exercised end to end against the fixture: after a successful release the released-mode check reported consistent, and committing a change to `plugins/sdl/lib/validate.py` without releasing was reported as "1 shipped file(s) changed since v1.0.0 and are not released". Released mode runs on the daily schedule rather than on push — see the deadlock defect below.
- **References:** `.github/workflows/self-check.yml` (`release` job, `schedule` trigger), `scripts/check_release.py:217-277`.

### Defects found and fixed during review <!-- DM-1 -->

#### Released-mode detection moved off push to `main` (changes R5)

- **Finding:** released mode originally ran on every push to `main`, where its conditions are all transient until the release happens. It therefore reddened `main`, and `release.sh` refuses a commit whose checks are red (SR-3) — the two controls were mutually exclusive, and the only way out would have been `SDL_RELEASE_SKIP_CI=1` on every release, hollowing out that precondition.
- **Fix:** released mode runs on `schedule`/`workflow_dispatch` only. PR mode is unaffected. This is a deliberate reduction in detection latency for a forgotten release, from immediate to up to a day — accepted and recorded as **R5**, not a free fix.
- **References:** `.github/workflows/self-check.yml` (`release` job); `docs/releasing.md`, "What CI checks"; R5.

#### T1's mitigation was total over parsing but not over reading

- **Finding:** `check_manifest` trusted the manifest's *shape* once `json.loads` succeeded, so a well-formed-but-wrong-shaped document crashed the daily job instead of reporting drift — the exact failure T1 exists to prevent, and reachable from a legitimate manifest, since the marketplace schema permits a bare-string `source`. In the same path, `check_released` discriminated on `manifest is None`, so a served body of `null` was misreported as an outage and skipped the comparison entirely, failing open.
- **Fix:** every field is type-checked before use, and fetch failure is discriminated on the error rather than the value. `02`'s T1 mitigation text was corrected — it had claimed the coverage this defect disproved.
- **References:** `scripts/check_release.py:78-122`, `:268-275`; `scripts/test_check_release.py::MalformedManifest`; T1 in `02-threat-model.md`.

#### The manifest write could strand a release past the point of no return (T3)

- **Finding:** the manifest rewrite ran *after* the tag push and assumed each entry and its `source` were objects. Since `vX.Y.Z` is immutable and `release.sh` refuses to re-release it, a raise there published both tags with the distribution channel still pointing at the old ref and no way to re-run — breaking this script's own stated invariant that all refusals precede any mutation.
- **Fix:** the manifest is cloned and validated at step 3, before the CI check, the prompt, and any tag. `check` and `write` share one validator, so passing the preflight guarantees the write cannot fail on shape. Verified by execution: eleven malformed manifests each refused with no tag in the origin; negative-controlled — without the preflight all eleven push both tags and then fail.
- **References:** `scripts/release.sh:79-144`, `:210-215`; T3 in `02-threat-model.md`.

#### PR mode crashed on a base version that is present but not orderable

- **Finding:** `check_pr` guarded only `base_version is None` before comparing, so a base declaring an unparseable version (`1.0`, `v1.0.0`, `latest`) raised `TypeError` out of a required check. The guard that was present, `if new is None`, was dead — the head version is already validated above — so the check guarded the safe operand and left the reachable one open.
- **Fix:** guard on `base_parsed`, covering absent, missing, and unorderable base versions identically with a note naming the value. An unparseable *head* version is still an error. Negative-controlled.
- **References:** `scripts/check_release.py:181-214`; `scripts/test_check_release.py::PrMode`.

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
