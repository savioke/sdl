---
name: sdl-spec
description: Scaffold a new SDL cycle and capture security-relevant requirements at the start of a feature. Use when the user is planning a new feature, branch, or substantial change on a project that has a docs/sdl/ folder, or when they say "let's plan X", "spec out Y", "I want to add Z", or have just created a new feature branch. Creates docs/sdl/YYYY-MM-DD-<branch-slug>/ from templates, runs a brief requirements interview, and surfaces unresolved residual risks from prior cycles.
---

# sdl-spec

You scaffold the SDL cycle for a new feature and run a short, focused requirements interview. The goal is to capture security-relevant context the team will need later — not to write a full spec.

## Preconditions

1. The repo has a `docs/sdl/` folder. If not, this skill does not apply — exit silently.
2. If a cycle for the current branch already exists (`docs/sdl/*/.sdl-meta.yml` with matching `branch:`), do not re-scaffold — tell the user the existing cycle and offer to update `01-requirements.md` instead.
3. If `docs/sdl/baseline.md` is missing or a stub, suggest running `sdl-baseline` first — it records the standing exposure model and risks so cycles document only their delta. Don't block; proceed if the user prefers.

## Fast path: small, already-implemented changes

When the change is already implemented (or nearly) and small — roughly a day of work or less, no new trust boundary, no new external input — don't run the cycle as three separate passes. In one pass: scaffold (step 1), skip the interview (every required topic is answerable from the diff and the conversation), write `01-requirements.md`, then author `02-threat-model.md` per `sdl-threat-model` and run `sdl-review`, all in the same session. Show the user the finished artifacts to correct instead of interviewing them first.

This compresses orchestration, not evidence: the four artifacts meet the same standard and the validator still gates. If the diff turns out to cross a new trust boundary or introduce external input, drop back to the interview — that judgment call is the one step you cannot skip.

## Inputs

- Current git branch name.
- Today's date.
- Templates directory: `<plugin-root>/templates/docs-sdl/`, where `<plugin-root>` is the directory two levels above this SKILL.md.
- `docs/sdl/baseline.md` if present — the repo's standing exposure model, trust boundaries, assets, and standing risks. Pull these from the baseline rather than re-asking the user.
- Prior cycle folders under `docs/sdl/` for cross-referencing and carry-forward detection.
- Whatever the user has told you about the feature in conversation.

## What to do

### 1. Scaffold with the tool

Run from the repo root (`<plugin-root>` is the directory two levels above this SKILL.md):

```
python3 <plugin-root>/lib/new_cycle.py
```

It normalizes the branch name to a slug, creates `docs/sdl/YYYY-MM-DD-<slug>/` from the templates, and writes `.sdl-meta.yml`; it refuses to overwrite an existing folder or re-scaffold a branch that already has a cycle. Do not hand-copy templates or hand-write the meta file — the tool exists so this step is deterministic. `related_cycles` and `carry_forward` get filled in step 3.

**Working directly on the default branch.** If the change is going to be pushed straight to `main` rather than through a PR, pass `--slug <short-name>` describing the change:

```
python3 <plugin-root>/lib/new_cycle.py --slug fix-token-refresh
```

The branch name is not a useful slug here — every such cycle would be called `main` — and the one-cycle-per-branch guard would refuse the second one. An explicit slug gives each push its own cycle, which is what the gate expects: a direct push must carry its own evidence, since no PR review stood between the code and the branch. Scaffold, author, and push the cycle in the same push as the code.

### 2. Run the requirements interview

Ask only what you cannot infer. Be concise — one short message with the questions, not a long preamble. If the user has already told you most of it in the conversation, fill what you know and ask only for the gaps.

If `baseline.md` exists, the standing exposure model, trust boundaries, assets, and data classifications are recorded there — don't re-ask them. Capture only what is **new or different for this change**: the boundary this feature introduces, the assets it newly touches, the requirements specific to it. Reference the baseline for the rest (e.g. "exposure model per baseline").

Required topics, in this order:

1. **What is being built and why?** One paragraph.
2. **What's in scope, what's out?** Especially anything related work that will be a separate cycle.
3. **Assets touched.** Data, systems, credentials, trust boundaries.
4. **Data classification.** PII, customer data, credentials, internal-only, public.
5. **Trust boundaries crossed.** Where untrusted input enters or privileged operations execute.
6. **External inputs introduced.** New endpoints, queue consumers, file ingest, IPC, env vars from runtime.
7. **Security requirements.** Authn, authz, encryption, logging, rate limiting, input validation.

Don't drown the user. If you can answer five of seven from context, ask the remaining two.

### 3. Detect related prior cycles and carry-forward residual risks

Scan `docs/sdl/*/01-requirements.md` and `docs/sdl/*/.sdl-meta.yml` for keyword overlap with this cycle's summary. For matches, list them in `related_cycles` (slug only) and reference them in `01-requirements.md` "Related prior cycles".

Then list what earlier cycles left open — don't re-derive it by reading each `04-verification.md`:

```
python3 <plugin-root>/lib/open_risks.py
```

It reads every cycle's residual-risk table, keeps the `defer` and `mitigate-later` rows, and drops any that a later cycle already claimed in its `carry_forward:`. What it prints is the live debt, not the whole history. For each item, ask the user: "Cycle <slug> deferred '<R-id>: <description>' — does this cycle address it?" Record the answers:

- **Yes, addressing it.** Add to `carry_forward:` in `.sdl-meta.yml` and reference in `01-requirements.md` "Carried-forward residual risks".
- **No, still deferred.** Note that the item remains open in the source cycle; do not add to this cycle's `carry_forward`.
- **No longer relevant.** Note the disposition change in this cycle's `01-requirements.md` so the auditor trail is intact.

Don't invent connections. If there are no obvious related cycles, leave the section empty.

### 4. Write `01-requirements.md`

Fill the template sections from the interview answers. Keep each section tight — auditors want completeness, not volume.

Leave `02-threat-model.md`, `03-implementation.md`, and `04-verification.md` as templates. They get filled by `sdl-threat-model` and `sdl-review` later.

### 5. Report

Tell the user:

- The cycle folder you created.
- Which related cycles you found (or "none").
- Which carry-forward items, if any, this cycle is taking on.
- That you'll fill `02-threat-model.md` (via `sdl-threat-model`) once the architecture is concrete, and `03`/`04` (via `sdl-review`) before the PR — as a normal part of the work, not something the user has to request.

## Proceeding through the cycle

These artifacts are part of normal development, not a task the user must authorize. Don't close with "let me know when you'd like me to threat-model" — when the architecture is concrete enough, run `sdl-threat-model` on your own initiative, and `sdl-review` when the change is heading for commit or PR. Announce what you're about to do and show what you wrote so the user can correct it; transparency, not permission-seeking, is the goal. Stop to ask only for a genuine open question you can't resolve from the code or conversation — an architectural decision, an undocumented trust boundary, a domain risk only the human knows.

## Tone

You are scaffolding, not gating. Don't make the user feel like they need permission to start work. The interview should feel like a colleague asking a few good questions, not a form to fill out.

If the user pushes back on a question ("we don't know yet"), accept it, write `TBD` in the relevant field, and move on. `sdl-review` will catch missing fields before the PR.
