# 02 — Threat Model

<!-- SR-2: Threat model. SD-1, SD-2: Secure design and defense in depth. -->

## Components and data flows

- **`scripts/release.sh`** — runs on the maintainer's workstation with their git push and `gh` credentials. Reads the version from `plugin.json`, queries `gh` for the commit's check runs, creates and pushes tags to `savioke/sdl`, clones `savioke/relay-plugin-marketplace` to a temp dir, rewrites its manifest, pushes.
- **`scripts/check_release.py`** — runs in this repo's CI with the default `GITHUB_TOKEN` (read-only for this purpose). Reads local git history and, in released mode, fetches the marketplace manifest over HTTPS.
- **`vX.Y.Z` / `vX` tags** — the crossing point into every consumer's CI (`baseline.md`, "This repo → consumer CI").
- **Marketplace manifest** — the crossing point into developer agents (`baseline:B7`). Written by `release.sh`, read by `check_release.py`, read by Claude Code at install/update.

New flow this cycle: an externally-hosted document is fetched into this repo's CI (T1). New privileged operation: an automated write into a second repo that feeds developer machines (T3).

## Threats <!-- SR-2 -->

### T1 — Hostile or malformed manifest fetched into CI

- **Category:** Tampering / Denial of service
- **Component / flow:** `check_release.py` → `raw.githubusercontent.com` → `json.loads` in this repo's CI.
- **Description:** The released-mode check parses a document this repo does not control. Whoever serves it (the marketplace repo's writers, or anyone able to break TLS) chooses its size, shape, and contents. Unbounded reading lets the responder decide how much memory the runner spends; unhandled parse failures turn an outage into a red `main`, which trains the maintainer to ignore the signal.
- **Likelihood / Impact:** low / low — the parsed values are only compared and printed. Nothing from the manifest is executed, interpolated into a shell, or written to disk.
- **Mitigation:** HTTPS with default certificate verification; 30-second timeout; read capped at 1 MB before parsing (`check_release.py`, `fetch_manifest`); every failure mode — HTTP error, transport error, oversize, malformed JSON — returns an error value rather than raising, and the caller downgrades it to a note (SR-8). Only a manifest that is fetched *and* parsed *and* disagrees fails the build.
- **Mitigation type:** preventive
- **Defense in depth notes:** The check is itself a detective control for `baseline:B7`. An attacker who alters the manifest to repoint the plugin cannot both do so and keep this check green — suppressing detection requires leaving `source.ref` at the released tag, which is the thing being protected.

### T2 — Version string reaching a shell and a ref name

- **Category:** Elevation of privilege
- **Component / flow:** `plugin.json` `version` → `release.sh` → `git tag`, `git push`, marketplace commit message.
- **Description:** The version is repo-controlled data that becomes a git ref name, a tag message, and a commit message on the maintainer's workstation. A crafted value (`1.0.0; …`, `../../evil`, a newline) landing in `plugin.json` would execute or write outside the intended target when the maintainer next releases. Reachable by anyone who can merge a `plugin.json` edit.
- **Likelihood / Impact:** low / high — requires a merged PR, but succeeds against the maintainer's own credentials, which can write both distribution channels.
- **Mitigation:** the version is matched against `^[0-9]+\.[0-9]+\.[0-9]+$` before any use (`release.sh`, step 2) and the release aborts otherwise; the alias is derived from the validated string by parameter expansion, not by re-parsing; every expansion is quoted; the same rule gates in CI at PR time (`check_release.py`, `SEMVER_RE`), so a non-conforming version fails review before it can reach a release.
- **Mitigation type:** preventive
- **Defense in depth notes:** Two independent enforcement points (PR-time check, release-time check) with the same rule, so neither is load-bearing alone. Inherits `baseline:B2` — a hostile `plugin.json` edit implies the same review failure that a hostile skill edit does.

### T3 — Write access to the distribution channel

- **Category:** Elevation of privilege
- **Component / flow:** `release.sh` → tags in `savioke/sdl`; `release.sh` → manifest in `savioke/relay-plugin-marketplace`.
- **Description:** Whatever can move the `vX` alias or rewrite the manifest can ship arbitrary code to every consumer's CI and every developer's agent — the highest-blast-radius capability in this system (`baseline:B1`, `baseline:B7`). The obvious convenience is to have CI do it on merge, which would place that capability in a workflow-triggered job holding a long-lived cross-repo token. Any compromise of this repo's workflows, or of a token in its secret store, would then be a supply-chain compromise of every governed repo, and the credential would be exposed continuously rather than at the moments a human is releasing.
- **Likelihood / Impact:** low / high
- **Mitigation:** the capability is deliberately not automated. No workflow in this repo holds a credential that can write a tag or the manifest; CI only *detects* drift (`check_release.py` performs no writes), and the release is performed interactively by the maintainer with their own credentials, behind a printed plan and a confirmation prompt. Immutable tags bound what a release can be: `release.sh` refuses if `vX.Y.Z` already exists locally or on the remote, so a released artifact cannot be rewritten, only superseded; and the manifest can only be pointed at a tag, never at a branch.
- **Mitigation type:** preventive
- **Defense in depth notes:** The green-checks precondition means a release cannot ship a commit this repo's own gate rejected. Tag signing, where configured, makes the releasing identity attributable after the fact — the revisit path `baseline:B1` names. Detection is independent of the actor: the daily released-mode check fails if the manifest stops naming the released tag, no matter who changed it or how.

## Threats inherited from prior cycles <!-- SR-2 -->

- **`baseline:B5` — a bad release reaches all consumers at once via the moving alias.** Still applies and is inherent to the zero-friction CI channel; N repos cannot be asked to edit a pin per release. Narrowed here, not closed: the compatibility contract (`docs/releasing.md`) confines alias moves to changes that cannot fail a previously-passing PR, new checks must land as `[warn]` before becoming failures, the plugin channel no longer consumes a moving ref at all, and a documented rollback (re-point the alias at the previous exact tag) makes recovery a single command.
- **`baseline:B1` — supply-chain integrity of the validator.** Unchanged in kind. This cycle adds two controls it names as its revisit path: signed releases, and a green-CI precondition on shipping.
- **`baseline:B2` — skill-instruction integrity.** Applies to `plugin.json` as another agent-adjacent file the release path trusts; see T2.

## Out-of-scope threats

- **Compromise of the maintainer's workstation or GitHub account.** Out of scope for any design that lets a human release; the mitigation is account hygiene and 2FA, not this repo. Signing narrows attribution, not capability.
- **A malicious commit that passes review.** Owned by `baseline:B1`/`B2` (single maintainer, no second human reviewer). The release process ships what review approved; it is not a second reviewer.
- **`gh`'s reported check conclusions being falsified.** Requires write access to this repo's workflows, which already implies the ability to ship (T3).
- **Tag race between the existence check and the push.** Git rejects a non-fast-forward push to an existing tag ref without `--force`, and `release.sh` never forces the immutable tag, so a concurrent release fails loudly rather than silently overwriting.
- **Marketplace repo write access itself.** `baseline:B7`, accepted there; this cycle reduces its reach but does not gate that repo.

## Noted for future cycles

- If `release.sh` is ever made non-interactive or moved into CI, T3's mitigation is void by construction — that change needs its own cycle, not a flag.
- The Copilot/clone channel still tracks `main` rather than a tag, so those developers can run unreleased skills. Acceptable while that population is small and self-updating; if it grows, point `install.sh` at the latest release tag.
- `SDL_RELEASE_SKIP_CI` exists for infrastructure flake. If it is ever used routinely, the green-checks precondition has become theatre and the underlying flake should be fixed instead.
- `.github/workflows/sdl-validate.yml` is a shipped path, so any automated PR that bumps an action pin in it — every Dependabot run — now fails the PR-mode check until a human adds a version bump and changelog entry. That is consistent with `docs/dependency-updates.md` (classification by diff shape, not author) and with the fact that such a PR already needs a cycle record, but it does mean no Dependabot PR touching that file can ever merge unattended. Revisit if the manual finishing step becomes a burden.
