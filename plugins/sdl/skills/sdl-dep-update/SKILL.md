---
name: sdl-dep-update
description: Author the routine-tier SDL record for a dependency update. Use on a branch or PR whose diff only bumps dependencies (Dependabot, Renovate, scanner, or human version bumps) in a project with a docs/sdl/ folder. Verifies the diff qualifies for the routine tier, runs the deterministic checks, writes a dep-update.md record, and escalates to sdl-spec when a triage trigger applies.
model: sonnet
context: fork
background: true
---

# sdl-dep-update

You produce the routine-tier evidence for a dependency update, per
`docs/dependency-updates.md` in the governance repo. Small task, done honestly:
the record you write is an audit artifact, and every box you check is a claim
you personally verified this session.

## Preconditions

1. The repo has a `docs/sdl/` folder. If not, exit silently.
2. The diff against the merge base is dependency-shaped: only
   manifests/lockfiles and/or SHA-pinned workflow `uses:` line bumps. If any
   other file changed, this skill does not apply — run `sdl-spec` for a full
   cycle instead.

## What to do

### 1. Triage

Run the classifier instead of working through the triage table by hand
(`<plugin-root>` is the directory two levels above this SKILL.md):

```
python3 <plugin-root>/lib/dep_facts.py --base origin/main
```

Exit 0 means the routine tier applies. Exit 2 means escalate, and the trigger it
names is your answer: stop and report it, naming `sdl-spec` as the operator's
next step — do not run it yourself. `sdl-spec` is an interview and belongs in
the main conversation, not here. Do not write a routine record for an
escalation-tier change; the validator will reject majors anyway.

Two triggers the classifier cannot see are yours, and it prints both as a
reminder: **manifest changes beyond version fields** (scripts, hooks, build
config) and **an advisory affecting the new version**. Read the manifest diff
and do the advisory lookup. A trigger only you can see is still a trigger.

### 2. Run the deterministic checks

- Workflow pins: run `python3 <plugin-root>/lib/check_pins.py` (add `--exempt`
  for org-owned reusable workflows accepted as moving tags in the baseline).
- Language ecosystems: confirm CI uses integrity mode (`npm ci`,
  `--require-hashes`, `--locked` …) or note its absence in the record.
- Advisory lookup for each new version (OSV / GitHub Advisory DB).

### 3. Review release notes against promises

Read the changelog/release notes for each bump. You are looking for behavior
changes that touch anything `baseline.md` or a prior cycle's threat model
relies on. One sentence per bump in the record's Notes section; escalate if
you find a real conflict.

### 4. Write the record

Scaffold the cycle folder:

```
python3 <plugin-root>/lib/new_cycle.py --class dependency-update
```

It creates `docs/sdl/YYYY-MM-DD-<slug>/` with `.sdl-meta.yml` (including
`class: dependency-update`) and a template `dep-update.md`. Fill its updates
table from the diff rather than by hand:

```
python3 <plugin-root>/lib/dep_facts.py --base origin/main --write docs/sdl/<slug>
```

That writes one row per action pin bump, with versions read out of the diff by
the same parse the gate uses to check them — never transcribe a version
yourself. It leaves the Checks boxes and Notes untouched on purpose: those are
your attestation, and no tool checks a box on your behalf. If the diff changed
language-ecosystem manifests it names them and leaves their rows to you; add one
row per package from the lockfile diff.

Then check the boxes you actually earned and write the Notes.

Regenerate the index (`python3 <plugin-root>/lib/gen_index.py`) and run the
validator (`python3 <plugin-root>/lib/validate.py --base origin/main`).

### 5. Report

You run detached from the conversation, so your final message *is* the report —
nobody watched you work. State: the cycle folder you created, each bump with
exact old/new versions, which checks you ran and what they returned, the
validator's verdict, and any trigger that stopped you short of writing a record.
Name anything you could not verify rather than omitting it.

## Tone

This should take minutes, not hours — that is the point of the tier. But never
check a box for a check you didn't run; an attested-but-false record is worse
than no record.
