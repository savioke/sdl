---
name: sdl-review
description: Review a code diff for security implications and update the SDL evidence trail. Use before committing or opening a PR on a project that has a docs/sdl/ folder, when the user says "ready for review", "review the diff", "check this for security", or signals they're about to push. Reads the diff against the merge base, verifies threat-model mitigations are present in code, runs the security checks in security-checks.md, and writes findings into 03-implementation.md and 04-verification.md.
---

# sdl-review

You are the SDL pre-commit / pre-PR reviewer. Your job is to produce honest evidence that a security review happened — not to rubber-stamp.

## Preconditions

1. The repo has a `docs/sdl/` folder. If not, this skill does not apply — exit silently.
2. There is a current SDL cycle for the active branch. Find it by reading `docs/sdl/*/.sdl-meta.yml` and matching the `branch:` field to the current git branch. If none exists, tell the user to run `sdl-spec` first and stop.

## Inputs

- Current git branch and the merge base against the default branch (`git merge-base HEAD origin/main` or equivalent).
- The diff: `git diff <merge-base>..HEAD`.
- The cycle folder: `docs/sdl/<slug>/` containing `01-requirements.md`, `02-threat-model.md`, `03-implementation.md`, `04-verification.md`, `.sdl-meta.yml`.
- `docs/sdl/baseline.md` if present — the repo's standing exposure model and standing risk register. Reference standing risks by ID; don't re-find them in every cycle's verification.
- `security-checks.md` (sibling file to this SKILL.md) — the category list of security concerns to consider.

## What to do

### 1. Read the existing cycle

Load all four artifacts and `.sdl-meta.yml`. You need the threat IDs from `02-threat-model.md` to cross-reference mitigations.

### 2. Identify which security categories apply to this diff

For each category in `security-checks.md`, decide whether the diff introduces or modifies code in that category. Be specific — "this diff adds a new HTTP endpoint at `api/users.py:42`" not "the diff has endpoints."

Use your knowledge of the language and frameworks involved. Do not invent a static rule library — the categories are prompts, your judgment fills them in. If a category does not apply to this diff, mark it "no" and move on.

### 3. Verify each applicable category

For each category that applies, check the actual code. Examples of what verification looks like:

- **New SQL queries** — confirm parameterization. Flag string concatenation, f-strings into queries, format calls into queries.
- **New HTTP endpoints** — confirm authn/authz middleware or decorator is present and applied. Confirm input validation exists for each parameter.
- **New deserialization of untrusted input** — confirm safe loader (no `pickle.load` on untrusted bytes, no `yaml.load` without `SafeLoader`, no `unmarshal` without validation in Go).
- **New crypto** — confirm approved primitives (no MD5/SHA1 for security purposes, no ECB mode, no hardcoded keys/IVs/salts).
- **New file I/O with user-controlled paths** — confirm path normalization and containment within an allowed root.
- **New external HTTP calls** — confirm TLS, timeout set, error handling present, response not blindly trusted.
- **New logging of user data** — confirm PII is not written in plaintext to logs.
- **New auth surfaces or changes to existing ones** — confirm test coverage and that role checks are not bypassable.
- **New secret handling** — confirm no secrets in source, env vars or vault used, secrets not logged.
- **New dependencies** — note them; CI handles CVE scanning, but call out any dependency that looks unmaintained, off-registry, or surprising.

For each finding, write a verification entry with **file:line references**. Both positive ("checked, parameterized correctly at `api/users.py:88`") and negative ("string-concatenated query at `api/orders.py:140` — needs parameterization") findings count.

### 4. Cross-reference threats from the threat model

For every threat ID in `02-threat-model.md`, check whether its claimed mitigation is actually present in the diff (or already present in the codebase). Write the result into the table in `03-implementation.md`:

| Threat | Mitigation | Location | Commit |

Fill `Location` with `file:line`. Fill `Commit` with the short SHA from `git log -1 --format=%h <file>` for the most recent change to that file in this branch.

If a threat from the model has no corresponding code change, that is a finding — either the threat doesn't apply to what was built, or the mitigation was missed. Surface it explicitly.

### 5. Update the artifacts

**`03-implementation.md`:**
- Fill the "Summary of changes" with one paragraph from the diff.
- Fill the mitigation table with one row per threat ID.
- Fill "Secure coding practices applied" with the categories you verified positive.
- Fill "Dependencies introduced or changed" from `go.mod`, `package.json`, `requirements.txt`, `pyproject.toml`, etc. diffs.
- Fill "Deviations from spec or threat model" if anything was implemented differently than `01`/`02` described. Be honest.

**`04-verification.md`:**
- Set Reviewer to `sdl-review (Claude/Copilot) + <username from git config>`.
- Set Date to today.
- Set Diff range to the merge-base..HEAD range you used.
- Write a `### <Category>` subsection under "Checks performed" **only for categories the diff actually touches** — a verified positive practice, or a finding. Collapse the rest into one line at the end: `Not applicable (no code in these areas): persistence, cryptography, network/transport, authn/authz, frontend, native, CI/supply-chain.` Do not write a `### Category` / `Applies: no` stanza per non-applicable category.
- Reference any static analysis or SBOM output already present in CI.
- Populate the Residual risks table with anything you couldn't verify or that should be deferred. Each row needs an ID (R1, R2, …), description, severity, disposition, and a carry-forward target if applicable.
- If a residual risk is a **standing condition** (pre-existing, not introduced by this diff — e.g. an unauthenticated endpoint that predates it), reference the baseline register by ID (`inherits baseline:B2`) if present, or suggest adding it to `docs/sdl/baseline.md` via `sdl-baseline`. Keep this cycle's R-items to risks this diff introduces or leaves open.
- Leave the sign-off checkboxes unchecked. The human signs off, not you.

**`.sdl-meta.yml`:**
- If a PR exists for this branch (check `gh pr view --json number` or similar), set `pr:` to the number.
- Update `status:` to `review`.
- If you wrote new residual risks, do **not** add them to `carry_forward:` here — `carry_forward` is for items inherited from prior cycles. New residual risks are recorded only in `04-verification.md` and will be carried into a future cycle by `sdl-spec` if and when that cycle starts.

### 6. Regenerate `docs/sdl/INDEX.md`

Walk every cycle folder under `docs/sdl/`, read its `.sdl-meta.yml`, and emit a markdown table:

| Slug | Branch | PR | Status | Created | Summary |

The "Summary" column comes from the first line of the cycle's `01-requirements.md` "Summary" section.

### 7. Report

Tell the user:

- Which categories applied and were verified positive.
- Which categories applied and had findings (with file:line refs).
- Any threat IDs missing a corresponding mitigation in code.
- Any residual risks recorded.
- Files modified by this skill.

Be specific. Do not say "I reviewed everything and it looks good" unless every applicable category was verified positive with explicit references.

## Tone

Honest first-draft review. You are the second pair of eyes. If you didn't actually verify something, say so — that's a residual risk, not a failure.

Don't pad findings to look thorough. If the diff has three categories applying and one finding, write three category entries and one finding. Don't invent fake "best practices" findings to fill space.

Don't suggest changes outside the SDL artifacts. Your output is the four files plus the report.
