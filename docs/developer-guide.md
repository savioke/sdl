# SDL — Developer Guide

What you need to know to work on a project that uses our SDL governance.

## What it is

A lightweight evidence trail for IEC 62443-4-1. Each branch/PR generates a folder under `docs/sdl/` with four short markdown files. The agent (Claude Code or Copilot) writes them. You review and edit.

## What you do

0. **Once per repo, initialize the baseline.** The first time a repo adopts SDL, ask the agent to run `sdl-baseline` ("initialize the SDL baseline"). It scans the codebase once and records the repo's standing security posture — exposure model, trust boundaries, standing risks — in `docs/sdl/baseline.md`, which later cycles reference instead of re-deriving. Once per repo, not per branch.
1. **Start a feature branch** as usual.
2. **Talk to the agent** about what you're building. It will invoke `sdl-spec` to scaffold `docs/sdl/YYYY-MM-DD-<branch-slug>/` and ask a few short questions (assets touched, trust boundaries, data classification, external inputs). Answer them in conversation. The agent fills the file.
3. **Build the feature.** As architecture firms up, the agent invokes `sdl-threat-model` to populate `02-threat-model.md`. Skim and correct.
4. **Before pushing the PR**, ask the agent to review (or it will offer). It runs `sdl-review` against the diff, populates `03-implementation.md` and `04-verification.md`, and flags anything it couldn't verify as residual risk.
5. **Read what it wrote.** Edit anything wrong. Sign off the checkboxes in `04-verification.md`.
6. **Commit and push.** CI validates the structure.

That's it. No forms, no Jira tickets, no separate security reviews unless something material is flagged.

## One-time setup

```
gh repo clone savioke/sdl
./sdl/scripts/install.sh
```

Installs skills globally for Claude Code and Copilot. Updates: `cd ~/.sdl-governance && git pull`.

## Per-repo setup (run once when a repo first adopts SDL)

```
~/.sdl-governance/scripts/sync-to-repo.sh /path/to/your/repo
```

Drops `.github/workflows/sdl.yml`, creates `docs/sdl/`, and writes a `docs/sdl/baseline.md` stub. All are committed. Then run `sdl-baseline` once (see step 0 above) to fill the baseline.

Note that this is the only step that has to happen *in the repo*. Cloning a repo that already opted in needs nothing — no per-clone setup, no hook installation. Just clone and start working.

## Things to know

- **One cycle per branch.** New branch = new folder. Don't reuse old ones, even for "phase 2" work — cross-reference instead. `sdl-spec` will prompt you.
- **Cycles are sized to the change.** The skills document only the delta over the baseline — the new trust boundary, the real new threats (usually zero to two), the categories the diff touches. If a tiny change produces an audit-sized cycle, the baseline is probably missing or stale — run `sdl-baseline`.
- **The agent is a first draft, not the final word.** Especially threat models. Read what it wrote and correct domain-specific gaps.
- **Residual risks are valuable.** When the agent says "I couldn't verify X," that's the audit-relevant honesty. Don't pressure it to claim coverage it didn't establish.
- **Carry-forward works.** If a previous cycle deferred something, `sdl-spec` surfaces it at the start of the next cycle so it doesn't get lost.
- **CI is the gate.** There are no local pre-commit hooks. The PR will fail if SDL artifacts are missing or stub. Catch it earlier by asking the agent to run `sdl-review` before pushing.
- **Don't delete cycle folders, ever.** Even for ripped-out features. Auditors want history.
- **If you commit without an agent**, no SDL artifacts get written. CI will catch it on the PR. Fix by asking the agent to run `sdl-spec` (if no cycle exists) and `sdl-review` (to populate the rest), then push.

## When skills don't fire automatically

Skills trigger on intent. If yours misses, just ask:

- "Initialize the SDL baseline" (once per repo)
- "Run sdl-spec for this feature"
- "Threat model this"
- "Review the diff for SDL"

## When you disagree with the agent

Edit the file. The artifact is the source of truth, not the conversation. Commit the edits with the rest of your work.

## Pointers

- Plan and architecture: `Plan.md`
- Practice mapping: `docs/62443-mapping.md`
- Skills: `skills/`
