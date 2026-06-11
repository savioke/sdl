# 02 — Threat Model

## Components and data flows

- **Skill instructions** (`sdl-spec`, `sdl-threat-model`, `sdl-review` `SKILL.md`) — agent-executed text; this diff adds a "Proceeding through the cycle" principle and reframes handoffs from passive to active. Crosses the standing **repo → developer/CI agent** boundary (baseline:B2).
- **Verification template** (`04-verification.md`) — sign-off checklist removed.
- **62443 mapping** (`docs/62443-mapping.md`) — four evidence pointers re-aimed at PR/CI/git.
- **Plugin manifests** (`plugin.json`, `marketplace.json`) — version 0.2.0 → 0.3.0; distribution only.

No runtime, no inputs, no secrets. Exposure model per `baseline.md`.

## Threats <!-- SR-2 -->

### T1 — Reduced human checkpoints weaken process assurance

- **Category:** Repudiation (loss of recorded human accountability / oversight)
- **Component / flow:** SDL process — sign-off removal in the verification template combined with the skill autonomy principle.
- **Description:** Removing the sign-off checklist and instructing the agent to advance through SDL steps without asking could, together, let a cycle complete and merge with weaker recorded human review than before — most plausibly in a consumer repo that does not enforce PR review, or if the autonomy text is later broadened beyond writing artifacts into taking code/merge actions.
- **Likelihood / Impact:** low / medium
- **Mitigation:** The actual review-and-accountability control is unchanged. Responsibility is recorded by PR approval and commit/merge history — now the explicit 62443 evidence for SM-2, SR-5, SD-3, DM-2 — and the CI gate (`lib/validate.py`) independently requires all four artifacts present and not byte-equal to the templates. The agent cannot approve or merge its own PR, and CI runs regardless of agent autonomy. The autonomy principle is explicitly scoped to *writing artifacts* and bounded by existing skill guardrails (halt on TBD requirements or missing cycle, don't fabricate components, ask when architecture is unclear, don't propose unagreed mitigations).
- **Mitigation type:** preventive (scoping of the principle) plus the independent, non-bypassable PR + CI gate.
- **Defense in depth notes:** Branch protection requiring PR review (repo setting, owner: maintainer); the self-gate `sdl.yml`; the transparency requirement that each skill still reports what it wrote, so a human sees the artifacts before approving the PR.

## Threats inherited from prior cycles <!-- SR-2 -->

- **baseline:B2** — this diff edits skill `.md` files, exactly the skill-instruction-integrity risk. The mitigation still holds: changes land via PR review and the skill files are gated as code by the validator. This cycle is itself an instance of that control operating.
- **baseline:B1** not engaged — no change to `validate.py` or the reusable workflow.

## Out-of-scope threats

- Distribution integrity of the bumped plugin (repo → marketplace / `git pull`) — same posture as any skill change; covered by baseline:B2 and B5. Owner: baseline.
- 62443 mapping accuracy — a documentation-correctness concern, not an attack surface; verified in this cycle's `04-verification.md`. Owner: this cycle's verification.

## Noted for future cycles

- If the autonomy principle is ever extended from "writing artifacts" to taking code actions or merging without human review, re-threat-model — that changes the elevation-of-privilege posture materially.
- If a consumer repo adopts SDL without branch protection / required PR review, sign-off removal leaves human accountability resting on commit authorship alone; signpost to recommend required PR review in onboarding (`sync-to-repo.sh` / developer guide).
