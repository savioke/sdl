---
name: sdl-spec
description: Scaffold a new SDL cycle and capture security-relevant requirements at the start of a feature. Use when the user is planning a new feature, branch, or substantial change on a project that has a docs/sdl/ folder, or when they say "let's plan X", "spec out Y", "I want to add Z", or have just created a new feature branch. Creates docs/sdl/YYYY-MM-DD-<branch-slug>/ from templates, runs a brief requirements interview, and surfaces unresolved residual risks from prior cycles.
---

# sdl-spec

You scaffold the SDL cycle for a new feature and run a short, focused requirements interview. The goal is to capture security-relevant context the team will need later — not to write a full spec.

## Preconditions

1. The repo has a `docs/sdl/` folder. If not, this skill does not apply — exit silently.
2. The user is at the start of meaningful work, not mid-implementation. If a cycle for the current branch already exists (`docs/sdl/*/.sdl-meta.yml` with matching `branch:`), do not re-scaffold — tell the user the existing cycle and offer to update `01-requirements.md` instead.
3. If `docs/sdl/baseline.md` is missing or still a stub, mention once that running `sdl-baseline` first will keep this and every later cycle small (it records the repo's standing exposure model and risks so cycles document only their delta). Offer it, but don't block — proceed with the cycle if the user wants to.

## Inputs

- Current git branch name.
- Today's date.
- Templates directory: `~/.sdl-governance/templates/docs-sdl/` (or the cloned location).
- `docs/sdl/baseline.md` if present — the repo's standing exposure model, trust boundaries, assets, and standing risks. Pull these from the baseline rather than re-asking the user.
- Prior cycle folders under `docs/sdl/` for cross-referencing and carry-forward detection.
- Whatever the user has told you about the feature in conversation.

## What to do

### 1. Generate the slug and create the folder

- **Branch slug normalization.** Take the branch name, strip everything before the last `/`, lowercase, replace underscores with hyphens, drop any non-`[a-z0-9-]` characters, truncate to 40 chars (cut on a hyphen boundary if possible).
- **Folder name.** `docs/sdl/YYYY-MM-DD-<slug>/` using today's date.
- **Refuse to overwrite.** If the folder exists, stop and tell the user.

Copy all five template files from `templates/docs-sdl/` into the new folder. Do not modify them yet beyond `.sdl-meta.yml`.

### 2. Populate `.sdl-meta.yml`

```yaml
slug: <YYYY-MM-DD-slug>
branch: <original branch name, pre-normalization>
created: <YYYY-MM-DD>
pr: null
status: in-progress
related_cycles: []
carry_forward: []
```

`related_cycles` and `carry_forward` get filled in step 4.

### 3. Run the requirements interview

Ask only what you cannot infer. Be concise — one short message with the questions, not a long preamble. If the user has already told you most of it in the conversation, fill what you know and ask only for the gaps.

If `baseline.md` exists, the standing exposure model, trust boundaries, assets, and data classifications are already recorded there. Do not re-ask them. Capture only what is **new or different for this change**: the boundary this feature introduces, the assets it newly touches, the requirements specific to it. Reference the baseline for the rest (e.g. "exposure model per baseline"). This is the main lever that keeps cycles small.

Required topics, in this order:

1. **What is being built and why?** One paragraph.
2. **What's in scope, what's out?** Especially anything related work that will be a separate cycle.
3. **Assets touched.** Data, systems, credentials, trust boundaries.
4. **Data classification.** PII, customer data, credentials, internal-only, public.
5. **Trust boundaries crossed.** Where untrusted input enters or privileged operations execute.
6. **External inputs introduced.** New endpoints, queue consumers, file ingest, IPC, env vars from runtime.
7. **Security requirements.** Authn, authz, encryption, logging, rate limiting, input validation.

Don't drown the user. If you can answer five of seven from context, ask the remaining two.

### 4. Detect related prior cycles and carry-forward residual risks

Scan `docs/sdl/*/01-requirements.md` and `docs/sdl/*/.sdl-meta.yml` for keyword overlap with this cycle's summary. For matches, list them in `related_cycles` (slug only) and reference them in `01-requirements.md` "Related prior cycles".

Then scan `docs/sdl/*/04-verification.md` files of related cycles for residual risks with `Disposition: defer` or `mitigate-later`. For each, ask the user: "Cycle <slug> deferred '<R-id>: <description>' — does this cycle address it?" Record the answers:

- **Yes, addressing it.** Add to `carry_forward:` in `.sdl-meta.yml` and reference in `01-requirements.md` "Carried-forward residual risks".
- **No, still deferred.** Note that the item remains open in the source cycle; do not add to this cycle's `carry_forward`.
- **No longer relevant.** Note the disposition change in this cycle's `01-requirements.md` so the auditor trail is intact.

Don't invent connections. If there are no obvious related cycles, leave the section empty.

### 5. Write `01-requirements.md`

Fill the template sections from the interview answers. Keep each section tight — auditors want completeness, not volume.

Leave `02-threat-model.md`, `03-implementation.md`, and `04-verification.md` as templates. They get filled by `sdl-threat-model` and `sdl-review` later.

### 6. Report

Tell the user:

- The cycle folder you created.
- Which related cycles you found (or "none").
- Which carry-forward items, if any, this cycle is taking on.
- That `02-threat-model.md` should be filled by `sdl-threat-model` once architecture firms up, and `03`/`04` by `sdl-review` before the PR.

## Tone

You are scaffolding, not gating. Don't make the user feel like they need permission to start work. The interview should feel like a colleague asking a few good questions, not a form to fill out.

If the user pushes back on a question ("we don't know yet"), accept it, write `TBD` in the relevant field, and move on. `sdl-review` will catch missing fields before the PR.
