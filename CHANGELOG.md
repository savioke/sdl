# Changelog

What changed in each release of `savioke/sdl`, newest first.

Consumer repos pin the moving major alias (`@v2`), so a release reaches their CI
without them changing anything — this file is how they find out what moved. Every
entry notes whether it can turn a previously-passing PR red. See
`docs/releasing.md` for the compatibility contract and the release procedure.

Entries below 2.0.0 describe the `v1` line and refer to `@v1` as it was current
at the time. They are left as written: a changelog is a record of what shipped,
not a description of the present. `v1` is end-of-life — see 2.0.0.

Versions are shared by the Claude and Codex plugin manifests under
`plugins/sdl/`; each is tagged `vX.Y.Z` and, for the current major, aliased by
`vX`.

## 2.1.0 — 2026-08-22

**Not breaking.** Add first-class Codex distribution for the existing SDL
skills. The plugin now includes a Codex manifest, the Relay marketplace exposes
a Codex catalog, and the installer registers and installs `sdl@relay` when the
Codex CLI is available. Claude Code and Codex use the same skills, helper
scripts, templates, version, and immutable release tag.

Release checks and `release.sh` now keep both plugin manifests and both
marketplace catalogs in lockstep, including validating the source kind,
repository URL, plugin subdirectory, and tag. The Claude-specific
background/subagent hints on `sdl-dep-update` remain in place; hosts that do not
implement them run the same skill inline.

## 2.0.0 — 2026-08-06

**Breaking.** A direct push of code to the default branch now fails the gate
unless the push carries an SDL cycle. Nothing else changes what passes: pull
requests are validated exactly as before.

**`v1` is end-of-life.** The `v1` alias is left where it is so nothing breaks
mid-flight, but it is not maintained: it contains a `push` run that validates
nothing, which is the defect this release exists to fix. Move every repo to
`@v2`. New adoptions get `@v2` automatically.

### The gate now sees direct pushes

Before this, the `push` run was a no-op in every repo. It diffed `origin/main`
against `HEAD` — the same commit, on a push to main — so it found nothing and
reported "no substantive code changes; cycle presence not required." Green, on
every push, forever. Code that reached `main` without a PR was never validated
by anything.

- **Pushes that came from a PR are skipped, not re-judged.** The gate asks
  GitHub whether the commit came from a merged pull request. It did — skip, the
  `pull_request` run already validated it under the full rules (adoption PRs,
  dependency-update class, and all). Re-deriving that decision on the push path
  would mean reimplementing those rules and getting the edge cases wrong.
  Commit *parent count* is not used for this: squash and rebase merges land as
  single-parent commits and would have been misread as direct pushes.
- **Direct pushes are validated against the previous commit**
  (`github.event.before`) rather than against a ref that has already moved.
- **A direct push must carry its own cycle.** It is matched by the cycle folder
  appearing in the push, not by `branch:` — a cycle declaring `branch: main`
  would otherwise vouch for every future push to `main` once one existed.
- **Every uncertain case validates rather than skips.** If the PR lookup fails,
  the gate validates and says why it could not tell.
- **Branch creation and force-pushes are skipped explicitly**, with the reason
  stated: there is no reachable previous commit to diff against.

### Honest reporting

- An empty diff now says what it is — `origin/main and HEAD are the same commit
  — nothing to compare` — instead of "no substantive code changes", which read
  as a verdict on the work when there had been no work to judge.

### Tools

- **`new_cycle.py --slug NAME`** names a cycle explicitly and lifts the
  one-cycle-per-branch guard. Without it, successive direct pushes to `main`
  were impossible to scaffold: the first produced `<date>-main` and every later
  one was refused as "branch 'main' already has a cycle". The guard still
  applies to feature branches, where a second scaffold is an accident rather
  than an intent.

### Hardening

- `sdl-validate.yml` passes inputs through the environment instead of
  interpolating `${{ }}` directly into `run:` blocks. Any repo may call this
  workflow (`baseline:B4`), and an interpolated input is a script-injection
  path — into the caller's own runner, but worth closing regardless.
- The workflow declares `permissions: contents: read, pull-requests: read`.

### Upgrading

Point your `sdl.yml` at `@v2` — one line, and the only required step:

```yaml
uses: savioke/sdl/.github/workflows/sdl-validate.yml@v2
```

Then, before you push code straight to `main`, scaffold a cycle for it with
`new_cycle.py --slug <name>` and push both together. Docs and config are
unaffected — the requirement applies to source files, `.github/workflows/`, and
skill definitions.

If your `sdl.yml` also passes `sdl_ref`, move it to `v2` as well; leaving it at
`v1` pairs the v2 workflow with a v1 validator that does not understand
`--push`. Repos that pass nothing get the right default.

Repos whose default branch is not named `main` should change `branches: [main]`
in their own `sdl.yml`; otherwise the push run never fires and the gap this
release closes stays open there.

## 1.3.0 — 2026-08-06

**Not breaking.** The gate is untouched — no PR that passed before fails now.
The three new tools are things an agent already did by hand; none of them can
reject a change, and skipping them changes nothing about whether a PR passes.

### Tools

Three pieces of cycle work that never needed a model. Each takes a step that was
prose an agent reasoned through and makes it a command that answers instantly —
and, where it touches an audit record, removes a place a wrong value could be
typed in.

- **`lib/dep_facts.py` — dependency triage and record rows, from the diff.**
  Answers the two questions `sdl-dep-update` used to work through by hand: does
  this diff qualify for the routine tier (exit 0), or which escalation trigger
  fired (exit 2, named on stdout)? With `--write` it also fills the record's
  Updates table. Versions are read out of the diff by the same parse the gate
  uses to check them, so a version in a record is no longer transcribed by an
  agent. Deliberately partial and explicit about it: GitHub Actions pin rows are
  generated in full, language-ecosystem manifests are named and left to the
  author, and the two triggers no classifier can see — manifest changes beyond
  version fields, and advisory results — stay attestation and are printed as a
  reminder. It never checks a Checks box or writes a Note.
- **`lib/open_risks.py` — what earlier cycles left open.** Reads every cycle's
  residual-risk table, keeps the `defer` and `mitigate-later` rows, and drops any
  a later cycle already claimed in its `carry_forward:`. `sdl-spec` used to
  re-derive this by reading every `04-verification.md` at the start of each
  cycle — work that grew with the repo and produced the same answer every time.
  `--all` shows accepted and already-claimed items too.
- **`lib/cycle_stamp.py` — the mechanical review fields.** Stamps Reviewer, Date,
  and Diff range into `04-verification.md`, and prints the last commit touching
  each changed file for the `03` mitigation table. Writes nothing else; the
  findings are the review. `--agent` names a non-Claude agent.

### Skills

- `sdl-dep-update` triage is now the classifier's exit code rather than a table
  read by hand, and its Updates table is generated. The attestation steps are
  unchanged — you still check only the boxes you earned.
- `sdl-spec` calls `open_risks.py` for carry-forward detection.
- `sdl-review` calls `cycle_stamp.py` for the fields git already knows.
- Fixed: `sdl-dep-update` referred to the plugin root as both `<governance>` and
  `<plugin-root>` in the same file. That skill now says `<plugin-root>`
  throughout. (`new_cycle.py` and `gen_index.py` still say `<governance>` in
  their usage docstrings — cosmetic, and left for a cycle that touches them.)

### CI (this repo only — consumers unaffected)

- `self-check.yml` discovers `lib/test_*.py` instead of running a hand-listed
  set, so a new test file cannot be silently skipped, and smoke-runs `--help` for
  every tool rather than just the validator.

### Upgrading

Nothing to do. The new tools ship with the plugin and the skills call them; if
you invoke the skills as usual you get the faster path automatically. Running
them by hand is supported — each takes `--help`.

## 1.2.0 — 2026-08-06

**Never tagged.** 1.3.0 was released before this version was, and `release.sh`
reads whatever `plugin.json` says at release time, so no `v1.2.0` tag exists.
Everything below shipped inside `v1.3.0`. Kept as a record of what changed and
when; do not go looking for the tag.

**Not breaking.** The gate is untouched — no PR that passed before fails now.

### Skills

- **`sdl-dep-update` runs detached, on a smaller model.** New frontmatter
  (`context: fork`, `background: true`, `model: sonnet`) hands the routine-tier
  record to its own subagent instead of expanding it into your conversation. You
  get a task notification when it lands, and the primary model's context is never
  spent on a lockfile bump — which was most of what made the cheapest tier of
  work feel expensive.

  The fork starts from a fresh context. That suits this skill: every box it
  checks has to be re-derived from the diff and the tooling rather than inherited
  from whatever the main conversation happened to remember, which is what the
  record already claims when it says the checks were verified this session.

  Two instructions changed to match. The skill now closes with an explicit report
  step, because nobody watched it work; and an escalation trigger stops and names
  `sdl-spec` rather than trying to run an interview from a detached agent.

- Skill runners ignore frontmatter keys they don't recognize, so this is inert
  outside Claude Code — verified against Codex and Antigravity, which both load
  the same `SKILL.md` and will keep running it inline on whatever model is
  driving. Their own subagent and model-selection mechanisms live outside
  `SKILL.md` (Codex uses TOML agent profiles), so there is no portable spelling
  of this to reach for.

### Upgrading

- **Consumer repos:** nothing to do; the gate did not change.
- **Claude Code:** `/plugin marketplace update relay`, then reload. Dependency
  update records now arrive as a background task notification instead of inline
  output. Read the record before you push, same as always.

## 1.1.0 — 2026-08-04

**Not breaking.** Only widens what passes: an adoption PR that failed the gate
now succeeds. Nothing that passed before fails now.

### Gate (reaches consumer CI via `@v1`)

- **A repo's SDL adoption PR no longer needs a cycle.** It installs
  `.github/workflows/sdl.yml`, which the gate counts as code — so it demanded a
  cycle that by definition cannot exist yet, and the fix was a decoy cycle
  documenting the act of enrolling. The validator now recognizes the adoption
  diff and takes `docs/sdl/baseline.md` as its artifact.

  The exemption is narrow on purpose. It applies only to a diff that **adds**
  both `sdl.yml` and `baseline.md` and touches nothing else outside `docs/sdl/`;
  the workflow must be the generated caller (every `uses:` resolves to
  `savioke/sdl/.github/workflows/sdl-validate.yml`, no inline `run:`); and the
  baseline must have real content, not the stub. Because it fires only while
  `baseline.md` is being added, a repo can reach it once and never again.
- Two clearer failures in the same area: an adoption PR carrying a stub baseline
  now says so and names the `sdl-baseline` skill, and the missing-cycle message
  no longer reads as if the gate were demanding a particular branch name.

### Skills and scaffolding

- `sdl-baseline` and `sync-to-repo.sh` now direct you to fill the baseline
  *before* the adoption commit, so the scaffold and the filled baseline land in
  one PR. Splitting them across two PRs fails the gate on the first.

### Upgrading

- **Consumer repos:** nothing to do; `@v1` picks this up. A repo mid-adoption
  with a red gate can drop its decoy cycle, or keep it — a real cycle still
  satisfies the gate and takes precedence over the exemption.
- **Claude Code:** `/plugin marketplace update relay`, then reload.

## 1.0.1 — 2026-08-04

**Not breaking.** Removes gate runs that never validated anything; no PR outcome changes.

### Gate (reaches consumer CI via `@v1`)

- The generated `sdl.yml` now filters its `push` trigger to `main`. It was
  `on: [pull_request, push]`, which also fires on **tag** pushes — where the
  validator has nothing to say, because it diffs against `origin/main`. A release
  tag produced an empty diff and a vacuous pass; a tag cut anywhere else would
  demand an SDL cycle for a push that changed no code.

### Upgrading

- **Consumer repos:** `sdl.yml` was written into your repo at onboarding and is
  yours, so this release does not change it. Apply the same two-line edit to stop
  the spurious runs — or re-run `sync-to-repo.sh` after deleting the file:

  ```yaml
  on:
    pull_request:
    push:
      branches: [main]
  ```

- **Claude Code:** `/plugin marketplace update relay`, then reload.

## 1.0.0 — 2026-08-04

First release under the versioning contract in `docs/releasing.md`, and the
first to reach consumers since the `v1` tag was cut. Promoted to 1.0.0 so the
plugin's version and the tag consumers already pin (`@v1`) denote the same
major; 0.6.0 and 0.7.0 were never delivered as releases and are folded in here.

**Not breaking.** Nothing that passed the gate before fails now: the validator
changes below only widen what is accepted, and the one new check emits `[warn]`.

### Gate (reaches consumer CI via `@v1`)

- Dependency-update cycles: a `.sdl-meta.yml` declaring `class: dependency-update`
  is validated against a `dep-update.md` record instead of the four-document
  cycle, provided the whole diff is manifests, lockfiles, and pin-only workflow
  changes. Previously these needed a full cycle.
- Workflow pin changes are accepted only when every changed `uses:` line is
  SHA-pinned with a parseable version comment, the action is unchanged, and the
  major matches — a new, removed, or major-bumped action still requires a full
  cycle.
- New `[warn]` (not a failure): a diff that touches dependency manifests with no
  dependency-update cycle. Slated to become a hard check in a future major.
- Skill and template `.md` files are gated as code, so changes to agent-executable
  instructions require a cycle.
- `sdl-validate.yml` runs on newer pinned actions: `actions/setup-python` v6.3.0
  → v7.0.0 and `actions/checkout` v7.0.0 → v7.0.1. Both still declare
  `runs.using: node24`, so no runner requirement changed; the only breaking
  change in setup-python v7 is removal of the `pip-install` input, which this
  workflow never set and callers cannot reach.

### Plugin (reaches Claude Code via the marketplace)

- The plugin is self-contained: `skills/`, `lib/`, and `templates/` live under
  `plugins/sdl/`, and skills resolve their tooling relative to their own
  `SKILL.md` instead of assuming a `~/.sdl-governance` clone.
- Repo onboarding no longer needs a clone: `plugins/sdl/lib/sync_to_repo.sh`
  ships inside the plugin, and the `sdl-baseline` skill scaffolds an un-adopted
  repo on request before writing the baseline.
- New `sdl-dep-update` skill for routine dependency-update cycles.
- `sdl-review` gained a "Proportionality" section: the SDL artifacts record only
  what changes what an attacker can do, what a control detects, or what risk the
  reader is accepting — findings are one to three sentences, a re-review after PR
  comments does not get an entry per comment, and a concern investigated and found
  not to be a defect is not recorded at all. The `04-verification.md` template
  gained a matching, explicitly optional "Defects found" section. Non-security
  detail in these files buries the security signal.
- Marketplace renamed `relay-sdl` → `relay`; the plugin installs as `sdl@relay`
  from `savioke/relay-plugin-marketplace`.

### Release and supply chain

- `scripts/release.sh` performs the whole release; `scripts/check_release.py`
  fails CI when the repo, its tags, and the marketplace manifest disagree.
- The marketplace manifest now pins `source.ref` to the exact release tag rather
  than `main`, so a declared version identifies exactly one tree.
- Release tags are annotated and signed when a signing key is configured.
- `check_pins.py` verifies every SHA-pinned action against the tag in its
  comment, catching retag-after-pin drift; `self-check` runs daily so drift is
  found without waiting for a push.

### Upgrading

- **Consumer repos:** nothing to do. The next CI run picks this up from `@v1`.
- **Claude Code:** `/plugin marketplace update relay`, then reload. Required —
  the plugin cache is keyed by version, so an install stays on its old copy
  until the version changes.
- **Copilot / clone-based installs:** `cd ~/.sdl-governance && git pull &&
  scripts/install.sh`. Re-running `install.sh` is **required this time**: skills
  moved to `plugins/sdl/skills/`, and a symlink created before that move points
  at a path that no longer exists, which silently leaves the agent with no
  skills. A plain `git pull` is enough for later releases.

## Earlier history

Releases before 1.0.0 were tagged only as the moving `v1` alias and are not
itemized here. See `git log v1` and the cycle records under `docs/sdl/`.
