# 02 — Threat Model

<!-- SR-2: Threat model. SD-1, SD-2: Secure design and defense in depth. -->

## Components and data flows

- `plugins/sdl/skills/sdl-dep-update/SKILL.md` — frontmatter selects a new execution mode: forked subagent, Sonnet, backgrounded. Same repo checkout, same workstation privileges, same tool set.
- **Report flow (changed).** Skill output no longer streams into the operator's conversation; it returns once, as a task notification.
- **Escalation flow (changed).** Previously skill → `sdl-spec` in-process. Now skill → report → operator → `sdl-spec` in the main conversation.
- Unchanged: the inputs read (diff, manifests, lockfiles, templates, upstream advisory/release-note lookups), the artifacts written, and the gate that validates them.

## Threats <!-- SR-2 -->

### T1 — Attested record authored without live observation

- **Category:** Repudiation
- **Component / flow:** `sdl-dep-update` → `docs/sdl/<cycle>/dep-update.md`
- **Description:** The record's checked boxes are an attestation that specific checks ran. Authored inline, the operator saw the checks happen and could interrupt mid-course. Authored detached, the record arrives finished, so an overclaim — a box checked for a check that did not run, or a version transcribed wrongly — is no longer observable while it is being made. Running on a smaller model widens the window in which such an overclaim is plausible.
- **Likelihood / Impact:** low / medium
- **Mitigation:** The human attestation step is unchanged and explicit: the operator reads the record before pushing (`docs/developer-guide.md`, "read the record before you push"). The new step 5 requires the report to state which checks ran and what each returned, and to name anything unverified rather than omitting it — so the notification is checkable against the record rather than merely asserting success.
- **Mitigation type:** detective
- **Defense in depth notes:** SD-2 — `validate.py`'s `check_dep_record` independently rejects a stub record, a record declaring no updates, and any declared major bump; `check_dep_class_diff` rejects a diff that is not dependency-shaped. A record that overclaims about *tier* fails the gate regardless of what the agent wrote.

### T2 — Escalation trigger swallowed by the detached agent

- **Category:** Tampering (control bypass)
- **Component / flow:** triage step → `sdl-spec`
- **Description:** The pre-change instruction told the skill to *run* `sdl-spec` when a triage trigger fires. `sdl-spec` is an interview and cannot run from a background agent with no operator present; attempting it would fail or produce a degraded cycle, so an escalation-tier change (major bump, new dependency, changed action `owner/repo`) could end up with routine-tier evidence or none.
- **Likelihood / Impact:** low / medium
- **Mitigation:** The instruction now stops and reports which trigger fired, names `sdl-spec` as the operator's next step, and explicitly forbids running it — escalation returns to the main conversation, where the interview belongs.
- **Mitigation type:** preventive
- **Defense in depth notes:** SD-2 — if the agent ignored the instruction and wrote a routine record anyway, `check_dep_record` rejects a declared major bump and `check_dep_class_diff` rejects a non-dependency diff. The PR fails the gate rather than merging.

## Threats inherited from prior cycles <!-- SR-2 -->

- **`baseline:B2`** (skill-instruction injection) applies, and its stated revisit trigger — "any skill change" — fires this cycle. The change does not widen it: the skill file remains gated as code by `is_skill()`, PR review is unchanged, and no new tool or capability is granted. Confirmed in scope; disposition unchanged.
- **`2026-07-09-dep-update-tier` T3** (manifest *content* can still carry executable config; accepted at the routine tier and owned by policy, not the classifier) is unchanged. This cycle changes who authors the record, not what the tier accepts.

## Out-of-scope threats

- Vendor dependence on a specific model tier: `model: sonnet` is Claude-Code-specific, and agents that do not implement the key ignore it and run the skill inline as before. There is no failure mode for the gate to catch. Owned by policy, not a control here.
- Fork tool scope: the forked agent runs with the default agent tool set. The skill declared no `allowed-tools` before or after this change, so this is not a privilege increase — verified-negative, recorded so the next maintainer need not re-derive it.

## Noted for future cycles

- If `sdl-review` is ever forked, T1's analysis does not transfer unchanged: it makes security judgments rather than running fixed checks, and its useful inputs include conversational design context a fresh fork will not have.
- If this skill ever gains an `allowed-tools` restriction, re-check that the fork honors it — a fork's tool set comes from the agent type, not from the ambient session.
- `baseline.md` still describes skills as "executed by Claude Code / Copilot"; Codex and Antigravity are now in use among consumers, so the standing exposure model understates the agent surface.
