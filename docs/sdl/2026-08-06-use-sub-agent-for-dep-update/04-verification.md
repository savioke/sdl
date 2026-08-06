# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-08-06
- **Diff range:** `origin/main...HEAD` plus the uncommitted working tree — at review time nothing was committed on this branch, so the review was performed against the working tree. The gate must be re-run after the commit; see "Static analysis" below.

## Checks performed <!-- SVV-1, SVV-2 -->

### Concurrency and resource use (new async task spawned per invocation)

- **Finding:** Verified positive. `context: fork` spawns exactly one subagent per skill invocation, bounded by construction — no loop, no fan-out, and `background: true` returns via task notification rather than holding the caller's turn. The fork shares no mutable state with the primary conversation; its only outputs are files under `docs/sdl/<cycle>/` and its final report. Specifically checked for recursive spawn, where a forked agent re-invokes a skill and multiplies agents: the skill contains no self-invocation, and the one place it previously reached for another skill is the escalation path, which this diff changes to forbid invocation outright.
- **References:** `plugins/sdl/skills/sdl-dep-update/SKILL.md:4-6`, `:31-34`

### Build, CI, and supply chain

- **Finding:** Verified positive. The changed file is a shipped integrity asset (`baseline:B2`) that reaches consumers through the release channel, so release bookkeeping is part of the security-relevant surface: version bumped 1.1.0 → 1.2.0 with a matching changelog entry in the same PR, per `docs/releasing.md` step 2. Minor is the correct digit — the change adds capability and cannot turn a previously-passing PR red, confirmed by `git diff --stat` returning zero changed lines across `plugins/sdl/lib/`, `plugins/sdl/templates/`, `.github/`, and `scripts/`. No new CI step, third-party action, network fetch, or install-script change.
- **References:** `plugins/sdl/.claude-plugin/plugin.json:5`, `CHANGELOG.md:13-47`, `plugins/sdl/skills/sdl-dep-update/SKILL.md:4-6`

**Not applicable (no code in these areas):** input handling, data and persistence, network and transport, authentication and authorization, cryptography, secrets, logging and observability, dependencies, frontend and browser-facing, native and lower-level.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

- Plugin unit tests: `python3 -m pytest plugins/sdl/lib/` — 88 passed. No Python changed this cycle; run as a regression check.
- No shell script changed, so `shellcheck` coverage is unaffected.
- `validate.py --base origin/main` currently reports "no substantive code changes; cycle presence not required" and exits 0. **This is vacuous**: the validator reads `git diff base...HEAD`, which does not see the uncommitted working tree. `is_skill()` classifies `SKILL.md` as code (confirmed directly against the classifier), so the gate will require this cycle once the change is committed. Re-run after commit and before opening the PR.
- Secret scan over the diff: no key, token, password, or private-key material introduced.

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | The frontmatter contract (`model` / `context: fork` / `background`) was verified by reading the harness's skill-frontmatter schema, not by executing the skill end-to-end. If a key is wrong or unsupported in a consumer's Claude Code build, the observed failure is that the skill runs inline as before — the gate and the record are unaffected — but the intended benefit silently does not materialize. | low | mitigate-later | Confirm on the next real Dependabot PR that the skill forks and reports via notification; if it does not, the fix is frontmatter, not process. |
| R2  | Record honesty under Sonnet at default effort is unmeasured. T1's mitigation is detective (operator read-before-push plus the gate), so a degraded record is caught rather than prevented — but the detection depends on a human actually reading it, which is the same assumption the routine tier already made. | low | mitigate-later | Read the first two or three records authored this way against their diffs before treating the tier as settled. `effort:` is the dial if quality falls short; deliberately unset this cycle (see 03, "Deviations"). |

Standing conditions are not repeated here. `baseline:B2` (skill-instruction injection) fired its "any skill change" revisit trigger this cycle and was re-confirmed in scope with disposition unchanged — see 02, "Threats inherited". `baseline.md`'s component list still names only Claude Code / Copilot as executing agents while consumers now also use Codex and Antigravity; that understates the standing exposure model and is a `sdl-baseline` update, not a risk this diff introduces.
