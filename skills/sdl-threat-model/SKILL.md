---
name: sdl-threat-model
description: Produce a STRIDE-lite threat model for the current SDL cycle. Use when architecture or design decisions are being discussed mid-feature on a project that has a docs/sdl/ folder, after sdl-spec has run, or when the user says "threat model this", "what could go wrong", or is finalizing the design. Reads 01-requirements.md, walks STRIDE per component and data flow, references threats from related prior cycles, and writes 02-threat-model.md.
---

# sdl-threat-model

You produce the threat model for an in-flight SDL cycle. Output is `02-threat-model.md`. Goal: identify what could go wrong with what's actually being built, propose mitigations, link to prior-cycle threats so we don't relitigate.

## Proportionality

Most diffs introduce **zero to two** new threats. A concern earns a full stanza only if it is **presently reachable in the code as written by this diff**. Everything else is a one-line note:

- **Not reachable today** (the current inputs make it impossible) → "Noted for future cycles".
- **Not this code** (IAM scope, a permission someone already holds, a platform default) → "Out-of-scope threats", with the owner.
- **Covered by the baseline or a prior cycle** → reference by ID; don't restate.
- **Forward-looking habit risk** → "Noted for future cycles".

The Description / Likelihood / Impact / Mitigation / Mitigation-type / Defense-in-depth structure is for live threats only.

Read `docs/sdl/baseline.md` first (if present) and reference its standing exposure model and risks rather than re-deriving them.

## Preconditions

1. The repo has a `docs/sdl/` folder. If not, this skill does not apply — exit silently.
2. A cycle exists for the current branch and `01-requirements.md` is populated. If `01-requirements.md` is still mostly TBD, tell the user `sdl-spec` should run (or fill more of) requirements first, and stop.

## Inputs

- The cycle folder for the current branch (find via `docs/sdl/*/.sdl-meta.yml` matching the branch).
- `docs/sdl/baseline.md` if present — the repo's standing exposure model, trust boundaries, and standing risk register (B1, B2, …). Inherit from it; don't re-derive.
- `01-requirements.md` — the source of truth for what's in scope, what assets are touched, trust boundaries, external inputs.
- `02-threat-model.md` from each cycle listed in `.sdl-meta.yml` `related_cycles` — for inheritance.
- Whatever the user has shared about architecture in the conversation.

## What to do

### 1. Identify components and data flows

From `01-requirements.md` and the conversation, list the components introduced or modified and the data flows that cross trust boundaries. Don't draw a diagram; a brief bulleted inventory is enough. One bullet per component.

If the architecture is unclear, ask one or two pointed questions before continuing. Don't make up components.

### 2. Walk STRIDE per component

For each component or flow, ask:

- **S**poofing — can identity be forged here?
- **T**ampering — can data in transit or at rest be modified by an attacker?
- **R**epudiation — can an action be performed and denied, with no audit trail?
- **I**nformation disclosure — can data leak to a party not authorized to see it?
- **D**enial of service — can an attacker exhaust resources or block legitimate use?
- **E**levation of privilege — can a low-privilege user gain higher privilege?

Don't list every theoretical STRIDE concern for every component. Apply judgment. Most components only meaningfully expose two or three categories. Skip the rest.

### 3. Write threats with stable IDs

For each real concern identified, write an entry with a stable ID (`T1`, `T2`, …) so `03-implementation.md` and `04-verification.md` can reference them. Use the template structure:

```
### T1 — <short name>

- **Category:** <STRIDE letter and word>
- **Component / flow:**
- **Description:**
- **Likelihood / Impact:** <low | medium | high> / <low | medium | high>
- **Mitigation:** <design choice or control>
- **Mitigation type:** <preventive | detective | corrective>
- **Defense in depth notes:** <complementary controls if any>
```

Be honest about likelihood and impact. Marking everything "high" is just as useless as marking everything "low".

### 4. Inherit threats from related cycles

Read `02-threat-model.md` from each cycle in `related_cycles`. For each prior threat that still applies to the current code path:

- Do not renumber it; reference it by `<prior-slug>:T<N>`.
- Add a short note in the "Threats inherited from prior cycles" section explaining whether the prior mitigation still holds, or whether this cycle changes it.

If a prior threat is now obsolete (the code path it covered is gone), say so explicitly with one line.

### 5. One-line notes: out of scope and noted for future cycles

Everything you considered but did not write as a live threat goes here, **one line each**.

- **Out-of-scope threats:** concerns owned elsewhere (IAM scope, a platform default, an upstream layer covered by the baseline or a prior cycle) or explicitly deferred/accepted. One line with rationale and owner — the auditor-visible reason a known concern wasn't mitigated here.
- **Noted for future cycles:** concerns not reachable with the code as written but worth a signpost if it grows a certain way (e.g. "if user-data ever carries a non-allowlisted string, switch to a YAML marshaller").

If a note wants a Mitigation and a Likelihood/Impact, either it's a real threat (promote it to step 3) or keep it to one line.

### 6. Report

Tell the user:

- How many new threats you wrote (and the IDs).
- How many prior-cycle threats are inherited.
- Anything you flagged out of scope and why.
- That `sdl-review` will verify the mitigations actually landed in code before the PR.

## Tone

A threat model is a draft for discussion, not a final document. Surface assumptions explicitly so the user can correct them. Domain-specific threats — the ones that matter most — usually only the human knows. Make it easy to push back.

Don't pad. Five well-chosen threats are worth more than fifteen generic ones. If a category genuinely doesn't apply to a component, skip it; don't write "Spoofing: N/A" for every component.

Don't propose mitigations the team hasn't agreed to. If a mitigation is uncertain, write the threat without one and surface the gap to the user.
