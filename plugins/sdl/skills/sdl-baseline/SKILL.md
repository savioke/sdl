---
name: sdl-baseline
description: Adopt SDL in a repo and author its security baseline. Use when the user says "initialize SDL", "add SDL to this repo", "set up the SDL baseline", or "document the security posture of this repo", or when docs/sdl/baseline.md is missing or still a stub. Scaffolds the repo (CI workflow, docs/sdl/) if it hasn't adopted SDL yet, then scans the existing codebase once, runs a short interview, and writes the standing exposure model, trust boundaries, assets, and standing risk register so later feature cycles stay small.
---

# sdl-baseline

You author the repo's security baseline: the standing facts every future SDL cycle inherits. Run once per repo; update rarely. Per-feature cycles reference it instead of re-deriving the exposure model and re-discovering standing risks.

## Preconditions

1. The repo has a `docs/sdl/` folder, **or** the user explicitly asked to adopt/initialize SDL here. If `docs/sdl/` is missing and the user did not ask, this skill does not apply — exit silently. Never scaffold a repo into SDL without an explicit request.
2. `docs/sdl/baseline.md` is missing or still a stub. If it exists with real content, do not overwrite — tell the user it exists and offer to update specific sections instead.

## What to do

### 0. Scaffold the repo if it hasn't adopted SDL yet

If `docs/sdl/` is missing (user explicitly asked — see preconditions), run the setup script from the repo root. `<plugin-root>` is the directory two levels above this SKILL.md (in Claude Code it is also available as `$CLAUDE_PLUGIN_ROOT`):

```
bash <plugin-root>/lib/sync_to_repo.sh .
```

It writes `.github/workflows/sdl.yml` (the CI gate), `docs/sdl/.gitkeep`, and a `docs/sdl/baseline.md` stub; it refuses to overwrite existing files. Do not hand-write these — the script keeps setup deterministic. Tell the user what was added, then continue below to fill the baseline.

**Commit the scaffold and the filled baseline together.** The gate counts `sdl.yml` as code, so the adoption PR would otherwise demand a cycle that cannot exist yet. The validator recognizes an adoption diff — one that adds `sdl.yml` and `docs/sdl/baseline.md` and touches nothing else outside `docs/sdl/` — and waives the cycle requirement, but only once the baseline has real content. A pushed stub fails the gate. Do not scaffold a cycle to get around this; fill the baseline.

### 1. Scan the codebase once

This is the one place a broad read is warranted. Build a picture of:

- **Entry points.** HTTP routes, RPC handlers, queue consumers, CLI commands, cron jobs, anything that takes external input.
- **External dependencies and integrations.** Cloud APIs, databases, third-party services, secret stores.
- **Credentials and assets.** Where secrets live, what data is stored, what is sensitive.
- **The deployment/exposure model.** How it runs and who can reach it. Infer what you can; confirm with the user in step 2.
- **Pre-existing security posture.** Unauthenticated surfaces, missing input validation, known-deferred work, concurrency hazards, anything that is a standing condition rather than introduced by a change.

Be efficient: you are mapping the security shape of the repo, not reviewing every line.

### 2. Short interview

Ask only what the scan can't tell you. Keep it to a few questions. The highest-value one is almost always the exposure model — confirm it explicitly, because every later threat model hinges on it. Also confirm data classifications and which of the pre-existing issues you found are known/accepted versus genuinely news to the team.

### 3. Write `docs/sdl/baseline.md`

Fill the template sections from the scan and interview:

- **System overview**, **Deployment and exposure model**, **Trust boundaries and standing data flows**, **Assets and data classification**, **Standing security requirements** — concise; bullets, not essays.
- **Standing risk register.** This is the most important section. Every pre-existing issue that is a standing condition gets a stable ID (`B1`, `B2`, …), a severity, a disposition (`accept` / `defer` / `mitigate-later`), and a trigger to revisit. These are the risks later cycles reference by ID instead of re-discovering.

Keep it tight. The baseline is a reference, not an audit report. If a section doesn't apply to this repo, write one line saying so rather than padding.

### 4. Migrate standing risks out of existing cycles (if any)

If feature cycles already exist (the baseline is being added to a repo that already ran cycles), scan their `04-verification.md` residual-risk tables for items that are really standing conditions — pre-existing unauthenticated endpoints, platform-level deferrals, etc. Move those into the baseline risk register with `B` IDs, and note in the source cycle that the risk is now tracked in the baseline. Leave genuinely cycle-specific risks where they are.

### 5. Report

Tell the user:

- That the baseline was written, and the standing risks you recorded (the `B` IDs and one-line each).
- Which pre-existing issues were news to them versus already known (from the interview).
- That future cycles will reference these instead of re-deriving them, so cycles should now be small.

## Tone

A one-time inventory, not an audit. Keep it concise.
