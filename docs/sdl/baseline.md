# SDL Baseline

Repo-level security baseline for `savioke/sdl`, the SDL governance tooling itself. Authored when this repo adopted SDL (dogfooding). Per-feature cycles reference this file instead of re-deriving it.

## System overview

SDL governance tooling for savioke. Public GitHub repo, no runtime service. Components:

- `plugins/sdl/lib/validate.py` — the CI gate validator. Python, standard library only.
- `.github/workflows/sdl-validate.yml` — reusable workflow consumers call via `workflow_call`.
- `plugins/sdl/skills/` — agent skill definitions (`sdl-spec`, `sdl-threat-model`, `sdl-review`, `sdl-baseline`, `sdl-dep-update`) executed by Claude Code / Copilot / Antigravity / Codex.
- `plugins/sdl/templates/` — markdown artifact stubs copied into each cycle.
- `scripts/install.sh` — symlinks skills onto a developer workstation; `scripts/sync-to-repo.sh` — onboards a consumer repo.
- `scripts/release.sh` — cuts a release; `scripts/check_release.py` — detects release drift in CI.
- Distributed by tagged release (`docs/releasing.md`), never from `main`: consumer CI resolves the moving major alias, `@v2` today; Claude Code developers get the `sdl@relay` plugin, which the `savioke/relay-plugin-marketplace` manifest pins to the immutable `vX.Y.Z` tag; Copilot/other-agent developers use per-developer clones at `~/.sdl-governance` (skills via symlink), which track `main` and are the one channel not fed by a tag.

## Deployment and exposure model

No runtime, no network listeners, no datastore, no PII, no secrets in the repo. Public repository. The execution surface is other machines and CI, not a server here:

- The reusable workflow and validator execute in **every consumer repo's CI**, with that repo's `GITHUB_TOKEN`.
- `install.sh` / `sync-to-repo.sh` execute on **developer workstations** with the developer's privileges.
- Skill `.md` files are executed as instructions by **agents** in developer and CI contexts.

Single maintainer. PR review is the primary gate on changes, now augmented by this repo's own SDL cycle and the `self-check.yml` unit tests.

## Trust boundaries and standing data flows

- **This repo → consumer CI.** A change to `validate.py`, `sdl-validate.yml`, or a skill changes behavior in every consumer. Highest blast radius. Crossing point: the major alias consumers pin, `@v2` today.
- **This repo → developer workstation (Claude Code).** The `sdl@relay` plugin is fetched from this repo's `main` as directed by the manifest in `savioke/relay-plugin-marketplace`. Crossing point: that manifest's `source` (url/path/ref) — an integrity asset that lives outside this repo and its SDL gate.
- **This repo → developer workstation (scripts).** `install.sh` writes a symlink into `~/.copilot/skills`; `sync-to-repo.sh` writes files into an arbitrary target repo.
- **Public read / public call.** Anyone can read the repo, and any repo can call the reusable workflow — by design, so external fork PRs can be validated without a shared secret.

## Assets and data classification

No confidentiality assets: the repo is public and holds no secrets or customer data. The assets are **integrity** assets — compromising any executes attacker-controlled logic in consumer CI or on developer machines:

- `plugins/sdl/lib/validate.py`, `.github/workflows/sdl-validate.yml`
- skill instructions under `plugins/sdl/skills/`
- `scripts/install.sh`, `scripts/sync-to-repo.sh`
- the marketplace manifest in `savioke/relay-plugin-marketplace` (external to this repo — see B7)

`security-checks.md` and `docs/62443-mapping.md` disclose review categories and internal audit prose — low sensitivity, accepted public (see `docs/admin-setup.md`).

## Standing security requirements

- All changes land via PR; the maintainer self-reviews (single maintainer, no second human reviewer).
- This repo runs its own SDL gate (`.github/workflows/sdl.yml`), self-referentially, on the same moving alias every other consumer pins — `@v2` today. It is gated by the release consumers get, not by `main`, so a regression that would break them breaks this repo too.
- The validator stays standard-library only — no third-party dependencies, so no dependency supply-chain of its own.
- CI must pass: validator unit tests, `shellcheck` on scripts, structure checks.
- Workflows must pin third-party actions by commit SHA; `actions/*` are pinned and kept current by Dependabot (see B6).
- Shipped content reaches consumers only through a tagged release cut by `scripts/release.sh` from a green `main` (`docs/releasing.md`). Released tags are immutable; only the `vX` alias moves, and only for changes that cannot fail a previously-passing PR.
- No CI job holds a credential that can write a tag or the marketplace manifest — CI detects release drift, the maintainer performs releases.

## Standing risk register

| ID | Description | Severity | Disposition | Owner / trigger to revisit |
|----|-------------|----------|-------------|----------------------------|
| B1 | Supply-chain integrity of the validator/workflow: a malicious or buggy change to `lib/validate.py` or `sdl-validate.yml` runs in every consumer's CI with their `GITHUB_TOKEN`. | high | mitigate-later | PR review + unit tests + self-gate today. Revisit (second reviewer / signed releases) on a second maintainer or more consumers. |
| B2 | Skill-instruction injection: skill `.md` files are executed by agents; a hostile edit hijacks agent behavior in dev/CI, no compiler in the way. | medium | mitigate-later | PR review; skills are now gated as code by the validator. Revisit on any skill change. |
| B3 | Workstation scripts run with developer privileges: `install.sh` / `sync-to-repo.sh` write into `~/.claude`, `~/.copilot`, and target repos. | medium | accept | Small, auditable, `shellcheck`-gated. Revisit if the scripts gain network fetches or privileged operations. |
| B4 | Publicly-callable reusable workflow: any GitHub repo can call `sdl-validate.yml` at any ref. By design (fork-PR validation); it runs only against the caller's checkout with the caller's token and exposes no savioke secret. | low | accept | Revisit if any secret is ever introduced into the workflow. |
| B5 | Moving major alias: consumers pin `@vX` (`@v2` today) and accept that it moves, so a bad release reaches all of them at once. Partially mitigated 2026-08-03 (cycle 2026-08-03-release-process): every release also cuts an immutable signed `vX.Y.Z`, the plugin channel consumes that rather than a moving ref, the compatibility contract confines alias moves to changes that cannot fail a passing PR, and consumers may pin an exact tag. The blast radius of a bad in-contract release on the CI channel is unchanged and inherent to zero-friction delivery. | medium | accept | Revisit if a release ever breaks a consumer, or on a second maintainer (staged rollout, canary repo). |
| B6 | Unpinned third-party actions: a compromised action tag would run in CI. Mitigated 2026-06-10 (cycle 2026-06-10-pin-actions-sha): `actions/*` pinned by commit SHA, Dependabot keeps them current. Reached consumer CI 2026-07-09 when `v1` advanced (cycle 2026-07-09-actions-3e1200532a). | medium | mitigated | Revisit if a new unpinned action is added. Tag moves lag merges — a mitigation in `sdl-validate.yml` is not live for consumers until the major alias advances. |
| B7 | Marketplace manifest lives outside this repo's gates: `savioke/relay-plugin-marketplace` has no SDL cycle, CI, or validator, yet its `source` field decides what code `sdl@relay` delivers to Claude Code developer machines. A malicious or mistaken edit repoints the plugin at arbitrary code. Partially mitigated 2026-08-03 (cycle 2026-08-03-release-process): `source.ref` pins an immutable release tag instead of `main`, so unreviewed commits to `main` no longer reach developers, and `check_release.py` fails this repo's CI daily if the manifest stops naming the released tag. Write access to that repo remains the exposure. | medium | accept | Org-member-only write access; drift is now detected within a day. Revisit (branch protection, SDL gating) when the marketplace gains more plugins, maintainers, or users. |

## Maintenance

Update this file when the exposure model changes, a standing risk is closed or added, or a major component is introduced or removed. It is not per-cycle; most PRs leave it untouched.
