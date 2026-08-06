# Dependency updates

Fleet policy for supply-chain updates in SDL-governed repos. Practice refs:
SM-9/SM-10 (third-party component management), DM-1 (defect management).

Updates are classified by **what the diff changes, not who authored it**. A
Dependabot PR, a scanner-generated PR, and a human commit acting on an advisory
all get the same treatment; author identity is spoofable, diff shape is not.

## Tiers

### Routine tier

For minor/patch bumps of dependencies the repo already uses. Evidence is one
`dep-update.md` record in a cycle folder with `class: dependency-update` in its
`.sdl-meta.yml` — not the four full-cycle artifacts. The validator enforces:

- The diff touches only dependency manifests/lockfiles (exact-filename
  allowlist) and/or workflow `uses:` lines that stay SHA-pinned, keep the same
  `owner/repo`, and stay within the same major version.
- `dep-update.md` exists, has content, and declares only non-major bumps.

Anything the classifier cannot positively identify as dependency-shaped
disqualifies the routine tier. That is intentional: the classifier fails
closed, and "full cycle required" is the safe wrong answer.

### Escalation tier

A full SDL cycle (`sdl-spec` → threat model → review), triggered by any of:

| Trigger | Why |
|---------|-----|
| Major version bump | Behavior changes; review against documented promises |
| New dependency, or action `owner/repo` change | New trust relationship |
| Unpinned or comment-less action ref | Reopens baseline:B6-class exposure |
| Manifest changes beyond version fields (scripts, hooks, build config) | Executable config, not a version bump |
| Hand-authored lockfile edit from outside trusted automation | Lockfiles direct what CI downloads and runs |
| Advisory lookup shows the *new* version is affected | The bump itself is the risk |

The classifier mechanically detects these for GitHub Actions (pin shape,
`owner/repo` identity, major version from the pin comment — including action
*removals*, which are CI behavior changes). For language ecosystems it checks
only the record's declared versions for majors; manifest changes beyond
version fields (scripts, hooks), hand-authored lockfile edits, and advisory
results are the author's attestation, backed by human merge review. The
validator does not parse lockfile contents.

`plugins/sdl/lib/dep_facts.py` runs that same classifier ahead of the gate, so
the author gets the tier decision and the named trigger as an exit code
(0 routine, 2 escalate) instead of working the table by hand. With `--write` it
also fills the record's Updates table from the diff. It never touches the Checks
boxes or Notes: the triggers it cannot see — manifest changes beyond version
fields, and advisory results — stay the author's attestation, and it prints both
as a reminder rather than implying coverage it does not have.

## Checks

Deterministic, re-run in CI rather than trusted from the record where possible:

- `plugins/sdl/lib/check_pins.py` — every pinned `uses:` SHA must match the upstream tag in
  its version comment. Detects retag-after-pin drift and lying comments. It
  cannot detect a release that was already compromised when pinned; that is
  what release-note review and the escalation tier are for.
- Ecosystem integrity mode where the repo has one: `npm ci` (lockfile integrity
  hashes), `pip install --require-hashes`, `cargo --locked`, etc.
- Advisory lookup (OSV / GitHub Advisory DB) for each new version — attested in
  the record.

## Merge rules

- No auto-merge for anything that executes in CI or at build time: actions,
  build plugins, install hooks. A human merges, with the record and green
  checks in front of them.
- Lockfile-only patch bumps of dev-dependencies may be auto-merged if a repo
  explicitly opts in; that opt-in belongs in the repo's `baseline.md`.

## Adoption

Manifest/lockfile-only diffs currently pass the gate with a warning if no
record exists (warn-first, same policy as the baseline check); the warning
becomes a hard failure in a future major version. Workflow pin bumps already
gate — the routine tier is what makes them cheap. Agents: use the
`sdl-dep-update` skill to author the record and run the checks.
