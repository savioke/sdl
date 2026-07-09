# 01 — Requirements

## Summary

Add a tiered process for supply-chain (dependency) updates, sized for a fleet of consumer repos with frequent bumps from Dependabot, scanners, and humans. Routine minor/patch updates get a lightweight machine-checkable record instead of a full four-document cycle; major bumps, new dependencies, and anything outside the routine shape escalate to a full cycle. Motivated by cycle `2026-07-09-actions-3e1200532a`, where a full hand-written cycle for a two-pin Dependabot bump produced mostly boilerplate around two checks of real value (SHA-vs-tag verification, behavior-change review).

## Scope

In scope:

- A `class: dependency-update` cycle type recognized by `lib/validate.py`: requires `.sdl-meta.yml` + `dep-update.md` instead of the four artifacts, and only validates when the diff is dependency-shaped (manifests/lockfiles, or workflow diffs touching only SHA-pinned `uses:` lines) with no major bumps.
- A `templates/docs-sdl/dep-update.md` record template.
- `lib/check_pins.py` — deterministic verifier that every pinned `uses:` SHA matches the upstream tag named in its version comment; wired into `self-check.yml` for this repo.
- A fleet policy doc `docs/dependency-updates.md`: tier definitions, escalation triage, evidence requirements.
- An `sdl-dep-update` skill so agents author the record and run the checks.
- Warn-first (not fail) when a lockfile/manifest-only diff has no dependency-update record — those diffs pass silently today, and hard-failing would break every consumer's Dependabot flow at once (`baseline:B5` blast radius).

Out of scope: running `check_pins` inside `sdl-validate.yml` for consumers (API rate limits and upstream-retag failure modes need thought — noted for a future cycle); per-ecosystem lockfile parsers; fleet-level aggregation/dashboard.

## Assets touched <!-- SR-1 -->

`lib/validate.py` — the gate that runs in every consumer's CI (highest-blast-radius asset per `baseline.md`, B1). Skill files (B2). Templates. `self-check.yml`.

## Trust boundaries crossed <!-- SR-2 -->

The repo→consumer-CI boundary: this change alters what the gate accepts. A flaw here doesn't execute attacker code directly, but a too-loose classifier lets code changes ride through consumer CI under the light tier — a gate-weakening, not a code-execution, failure. `check_pins.py` adds an outbound HTTPS call from CI to api.github.com.

## Data classification <!-- SR-1 -->

None. Public repo, no secrets — per `baseline.md`. `check_pins.py` reads `GITHUB_TOKEN` from the environment if present (rate limits only) and must never print it.

## External inputs introduced <!-- SR-2 -->

- `check_pins.py` parses workflow YAML from the repo under validation and JSON responses from api.github.com (untrusted-ish: attacker-influenced only via upstream compromise).
- `validate.py` newly parses diff content (pin lines, version comments) and `dep-update.md` (declared version table), both authored by the PR under validation — adversarial input by definition.

## Security requirements <!-- SR-3, SR-4 -->

- The dependency-only classifier must fail closed: any changed file or diff line it cannot positively classify as dependency-shaped disqualifies the light tier and requires a full cycle.
- Routine tier rejects: major version bumps (declared in the record or observed in workflow pin comments), new `uses:` entries without a removed counterpart, unpinned (non-40-hex) action refs, missing/unparseable version comments.
- `validate.py` stays standard-library only and network-free; `check_pins.py` is stdlib-only and is the only component that touches the network.
- Existing full-cycle behavior is unchanged for non-dependency diffs; a `class: dependency-update` meta on a non-dependency diff must fail, not soften the gate.
- New logic covered by unit tests in `lib/test_validate.py` (and a test module for `check_pins.py`).

## Related prior cycles

- `2026-06-10-pin-actions-sha` — established SHA pinning and Dependabot; this cycle builds the process for keeping those pins current at fleet scale.
- `2026-07-09-actions-3e1200532a` — the hand-written bump cycle whose cost/value ratio motivated this design.

## Carried-forward residual risks

None recorded as deferred in related cycles. This cycle formalizes the "pins must be kept current or B6 reopens" maintenance note from `2026-06-10-pin-actions-sha` into a checked process.
