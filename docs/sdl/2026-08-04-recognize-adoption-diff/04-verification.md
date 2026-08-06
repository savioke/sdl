# 04 — Verification

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-08-04
- **Diff range:** main...HEAD

## Checks performed <!-- SVV-1, SVV-2 -->

### Gate logic — the exemption's boundary (T1, T2, T3, T4)

- **Finding:** each mitigation was exercised against a real git repo, not only unit tests. A scratch repo enrolled by running the shipped `sync_to_repo.sh` and filling the baseline passes with `adoption PR: baseline authored, no cycle required` (exit 0) — the field-reported failure, reproduced and cleared. The same repo with the scaffold's stub baseline fails with the message naming `sdl-baseline` (T4). Adding `lib/app.py` or a second workflow to the adoption diff returns to the ordinary missing-cycle failure (T2). The T3 re-entry path was walked end to end: delete `baseline.md` in a docs-only PR (passes today, as expected — deleting a doc is not code), merge, then re-add the baseline together with a hostile `sdl.yml` carrying `- run: curl evil`; the second PR fails, because `sdl.yml` is modified rather than added and the diff never reaches the exemption. A caller-only `sdl.yml` with an extra job appended is rejected by `is_adoption_workflow` on either the `run:` or the foreign `uses:` (T1).
- **References:** `plugins/sdl/lib/validate.py:286-345`; `plugins/sdl/lib/test_validate.py:234-317` (`AdoptionDiff`, 11 cases).

### CI / supply chain

- **Finding:** the exemption is one `Result` on one check; `main()` is otherwise untouched, so `cycle` stays `None` on an adoption PR and the artifact and dependency-class checks are unreachable rather than skipped-with-a-pass. `check_cycle_present`'s two pre-existing outcomes are unchanged, and its new arguments are threaded from values `main()` already computed — no new call to git beyond `added_files`, which reuses `run()` and the same `base...HEAD` range. Consumer-visible surface (the generated workflow, `sdl-validate.yml`, permissions) is unchanged; this release ships validator logic only.
- **References:** `plugins/sdl/lib/validate.py:222-224`, `:330-345`, `:378`.

### Input handling

- **Finding:** the only untrusted parse is the line-wise read of `sdl.yml`. It is read as text with `errors="replace"`, never YAML-loaded, so no parser is introduced on attacker-controlled input. Both regexes are anchored and quantifier-flat (no nesting), so a pathological workflow file cannot cause backtracking blowup; an unparseable or unmatched line rejects rather than being skipped.
- **References:** `plugins/sdl/lib/validate.py:61-68`, `:286-299`.

### Documentation of the security control

- **Finding:** the instruction order in `sync_to_repo.sh` and `sdl-baseline` was inverted (commit the scaffold, then fill the baseline), which produced the stub-baseline failure as the *documented* path. Both now say fill first, commit together, and state that a pushed stub fails. `sdl-baseline` also says explicitly not to scaffold a cycle to get around it — the workaround this change exists to remove.
- **References:** `plugins/sdl/lib/sync_to_repo.sh:71-86`; `plugins/sdl/skills/sdl-baseline/SKILL.md:27`; `docs/developer-guide.md:51-53`; `docs/admin-setup.md:35-39`.

**Not applicable (no code in these areas):** persistence, network/transport, authentication/authorization, cryptography, secrets handling, logging/PII, concurrency, dependencies, frontend, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

All suites pass: `test_validate.py` 55 (11 new), `test_check_pins.py` 10, `test_gen_index.py` 8, `test_new_cycle.py` 15, `test_check_release.py` 47. `shellcheck` clean on `sync_to_repo.sh`. No dependency change; stdlib only.

## Residual risks <!-- DM-1 -->

| ID | Description | Severity | Disposition | Carry-forward target |
|----|-------------|----------|-------------|----------------------|
| R1 | The exemption trusts that a caller-only `sdl.yml` is safe because its behavior is the reusable workflow's. True today; it stops being true if `sdl-validate.yml` ever grows inputs the caller can pass (`with:`/`secrets:`), which `is_adoption_workflow` does not inspect. | low | accept | Revisit in any cycle that adds inputs to `sdl-validate.yml`; that cycle must also constrain them here. |
| R2 | Adoption is recognized by diff shape, not by a declared class, because there is no `.sdl-meta.yml` to declare one in yet. Shape-matching is more brittle than a declaration if the scaffold's file set changes. | low | accept | Revisit if `sync_to_repo.sh` ever writes a different set of files; the allowlist in `check_adoption` must move with it. |
| R3 | This widening reaches every consumer when `v1` moves, per `baseline:B1` and the minor-release contract. Verified as widening-only (nothing previously green can turn red), but a defect in the new predicate would silently pass an adoption-shaped PR in any repo. | low | accept | Standing; already tracked as `baseline:B1`. Rejection cases are pinned by tests so a future loosening is deliberate. |
