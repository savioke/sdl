# 02 — Threat Model

## Components and data flows

- **`scripts/sdl-serve.py`** — stdlib `http.server` bound to `127.0.0.1`. A custom `do_GET` maps request paths to files under one of two roots (target repo's `docs/sdl/`, or the install's `viewer/`) and builds a JSON manifest by walking `docs/sdl/`. Read-only; no writes, no network egress.
- **`viewer/index.html`** — single-page app. Fetches `/_manifest`, then fetches and renders selected files; markdown via `marked`, `.sdl-meta.yml` as plain text in a `<pre>`.
- **`viewer/marked.min.js`** — vendored third-party renderer (marked v12.0.2), runs in the developer's browser.

## Threats <!-- SR-2 -->

### T1 — Path traversal escaping the served roots

- **Category:** Information disclosure
- **Component / flow:** `do_GET` → `safe_join` mapping a request URL to a filesystem path.
- **Description:** A crafted request (`../`, URL-encoded `%2e%2e`, absolute path, or a symlink inside `docs/sdl/` pointing out) could map outside `docs/sdl/` (or the viewer dir) and read arbitrary files readable by the developer's account.
- **Likelihood / Impact:** low / medium — the listener is localhost-only (a remote attacker can't reach it), but a malicious link/script targeting `127.0.0.1` in the dev's browser, or a hostile symlink committed to a repo, makes it reachable.
- **Mitigation:** `safe_join` unquotes, `posixpath.normpath`-collapses, then `resolve()`s the candidate and requires it to be the root or a descendant of the *resolved* root (`root in target.parents`); anything else returns 404. `resolve()` also collapses symlinks, so a symlink out of the root fails the containment check. Verified with `../`, encoded `%2e%2e`, and `_viewer/../scripts/` probes.
- **Mitigation type:** preventive
- **Defense in depth notes:** binds `127.0.0.1` only (no LAN exposure); read-only (GET/HEAD), so traversal can disclose but not write; serves bytes only for paths that pass containment and exist as files.

### T2 — Tampering with the vendored renderer

- **Category:** Tampering
- **Component / flow:** `viewer/marked.min.js` loaded and executed in the developer's browser.
- **Description:** If the vendored JS were swapped for a malicious build (bad commit, compromised mirror at vendor time), arbitrary script would run in the viewer with access to the rendered docs.
- **Likelihood / Impact:** low / medium
- **Mitigation:** pinned to marked v12.0.2 and committed (git-tracked, PR-reviewed like any dependency). `sdl-serve.py` recomputes the file's SHA-256 at startup and warns on mismatch against the pinned constant (`15fabce5…847a894`).
- **Mitigation type:** detective (startup hash check) + preventive (version pin, PR review, git history)
- **Defense in depth notes:** the asset is served only over localhost to the same user; no auto-update path fetches a newer build at runtime.

## Threats inherited from prior cycles <!-- SR-2 -->

- **baseline:B3** — workstation scripts run with developer privileges. `sdl-serve.py` is such a script and, unlike `install.sh`/`sync-to-repo.sh`, it opens a network listener and serves files — exactly B3's "revisit if the scripts gain network fetches or privileged operations" trigger. That new surface is threat-modeled here as T1 (containment) and bounded to localhost/read-only, so B3's `accept` disposition still holds for this script.

## Out-of-scope threats

- Denial of service against the localhost server — single local user, ephemeral process; not a meaningful target. Owner: accepted.
- Authentication / authorization — by design none; localhost, single-user, read-only view of the user's own files. Owner: accepted.

## Noted for future cycles

- The viewer renders markdown HTML without sanitizing (`marked` passes raw HTML through), so it trusts the repo's own docs. If viewing *untrusted* repos ever becomes a use case, add a sanitizer (e.g. DOMPurify) — tracked as residual risk R1 in `04`.
- If the launcher ever gains write capability, a non-localhost bind, or a runtime fetch to refresh assets, re-threat-model against B3 and B5.
