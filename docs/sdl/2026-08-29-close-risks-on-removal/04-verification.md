# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-08-29
- **Diff range:** b6df566..HEAD (`origin/main...HEAD` at review time)

## Checks performed <!-- SVV-1, SVV-2 -->

### Agent-executed instructions (baseline:B2)

- **Finding:** The nine markdown files are the whole security surface of this diff. Read in full: the added text adds no tool invocation, no command, no file path the skills write to, and no new input to any parser — it constrains what an agent may record, and always in the direction of requiring a visible artifact edit rather than permitting a silent one. Closure is bound to the reviewed diff (`sdl-review/SKILL.md:104`) and to a `carry_forward:` ref (`:111`), both of which land in the PR diff next to the deletion they claim; T1's mitigation is therefore present as written.
- **References:** `plugins/sdl/skills/sdl-review/SKILL.md:104-105,111,131`, `plugins/sdl/skills/sdl-threat-model/SKILL.md:19,84,90-91`, `plugins/sdl/skills/sdl-spec/SKILL.md:84`, `plugins/sdl/skills/sdl-baseline/SKILL.md:56`, `plugins/sdl/templates/docs-sdl/04-verification.md:39-58`, `plugins/sdl/templates/docs-sdl/01-requirements.md:37-40`, `plugins/sdl/templates/docs-sdl/02-threat-model.md:30-33,43-45`, `plugins/sdl/templates/baseline.md:47-53`

### Build, CI, and supply chain

- **Finding:** Verified positive. `scripts/test_check_release.py` runs only in this repo's `self-check.yml`; the change adds two `git config` calls on a throwaway fixture repo and one `TemporaryDirectory` flag. No workflow, action pin, permissions block, or secret is touched, and no assertion is weakened — the failure it fixes was in teardown, after the test's assertions had already run. `python3 -m unittest discover -s scripts`: 55 passed.
- **References:** `scripts/test_check_release.py:250-263`

**Not applicable (no code in these areas):** input handling, data and persistence, network/transport, authn/authz, cryptography, secrets, logging and observability, concurrency and resource use, dependencies, frontend.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

Existing CI coverage only: `self-check.yml` runs the validator and `check_release` unit tests and `shellcheck` on scripts; the SDL gate runs `validate.py` against this cycle. No new tooling. Stdlib-only, no SBOM delta.

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | T2 is mitigated only from this side: when code moves to another repo, this repo records the handoff and closes the item, but cannot verify the receiving repo ever opened it. Accepted — a marker here that no cycle can ever close is the noise this change removes, not a control. | low | accept | none; the receiving repo's own SDL adoption owns it |
| R2  | The convention is verified by reading the instructions, not by watching an agent apply them. The first real removal cycle is the first test of whether "closed by removal" is written as one past-tense line rather than a hedged residual row. | low | mitigate-later | Read the first cycle that closes a risk by removal against its diff; if the line drifts back toward hedging, tighten the wording in `sdl-review`. |

Standing conditions are unchanged: this diff inherits `baseline:B2` (skill files as executable spec) and adds nothing to the register.

## Risks closed by removal

None — this cycle removes no code. The section is exercised as scaffolding for future cycles, per the template.
