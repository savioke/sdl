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
5. **Read what it wrote.** Edit anything wrong.
6. **Commit and push.** CI validates the structure.

That's it. No forms, no Jira tickets, no separate security reviews unless something material is flagged.

## One-time setup

**Claude Code** (the common case). In any Claude Code session:

```
/plugin marketplace add savioke/relay-plugin-marketplace
/plugin install sdl@relay
```

That's the whole install — skills, templates, and tooling arrive as one plugin. To update: `/plugin marketplace update relay` and reload when prompted.

**Copilot or other agents.** These have no marketplace path, so they read the skills from a local clone:

```
gh repo clone savioke/sdl ~/.sdl-governance
~/.sdl-governance/scripts/install.sh
```

The script symlinks skills into Copilot and also sets up Claude Code as above. To update: `cd ~/.sdl-governance && git pull` (Copilot sees it immediately; Claude Code still updates via `/plugin marketplace update relay`).

If your clone predates 1.0.0, re-run `scripts/install.sh` once after that pull. Skills moved to `plugins/sdl/skills/`, so a symlink created earlier points at a path that no longer exists — Copilot loads no skills and says nothing about it. `ls -la ~/.copilot/skills/sdl` shows whether yours needs it.

## Per-repo setup (run once when a repo first adopts SDL)

This step needs the clone (see "Copilot or other agents" above), even if you otherwise use only Claude Code:

```
~/.sdl-governance/scripts/sync-to-repo.sh /path/to/your/repo
```

Drops `.github/workflows/sdl.yml`, creates `docs/sdl/`, and writes a `docs/sdl/baseline.md` stub. Then run `sdl-baseline` once (see step 0 above) to fill the baseline, and commit the scaffold and the filled baseline together.

That adoption PR needs no cycle: the gate counts `sdl.yml` as code, but it recognizes a diff that adds the workflow and the baseline and touches nothing else outside `docs/sdl/`, and takes the baseline as the artifact. It waives the cycle only for a baseline with real content — push the stub alone and the gate fails asking you to fill it. Bundle any other change into a later PR; mixing code into the adoption PR puts you back on the ordinary path of needing a cycle.

Note that this is the only step that has to happen *in the repo*. Cloning a repo that already opted in needs nothing — no per-clone setup, no hook installation. Just clone and start working.

## Things to know

- **One cycle per branch.** New branch = new folder. Don't reuse old ones, even for "phase 2" work — cross-reference instead. `sdl-spec` will prompt you.
- **Cycles are sized to the change.** The skills document only the delta over the baseline — the new trust boundary, the real new threats (usually zero to two), the categories the diff touches. If a tiny change produces an audit-sized cycle, the baseline is probably missing or stale — run `sdl-baseline`.
- **The agent is a first draft, not the final word.** Especially threat models. Read what it wrote and correct domain-specific gaps.
- **Residual risks are valuable.** When the agent says "I couldn't verify X," that's the audit-relevant honesty. Don't pressure it to claim coverage it didn't establish.
- **Carry-forward works.** If a previous cycle deferred something, `sdl-spec` surfaces it at the start of the next cycle so it doesn't get lost.
- **Dependency bumps get a lighter path.** Minor/patch bumps (Dependabot or otherwise) don't need a full cycle: the agent runs `sdl-dep-update`, which writes a one-file `dep-update.md` record the validator checks. Major bumps and new dependencies escalate to a normal cycle. Policy: [dependency-updates.md](dependency-updates.md); recipe: [Adding SDL docs to a Dependabot PR](#adding-sdl-docs-to-a-dependabot-pr).
- **CI is the gate.** There are no local pre-commit hooks. The PR will fail if SDL artifacts are missing or stub. Catch it earlier by asking the agent to run `sdl-review` before pushing.
- **Don't delete cycle folders, ever.** Even for ripped-out features. Auditors want history.
- **If you commit without an agent**, no SDL artifacts get written. CI will catch it on the PR. Fix by asking the agent to run `sdl-spec` (if no cycle exists) and `sdl-review` (to populate the rest), then push.

## Adding SDL docs to a Dependabot PR

Dependabot doesn't know about SDL, so its PRs arrive without artifacts and fail the gate (workflow pin bumps count as code). To fix one:

```
gh pr checkout <number>    # branch looks like dependabot/github_actions/actions-3e1200532a
claude
```

Ask for an SDL dependency-update cycle ("write the SDL dependency update record for this branch"). The agent runs `sdl-dep-update`: confirms the diff qualifies for the routine tier, verifies pins against upstream tags, checks advisories and release notes, and writes `docs/sdl/<date>-<slug>/` with the `dep-update.md` record.

Then **read the record before you push.** The checked boxes are your attestation that the dependency changes were actually looked at — this step exists to make you affirm that, not to launder a bot PR past the gate. Commit and push to the PR branch; validation passes and the PR is mergeable.

If the bump is a major version, the agent will say so and escalate to a full cycle (`sdl-spec`) instead — that's intended, not a malfunction.

## Browsing the SDL docs in a browser

To read a repo's cycles as rendered HTML instead of raw markdown:

```
python3 ~/.sdl-governance/scripts/sdl-serve.py [repo-path]   # defaults to cwd
```

Open http://127.0.0.1:8000/. The sidebar lists the baseline, the index, and every cycle (with status); clicking a file renders it. The viewer lives in the governance install — nothing is added to your repo — and it reads `docs/sdl/` live, so it always reflects the current files. It binds localhost only and serves only files under `docs/sdl/`. Stop it with Ctrl-C.

## When skills don't fire automatically

Skills trigger on intent. If yours misses, just ask:

- "Initialize the SDL baseline" (once per repo)
- "Run sdl-spec for this feature"
- "Threat model this"
- "Review the diff for SDL"
- "Write the SDL dependency update record" (Dependabot / version-bump branches)

## When you disagree with the agent

Edit the file. The artifact is the source of truth, not the conversation. Commit the edits with the rest of your work.

## Pointers

- Plan and architecture: `Plan.md`
- Practice mapping: `docs/62443-mapping.md`
- Skills: `plugins/sdl/skills/`
