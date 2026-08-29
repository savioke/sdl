# 02 — Threat Model

<!-- SR-2: Threat model. SD-1, SD-2: Secure design and defense in depth. -->

## Components and data flows

- **Skill edits** (`sdl-review`, `sdl-threat-model`, `sdl-spec`, `sdl-baseline`) — baseline:B2 executable-spec assets. They change how agents dispose of risks in every consumer repo's audit trail.
- **Template edits** (`01`, `02`, `04`, `baseline.md`) — the scaffolding every future cycle is authored into; comments here steer authoring the same way skill text does.
- **`docs/developer-guide.md`** — human-facing prose. No execution path.
- **`scripts/test_check_release.py`** — test fixture only. Runs in this repo's CI (`self-check.yml`), never in a consumer's.

No component in this cycle runs in consumer CI, handles input, or touches a credential. The flow at risk is documentary: how a risk leaves the open register.

## Threats <!-- SR-2 -->

### T1 — Closure used to drop a risk whose code is still there

- **Category:** Repudiation
- **Component / flow:** the removal-closure rule in `sdl-review` → `04-verification.md` "Risks closed by removal" → `carry_forward:` in `.sdl-meta.yml`.
- **Description:** The register now has an exit that isn't mitigation. An agent (or a developer steering one) can close an item by asserting the code is gone when it was only moved elsewhere in the repo, renamed, or disabled behind a flag. The risk disappears from `open_risks.py` output and never surfaces in another carry-forward interview, while the exposure it described is still reachable. This is the cost of the change, and it is the one worth modelling.
- **Likelihood / Impact:** low / medium
- **Mitigation:** closure is tied to the diff, not to a claim — the rule scopes it to code the reviewed diff deletes, and `sdl-review` only ever runs against an explicit merge-base..HEAD range, so the deletion is in the same diff the human reviews. Closing is not silent: it requires a past-tense line in `04-verification.md` naming what was removed *and* an added ref in `carry_forward:`, both visible in the PR diff next to the deletion they claim. Cycle documents are never amended, so the original risk statement survives in the cycle that raised it.
- **Mitigation type:** preventive (scoping) + detective (PR review of two correlated edits)
- **Defense in depth notes:** `validate.py` and `open_risks.py` are untouched, so nothing about the gate's artifact requirements or the open-list arithmetic changed — closure rides the same `carry_forward:` path a cycle already uses when it actually fixes something, and gets the same scrutiny.

### T2 — A risk that moves to another repo lands in neither register

- **Category:** Repudiation
- **Component / flow:** the "functionality that moves takes its risks with it" rule in `sdl-review` and `sdl-threat-model`.
- **Description:** This repo closes the item on the strength of the code leaving; the receiving repo has to open it in a cycle of its own. If that cycle is never run, the risk is documented nowhere current — the previous behavior at least left a (useless, uncloseable) marker here.
- **Likelihood / Impact:** medium / low
- **Mitigation:** partial and deliberate. The closing line records where the code went, so the trail points at the receiving repo rather than dead-ending; that repo's own SDL cycle owns the risk from there. This repo cannot verify another repo's register and does not try — a marker here that no one can ever close is not a control, it is the noise this cycle removes. Recorded as a residual risk in `04`.
- **Mitigation type:** detective (the handoff is named in the record)
- **Defense in depth notes:** none available from this side of the boundary. Mitigating properly means the receiving repo runs `sdl-spec`, which is that repo's adoption question, not this change's.

## Threats inherited from prior cycles <!-- SR-2 -->

- **baseline:B2** — skill `.md` files are edited, so the executable-spec surface is in play. Mitigation unchanged: the validator gates skills as code (this PR is subject to it), and the maintainer reviews the wording in the diff. This cycle adds instruction text only — no new tool, command, or file the skills touch.
- **baseline:B1** — nothing here runs in consumer CI, so the validator/workflow blast radius is not engaged. The skills do reach every consumer through the next release, which is why the wording is reviewed as code.
- **2026-07-09-faster-maybe:T2** — the fast path degrading the evidence trail. Directly related: T1 above is the same failure shape one step later in the cycle, and the same answer applies (the gate is unchanged, the artifact is in the diff the human reads). This cycle uses that fast path.

## Out-of-scope threats

- `scripts/test_check_release.py` — test-only fixture change; it disables git's background housekeeping and tolerates a teardown race, and relaxes no assertion. Owner: `2026-08-03-release-process`, which owns `check_release.py`.
- Historical cycle documents being rewritten to erase a risk — explicitly out of scope and forbidden by the rule as written; owner: PR review, which sees any edit to a prior cycle folder.
- `docs/developer-guide.md` — human prose with no execution path.

## Noted for future cycles

- If `open_risks.py` ever grows a `closed` disposition or a machine-readable closure record, revisit T1: the correlation between a deletion and its closure line could then be checked by the gate instead of by a reader.
