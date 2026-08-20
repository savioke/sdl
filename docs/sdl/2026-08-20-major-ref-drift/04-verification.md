# 04 — Verification

## Review pass

- **Reviewer:** sdl-review + eastagiletracker
- **Date:** 2026-08-20
- **Diff range:** c4ce162..HEAD (`origin/main...HEAD` at review time)

## Checks performed <!-- SVV-1, SVV-2 -->

### Input handling (two new parsers over workflow YAML)

- **Finding:** Verified positive. Both parsers read repo-local, already-trusted
  files — the same two workflow files CI executes — so the exposure is malformed
  input, not hostile input. The failure modes were checked rather than the happy
  path: an `sdl_ref` input with no `default:` returns `None` and is reported, a
  file with no `sdl_ref` input at all returns `None` and is reported, and a
  sibling input's `default:` is not readable as `sdl_ref`'s because the scan
  stops at the first line indented no deeper than the key. The real file has
  `base` with its own `default: origin/main` immediately above `sdl_ref`, so the
  unit fixture carries that exact shape rather than a minimal one. `caller_ref`
  is anchored on the full `savioke/sdl/.github/workflows/sdl-validate.yml@`
  path, so an ordinary `uses: actions/checkout@…` line is not mistaken for it.
- **References:** `scripts/check_release.py:93-121`, `scripts/test_check_release.py:69-100`

### Build, CI, and supply chain

- **Finding:** Verified positive. Nothing shipped changed: the diff touches
  `scripts/` and `docs/` only, `plugin.json` is untouched, and no version bump
  or changelog entry is due (`check_release.py --mode pr` reports "no shipped
  content changed"). The checks are detect-only and hold no credential, so
  `2026-08-03-release-process` T3 is preserved. The release procedure was walked
  against the new code: on the release commit the caller-ref check is exempt, so
  `release.sh` step 8 still ends green after a major; on the first commit after
  it, the check fires and keeps firing until the gate moves.
- **References:** `scripts/check_release.py:281`, `:328`, `:364-365`, `docs/releasing.md:65-71`

### Regression surface (a detective control that must not start failing)

- **Finding:** Verified positive. The `git`-backed fixture now writes both
  workflow files so it models the repo it stands in for; all 47 pre-existing
  tests pass unmodified against it, which is the evidence that no condition
  passing before fails now. On the real tree both modes still report `release
  state consistent`. The five behavioural tests were observed red before green:
  with the three `errors.extend(...)` call sites removed and the functions left
  in place, the six parser tests still pass and all five mode-level tests fail.
- **References:** `scripts/test_check_release.py:242-292`, `:387-427`, `:544-573`

**Not applicable (no code in these areas):** persistence, network/transport, authentication/authorization, cryptography, secrets handling, logging/PII, concurrency, dependencies, frontend, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

Unit tests: 60 in `scripts/` (up from 47), 144 in `plugins/sdl/lib/` unchanged.
`gen_index.py --check` current. Every `plugins/sdl/lib/*.py` still parses and
answers `--help`. `validate.py` passes on this branch. No dependency change, so
no SBOM delta. `check_pins.py` was not exercised here — it needs network the
review host does not have, and this diff changes no pin.

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | The stale-*consumer* half of `self-gate-v2:R2` is untouched: nothing detects another repo left calling a retired alias. This cycle closes only the two refs inside this repo. | medium | defer | Needs a mechanism this repo does not have — a consumer census, or the gate reporting its own alias. Re-record at the next major rather than losing it. |
| R2  | The caller-ref exemption is expressed as "`main` is the alias commit", which is a proxy for "the release just happened". A released-mode run against a checkout that is not `main` would read the proxy wrongly and skip the check. Not reachable today: CI runs it on `main` and `release.sh` refuses any other branch. | low | accept | Revisit if released-mode ever runs somewhere other than `main`. |
