---
name: sdl-baseline
description: Author the repo-level SDL security baseline once, when a repo adopts SDL. Use right after sync-to-repo.sh has run, when docs/sdl/baseline.md is missing or still a stub, or when the user says "initialize SDL", "set up the SDL baseline", or "document the security posture of this repo". Scans the existing codebase once, runs a short interview, and writes the standing exposure model, trust boundaries, assets, and standing risk register so later feature cycles stay small.
---

# sdl-baseline

You author the repo's security baseline: the standing facts every future SDL cycle inherits. This runs **once** per repo (and is updated rarely). Its purpose is to pay the "establish the whole security posture" cost a single time, here, so that per-feature cycles document only their delta instead of re-deriving the exposure model and re-discovering pre-existing risks every time.

## Preconditions

1. The repo has a `docs/sdl/` folder. If not, this skill does not apply — exit silently.
2. `docs/sdl/baseline.md` is missing or still a stub. If it exists with real content, do not overwrite — tell the user it exists and offer to update specific sections instead.

## Why this exists

Without a baseline, the first feature cycle in a repo absorbs the entire pre-existing security posture (every unauthenticated endpoint, every standing deferral), and later cycles re-explain the deployment model and re-list the same standing risks. The baseline is the home for all of that, written once. A 30-line change should then produce a 30-line-change-sized cycle, not a whole-codebase audit.

## What to do

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

This is a one-time setup that makes everything after it lighter. Frame it that way. Don't make it feel like a heavyweight audit — it's the inventory that lets the heavyweight audit never need to happen again.
