# 04 — Verification

## Review pass

- **Reviewer:** sdl-review (Claude) + Joe Cooper
- **Date:** 2026-06-11
- **Diff range:** origin/main..HEAD (`sdl-report-viewer`)

## Checks performed <!-- SVV-1, SVV-2 -->

### File I/O with request-controlled paths (T1)

- **Finding:** Every request path is mapped through `safe_join`, which unquotes, `posixpath.normpath`-collapses, `resolve()`s, and requires the result to equal or be a descendant of the resolved root, returning `None` (→ 404) otherwise. `resolve()` collapses symlinks, so a symlink committed inside `docs/sdl/` that points outside also fails containment. Confirmed live against three probes — `/../../../../etc/passwd`, URL-encoded `/%2e%2e/%2e%2e/etc/passwd`, and `/_viewer/../scripts/sdl-serve.py` — all returned 404; legitimate paths (`/INDEX.md`, `/_viewer/marked.min.js`, `/_manifest`, cycle files) served correctly.
- **References:** `scripts/sdl-serve.py` `safe_join`, `do_GET`.

### Network/transport exposure (T1 defense-in-depth)

- **Finding:** Server binds `127.0.0.1` explicitly, not `0.0.0.0` — repo contents are not reachable off-host. Handler implements only GET/HEAD (`do_HEAD = do_GET`); no write method exists, so the surface is read-only.
- **References:** `scripts/sdl-serve.py` `HTTPServer(("127.0.0.1", args.port), …)`, `do_GET`.

### Dependencies / supply chain (T2)

- **Finding:** One vendored client-side asset, `marked` v12.0.2 (MIT), pinned and committed. `sdl-serve.py` recomputes its SHA-256 at startup and warns on mismatch against the pinned constant. Absent from CI and consumer repos (`sync-to-repo.sh` unchanged). No Python dependencies added — stdlib only.
- **References:** `scripts/sdl-serve.py` `MARKED_SHA256`; `viewer/marked.min.js`.

### Secrets

- **Finding:** None introduced. The server reads and serves only `docs/sdl/` content and the static viewer assets; no credentials or tokens are read or logged (request logging is suppressed).
- **References:** full diff (3 new files, 2 doc edits).

**Not applicable (no code in these areas):** SQL/persistence, cryptography (beyond the integrity hash), authn/authz (none by design — localhost, single-user, read-only), deserialization (no YAML loader / pickle), logging of user data, concurrency, frontend build, native.

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

`scripts/sdl-serve.py` is Python (not shell), so `shellcheck` does not cover it; the repo CI (`self-check.yml`: validator unit tests, structure, `shellcheck` on the edited `install.sh`) and the SDL self-gate run on the PR. No SAST tool is wired for Python in this repo today — noted as R2. No SBOM applies to a single MIT-licensed, hash-pinned vendored asset.

## Residual risks <!-- DM-1 -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  | The viewer renders markdown HTML without sanitizing (`marked` passes raw HTML through), so it trusts the repo's own docs. Pointing it at an untrusted repo could execute embedded script in the dev's browser. | low | accept | Add DOMPurify if untrusted-repo viewing ever becomes a use case (see 02 "Noted for future cycles"). |
| R2  | No Python static analysis (lint/SAST) is wired in CI for `sdl-serve.py`; review of the handler was manual plus live traversal probes. | low | accept | Add a Python linter to `self-check.yml` if more Python lands in the repo. |
