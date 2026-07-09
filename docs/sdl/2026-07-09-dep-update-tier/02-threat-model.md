# 02 — Threat Model

## Components and data flows

- `lib/validate.py` dependency-update class — new parsing paths (changed-file classifier, workflow pin-line diff parser, `dep-update.md` version table parser) running in every consumer's CI against attacker-authored PR content.
- `lib/check_pins.py` — new stdlib tool; reads workflow files, calls `api.github.com` over HTTPS to resolve tags, compares SHAs. Runs in this repo's `self-check.yml`; consumers adopt via policy.
- `templates/docs-sdl/dep-update.md` — inert template for the routine-tier record.
- `skills/sdl-dep-update/SKILL.md` — agent-executed instructions (standing exposure per `baseline:B2`).
- `docs/dependency-updates.md` — inert policy prose.

## Threats <!-- SR-2 -->

### T1 — Gate softening via classifier bypass

- **Category:** Elevation of privilege (of a code change past the full-cycle gate)
- **Component / flow:** `validate.py` dependency-only classifier, evaluating attacker-authored diffs in consumer CI.
- **Description:** A PR sets `class: dependency-update` and shapes a diff the classifier accepts as dependency-only while it actually alters executable behavior — e.g. a workflow hunk that swaps *which* action runs while keeping pin-line shape (`uses: actions/checkout@<sha>` → `uses: evil/checkout@<sha> # v7.0.0`), or a code file placed at a path on the manifest allowlist. The result is code review evidence downgraded, not code execution — but at fleet scale a quiet downgrade is how supply-chain changes stop being looked at.
- **Likelihood / Impact:** medium / medium
- **Mitigation:** Fail-closed design: exact-filename allowlist for manifests/lockfiles (no glob patterns); workflow hunks accepted only when every removed and added line is pin-shaped, the added ref is a 40-hex SHA, and the `owner/repo` of each added line matches a removed line in the same file (new or renamed actions disqualify); anything unclassifiable → full cycle required. Declaring the class on a non-qualifying diff is a hard fail, not a fallback to the old behavior.
- **Mitigation type:** preventive
- **Defense in depth notes:** Human merge review remains mandatory (no auto-merge for CI-executing changes, per policy doc); unit tests pin the classifier's rejection cases so a future refactor can't silently widen it.

### T2 — Rubber-stamp record: declared checks that never ran

- **Category:** Repudiation
- **Component / flow:** routine-tier record → validator → audit trail.
- **Description:** `dep-update.md` is authored by the PR (human or agent) and can claim "pins verified, advisories reviewed" without either having happened. At volume, unverifiable self-attestation converges on fiction.
- **Likelihood / Impact:** high / low per event, systemic if normalized
- **Mitigation:** The validator trusts the record only for what it cannot recompute: it independently re-derives major-vs-minor from workflow pin comments in the diff and fails when the diff shows a major regardless of what the record declares; `check_pins.py` re-verifies SHA↔tag in CI rather than trusting the record's claim. What remains attested-only (release-note review, advisory lookup for language ecosystems) is explicitly labeled as attestation in the template.
- **Mitigation type:** detective
- **Defense in depth notes:** Escalation triage is computed from the diff, not the record, wherever possible.

### T3 — Tampered lockfile rides the routine tier

- **Category:** Tampering
- **Component / flow:** lockfile-only diffs accepted at the routine tier; lockfiles direct what package managers download and execute in consumer CI/builds.
- **Description:** A "version bump" lockfile diff can also rewrite resolved URLs or integrity hashes to attacker-controlled artifacts (dependency confusion, registry redirect). The routine tier deliberately does not parse per-ecosystem lockfiles, so the validator cannot see this.
- **Likelihood / Impact:** low / high
- **Mitigation:** Not mitigated by the validator — honestly out of its reach without per-ecosystem parsers (out of scope this cycle). Policy compensates: routine tier requires ecosystem integrity mode in CI (`npm ci`, `pip --require-hashes` where used), human merge review, and bumps sourced from trusted automation; a hand-authored lockfile edit from an unfamiliar contributor is a triage escalation trigger in the policy doc.
- **Mitigation type:** preventive (policy) + detective (ecosystem integrity checking)
- **Defense in depth notes:** Signpost below to revisit with per-ecosystem verification if fleet volume or contributor base grows.

## Threats inherited from prior cycles <!-- SR-2 -->

- **baseline:B1** — `validate.py` changes run in every consumer's CI. This cycle *adds parsing paths* to that asset; mitigation unchanged (PR review, unit tests, self-gate) and extended with classifier rejection tests.
- **baseline:B2** — new skill `sdl-dep-update` is agent-executed instructions; gated as code by the validator as before.
- **2026-07-09-actions-3e1200532a:T1** (malicious upstream release enters CI on a bump) — still live at every bump; the routine tier systematizes its mitigation (SHA↔tag verification becomes a tool run in CI instead of a hand-run check).
- **Disposition change:** `2026-06-10-pin-actions-sha` declared "Dependabot bump PRs trip the SDL gate; each supply-chain bump gets a quick review cycle" as intended behavior. This cycle deliberately revises that: full cycles for routine minor bumps don't scale to a fleet and dilute review attention. Recorded here so the trail shows the decision, not drift.

## Out-of-scope threats

- `check_pins.py` trusting a tag the attacker moved *before* the PR pinned it — the tool detects retag-after-pin drift, not a compromised release itself; release-integrity review stays a triage/human concern (owner: policy escalation tier).
- api.github.com spoofing/MITM — stdlib HTTPS with default certificate verification; platform trust root is the owner.
- CI outage or GitHub API rate limiting failing `check_pins` — availability-only, fails the build loudly, no integrity impact.
- `GITHUB_TOKEN` in `check_pins.py` — optional, read-only rate-limit relief, never printed; no new scope (baseline:B4 posture unchanged).

## Noted for future cycles

- If `check_pins` moves into `sdl-validate.yml` for consumers, model fleet-scale rate-limit DoS and the upstream-retag false-positive path first.
- If routine-tier volume invites auto-merge, threat-model that separately — current policy forbids it for CI-executing changes.
- Per-ecosystem lockfile verification (resolved-URL/integrity diff parsing) would close T3's validator blind spot; revisit if the fleet contributor base widens.
- Regexes added to `validate.py` parse adversarial content; keep them anchored and linear-time as they evolve.
