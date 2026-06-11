# SDL Baseline

Repo-level security baseline for `savioke/sdl`, the SDL governance tooling itself. Authored when this repo adopted SDL (dogfooding). Per-feature cycles reference this file instead of re-deriving it.

## System overview

SDL governance tooling for savioke. Public GitHub repo, no runtime service. Components:

- `lib/validate.py` — the CI gate validator. Python, standard library only.
- `.github/workflows/sdl-validate.yml` — reusable workflow consumers call via `workflow_call`.
- `skills/` — agent skill definitions (`sdl-spec`, `sdl-threat-model`, `sdl-review`, `sdl-baseline`) executed by Claude Code / Copilot.
- `templates/` — markdown artifact stubs copied into each cycle.
- `scripts/install.sh` — symlinks skills onto a developer workstation; `scripts/sync-to-repo.sh` — onboards a consumer repo.
- Distributed via the `@v1` tag (CI) and per-developer clones at `~/.sdl-governance` (skills via symlink).

## Deployment and exposure model

No runtime, no network listeners, no datastore, no PII, no secrets in the repo. Public repository. The execution surface is other machines and CI, not a server here:

- The reusable workflow and validator execute in **every consumer repo's CI**, with that repo's `GITHUB_TOKEN`.
- `install.sh` / `sync-to-repo.sh` execute on **developer workstations** with the developer's privileges.
- Skill `.md` files are executed as instructions by **agents** in developer and CI contexts.

Single maintainer. PR review is the primary gate on changes, now augmented by this repo's own SDL cycle and the `self-check.yml` unit tests.

## Trust boundaries and standing data flows

- **This repo → consumer CI.** A change to `validate.py`, `sdl-validate.yml`, or a skill changes behavior in every consumer. Highest blast radius. Crossing point: the `@v1` tag consumers pin.
- **This repo → developer workstation.** `install.sh` writes symlinks into `~/.claude/skills` and `~/.copilot/skills`; `sync-to-repo.sh` writes files into an arbitrary target repo.
- **Public read / public call.** Anyone can read the repo, and any repo can call the reusable workflow — by design, so external fork PRs can be validated without a shared secret.

## Assets and data classification

No confidentiality assets: the repo is public and holds no secrets or customer data. The assets are **integrity** assets — compromising any executes attacker-controlled logic in consumer CI or on developer machines:

- `lib/validate.py`, `.github/workflows/sdl-validate.yml`
- skill instructions under `skills/`
- `scripts/install.sh`, `scripts/sync-to-repo.sh`

`security-checks.md` and `docs/62443-mapping.md` disclose review categories and internal audit prose — low sensitivity, accepted public (see `docs/admin-setup.md`).

## Standing security requirements

- All changes land via PR; the maintainer self-reviews (single maintainer, no second human reviewer).
- This repo runs its own SDL gate (`.github/workflows/sdl.yml`, self-referential at `@v1`).
- The validator stays standard-library only — no third-party dependencies, so no dependency supply-chain of its own.
- CI must pass: validator unit tests, `shellcheck` on scripts, structure checks.
- Workflows should pin third-party actions; today they pin by major tag (see B6).

## Standing risk register

| ID | Description | Severity | Disposition | Owner / trigger to revisit |
|----|-------------|----------|-------------|----------------------------|
| B1 | Supply-chain integrity of the validator/workflow: a malicious or buggy change to `lib/validate.py` or `sdl-validate.yml` runs in every consumer's CI with their `GITHUB_TOKEN`. | high | mitigate-later | PR review + unit tests + self-gate today. Revisit (second reviewer / signed releases) on a second maintainer or more consumers. |
| B2 | Skill-instruction injection: skill `.md` files are executed by agents; a hostile edit hijacks agent behavior in dev/CI, no compiler in the way. | medium | mitigate-later | PR review; skills are now gated as code by the validator. Revisit on any skill change. |
| B3 | Workstation scripts run with developer privileges: `install.sh` / `sync-to-repo.sh` write into `~/.claude`, `~/.copilot`, and target repos. | medium | accept | Small, auditable, `shellcheck`-gated. Revisit if the scripts gain network fetches or privileged operations. |
| B4 | Publicly-callable reusable workflow: any GitHub repo can call `sdl-validate.yml@v1`. By design (fork-PR validation); it runs only against the caller's checkout with the caller's token and exposes no savioke secret. | low | accept | Revisit if any secret is ever introduced into the workflow. |
| B5 | Moving `v1` tag: consumers pin `@v1` and accept moving tags, so a bad release reaches all of them at once; a force-moved tag also weakens reproducibility. | medium | accept | Single consumer today. Revisit (recommend pinning exact tags or immutable releases) as consumer count grows. |
| B6 | Unpinned third-party actions: workflows pin `actions/*` by major tag (`@v4`, `@v5`), not by SHA; a compromised action tag would run in CI. | medium | mitigate-later | Pin by SHA. Revisit on the next workflow edit. |

## Maintenance

Update this file when the exposure model changes, a standing risk is closed or added, or a major component is introduced or removed. It is not per-cycle; most PRs leave it untouched.
