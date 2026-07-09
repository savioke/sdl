# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-07-09
- **Diff range:** origin/main..HEAD, working tree included (changes uncommitted at review time)

## Checks performed <!-- SVV-1, SVV-2 -->

### New file I/O with user-controlled paths (input handling)

- **Finding:** the branch name is the only untrusted input reaching a filesystem path. `slugify` (`lib/new_cycle.py:38-52`) takes the last path segment, lowercases, and strips everything outside `[a-z0-9-]`, so separators and dots cannot survive into the folder name; inputs normalizing to nothing raise instead of defaulting. `scaffold` additionally refuses existing folders and branches with existing cycles (`lib/new_cycle.py:78-85`), and `main` errors when the target repo lacks `docs/sdl/`. Verified by tests: traversal inputs (`../../etc/passwd`, `a\..\b`, …) and containment under `docs/sdl/`. `gen_index.py` derives no path from input — it writes only `docs/sdl/INDEX.md` (`lib/gen_index.py:126`).
- **References:** `lib/new_cycle.py:38-52,78-88`, `lib/gen_index.py:126`, `lib/test_new_cycle.py`

### Command execution with user-controlled arguments (input handling)

- **Finding:** no shell invocation. `new_cycle.py` reuses `validate.py`'s `run()` (list-arg `subprocess.run`, no `shell=True`) solely for `git rev-parse`; a failure surfaces as a clean error telling the user to pass `--branch`. `gen_index.py` spawns nothing.
- **References:** `lib/new_cycle.py:25,111-115`, `lib/validate.py:183-187`

### New CI workflow steps (build, CI, and supply chain)

- **Finding:** `self-check.yml` gains two steps — the new test modules on the unittest line and `gen_index.py --check` — inside the existing `validator` job. No new action, no version change to the pinned actions, no secret use (`--check` is read-only), and the required-files list gains the two tools. The reusable consumer-facing workflow `sdl-validate.yml` is untouched, so nothing changes in consumer CI.
- **References:** `.github/workflows/self-check.yml:22-24,72-73`

### Agent-instruction changes (baseline:B2 surface)

- **Finding:** three skill files edited. The `sdl-spec` fast path adds capability to skip the interview but is explicitly scoped (small, already implemented, no new trust boundary/external input) with a mandatory drop-back, and states the artifacts meet the same standard — wording reviewed against T2. The `sdl-review` and `sdl-dep-update` edits replace hand-performed mechanical steps with tool invocations and remove no checks: the dep-update triage, deterministic checks, and validator steps all remain. No skill instructs bypassing `validate.py`.
- **References:** `skills/sdl-spec/SKILL.md` (Fast path, step 1), `skills/sdl-review/SKILL.md` (step 6), `skills/sdl-dep-update/SKILL.md` (step 4)

**Not applicable (no code in these areas):** data and persistence, network and transport, authentication and authorization, cryptography, secrets, logging and observability, concurrency and resource use (regexes verified linear), dependencies (none added), frontend, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

- `ruff check lib/` — clean.
- `python3 -m unittest lib.test_validate lib.test_check_pins lib.test_new_cycle lib.test_gen_index` — 78 tests pass (55 pre-existing as regression, 23 new).
- Live exercise: scaffolded full and dependency-update cycles in a throwaway repo, verified layout, meta content, refusal paths, and INDEX generation; `gen_index.py --check` verified both directions. The live run caught and fixed one real bug pre-review (greedy regex swallowing the line after a bare `pr:` key — now a regression test).
- `python3 -m json.tool plugins/sdl/.claude-plugin/plugin.json` — valid (version bump only).
- CI once pushed: `self-check.yml` (tests + INDEX check + shellcheck + pins) and the self SDL gate (`sdl.yml`).

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | The fast-path boundary ("small, no new trust boundary") is judgment, not mechanically enforced — a misjudged fast path produces plausible-but-thin artifacts (T2). Detection relies on human PR review of artifacts beside the diff. | low | accept | revisit if review ever catches a rubber-stamped fast-path cycle, or if contributor base widens beyond the maintainer |
| R2  | `gen_index.py` summaries use a first-sentence heuristic; an abbreviation mid-sentence (e.g. "e.g. ") truncates the INDEX summary early. Cosmetic — INDEX is informational and the cycle files remain authoritative. | low | accept | none |
