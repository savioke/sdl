# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-08-06
- **Diff range:** 92cb993..HEAD (`origin/main...HEAD` at review time)

## Checks performed <!-- SVV-1, SVV-2 -->

### Input handling (three new parsers over diff and markdown)

- **Finding:** Verified positive. All three tools parse repo-local,
  already-trusted input (git's own diff output and files under `docs/sdl/`), so
  the exposure is malformed input rather than hostile input — an attacker able to
  supply either can already write the record directly (02, out-of-scope). Checked
  the failure modes rather than the happy path: a diff line that does not match a
  pin is skipped rather than partially interpreted; a pin with no version comment
  yields no row rather than a row with a blank version; an unpaired added action
  yields no row rather than an invented "from" version; and a same-version re-pin
  is correctly not a bump. The risk-table parser is anchored on the ID cell
  matching `R\d+` rather than on document position, so an unrelated table cannot
  be read as the risk register — verified with an `R2D2` decoy row. `carry_forward`
  is parsed in both its inline and block YAML forms.
- **References:** `plugins/sdl/lib/dep_facts.py:98-136`, `plugins/sdl/lib/open_risks.py:52-108`, `plugins/sdl/lib/test_dep_facts.py:29-84`, `plugins/sdl/lib/test_open_risks.py:45-115`

### Data and persistence (first programs to modify an audit artifact)

- **Finding:** Verified positive, and this is the change's main risk (T1). Both
  writers are bounded to a region they locate by anchor, and both fail loudly
  rather than silently: `fill_updates_table` raises `ValueError` when the
  `| package |` header is absent instead of returning the text unchanged, and
  `stamp` returns the labels it could not match so `main` exits 1. Confirmed by
  test that a table rewrite leaves the Checks boxes unchecked and the Notes
  section intact, that a stamp leaves findings and the residual-risk table
  untouched, and that re-running either replaces rather than appends (the
  `count=1` and the bounded row region). `re.sub` is called with a lambda
  replacement, so a value containing a backslash or backreference cannot corrupt
  the output — pinned by test, since a plain string replacement would be a
  natural and silently wrong refactor.
- **References:** `plugins/sdl/lib/dep_facts.py:146-162`, `plugins/sdl/lib/cycle_stamp.py:72-81`, `plugins/sdl/lib/test_dep_facts.py:139-171`, `plugins/sdl/lib/test_cycle_stamp.py:41-77`

### Build, CI, and supply chain

- **Finding:** Verified positive. Three new files ship inside `plugins/sdl/` and
  so reach consumers through the release channel (`baseline:B1`). Release
  bookkeeping done in the same PR per `docs/releasing.md` step 2: version 1.2.0 →
  1.3.0 with a matching changelog entry. Minor is the correct digit — the change
  adds capability and cannot turn a passing PR red, confirmed by the checking
  functions in `validate.py` being unchanged except for an additive capture group
  and by the pre-existing validator suite passing unmodified. None of the three
  tools runs in consumer CI; `sdl-validate.yml` has zero diff lines and still
  invokes only `validate.py`. Two CI enumerations that would have silently
  excluded the new files were found and fixed: the unit-test job listed test
  modules by hand (now discovery, so a future test file cannot be skipped) and
  the required-files check listed `lib/` scripts by hand (now includes all
  three). `check_release.py` needed no change — it matches on the `plugins/sdl`
  path prefix, so new files are covered automatically; verified by reading
  `SHIPPING_PATHS`. No new third-party action, network fetch, or install-script
  change.
- **References:** `.github/workflows/self-check.yml:24-33,112-121`, `plugins/sdl/.claude-plugin/plugin.json:5`, `CHANGELOG.md:13-68`, `scripts/check_release.py:44`

**Not applicable (no code in these areas):** network and transport, authentication and authorization, cryptography, secrets, logging and observability, concurrency and resource use, dependencies, frontend and browser-facing, native and lower-level.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

- Unit tests: `python3 -m pytest plugins/sdl/lib/` — 135 passed, up from 88. The
  47 new tests cover the three tools; the pre-existing 88 pass unmodified, which
  is the evidence that the `PIN_LINE_RE` change is behavior-preserving. Two of
  the new tests pin T3's fail-closed mitigation directly: an unrecognized version
  comment does not parse, and a pin the regex rejects escalates rather than
  passing the gate's pin check.
- CI smoke checks replicated locally: every `lib/*.py` parses under `ast.parse`,
  and all seven tools respond to `--help`.
- **End-to-end exercise of the routine tier, in a scratch git repo** — worth
  recording because the tier had never been run: `new_cycle.py --class
  dependency-update` → `dep_facts.py --write` → `validate.py` on a synthetic
  two-action Dependabot diff produced a record the gate accepted (4 checks
  passed), with versions matching the diff exactly. The same repo with a
  `v6.2.0 → v7.0.0` bump exited 2 and named the major-bump trigger. This is the
  first evidence that the dependency-update path works end to end.
- No shell script changed, so `shellcheck` coverage is unaffected. The
  `self-check.yml` edits were validated by parsing the workflow as YAML.
- Secret scan over the diff: no key, token, password, or private-key material.

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | `dep_facts` and `validate` identify a pinned `uses:` line through one regex, so the record's versions and the diff-side major check cannot disagree — a defect in `PIN_LINE_RE` is not surfaced by the two sides differing. Narrow in practice: the regex fails closed, so an unrecognized comment escalates rather than producing a wrong row; `check_dep_record` reads the record with separate code; and `check_pins.py` resolves comments against upstream tags wherever a repo runs it. | low | accept | Revisit on any non-additive change to `PIN_LINE_RE`. It now has two callers with different consequences — a loosening made for the generator would also widen what the gate accepts — so such a change needs tests on both sides. |
| R2  | `dep_facts.py` generates no rows for language-ecosystem manifests, and this repo has none — so the manifest path is exercised only by unit test, never against a real npm/Go/Python lockfile diff. The failure mode is visible (named manifests, no rows) rather than silent, but the first consumer repo with a lockfile is the real trial. | low | mitigate-later | Confirm on the first dependency PR in a repo that has a lockfile; if the output misleads, the fix is the reminder text, not the parser. |
| R3  | The `--write` paths were exercised end to end in a scratch repo and by unit test, but no dependency record generated this way has yet been read and merged by a human. T1's mitigation is preventive and T2's is a printed reminder; both assume an author who reads the output. | low | mitigate-later | Read the first real generated record against its diff before treating the path as settled. Pairs with `2026-08-06-use-sub-agent-for-dep-update:R2`, which this cycle narrows but does not close. |

Standing conditions are not repeated here. `baseline:B2` fired its "any skill
change" revisit trigger (three skills changed) and was re-confirmed in scope with
disposition unchanged; `baseline:B1` applies to the three newly shipped files and
is contained by the existing controls — see 02, "Threats inherited".
