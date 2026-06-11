# 01 — Requirements

## Summary

Provide a lightweight way to read a repo's `docs/sdl/` cycles as rendered HTML instead of raw markdown. A launcher script (`scripts/sdl-serve.py`, stdlib only) starts a localhost HTTP server that overlays two roots: the viewer assets (`viewer/index.html` + a pinned `viewer/marked.min.js`) served from the governance install, and the markdown read live from the target repo's `docs/sdl/`. The page fetches a server-built JSON manifest of the cycle tree and renders each file client-side with `marked`. The viewer lives once in `~/.sdl-governance` (a clone of this repo); nothing is copied into consumer repos, and `sync-to-repo.sh` is unchanged.

## Scope

In scope: `scripts/sdl-serve.py` (launcher + request handler), `viewer/index.html` (single-page viewer), `viewer/marked.min.js` (vendored renderer, pinned), and documentation of the command in `docs/developer-guide.md` and the `install.sh` usage footer. Out of scope: any change to `sync-to-repo.sh` or what lands in consumer repos (nothing new); server-side markdown rendering (done client-side); authentication (localhost, single-user, read-only by design); serving anything outside `docs/sdl/`.

## Assets touched <!-- SR-1 -->

A new workstation script (baseline:B3 class) and two static viewer assets in the governance install. At runtime the server reads files under the target repo's `docs/sdl/` and serves them to a local browser. No credentials, no writes, no network egress.

## Trust boundaries crossed <!-- SR-2 -->

New: a localhost HTTP listener. Untrusted input is the request URL path, which the handler maps to a file on disk — the boundary where path traversal must be contained. The rendered markdown content originates from the developer's own repo (same trust as opening the file in an editor).

## Data classification <!-- SR-1 -->

Public repo governance docs. No secrets, PII, or credentials. The server has read access to the developer's filesystem under its process privileges, so traversal containment is what keeps it scoped to `docs/sdl/`.

## External inputs introduced <!-- SR-2 -->

One: HTTP request paths to the localhost server (`do_GET`). Three route classes — `/_manifest` (no filesystem input), `/_viewer/*` (mapped under the viewer dir), and everything else (mapped under `docs/sdl/`). The `--port` and `repo` CLI args are developer-supplied, not remote.

## Security requirements <!-- SR-3, SR-4 -->

- Request paths must not resolve to any file outside their designated root (`docs/sdl/` or the viewer dir), including via `../`, URL-encoding, absolute paths, or symlinks.
- The server must bind `127.0.0.1` only — never expose repo contents on the network.
- The server is read-only: no method other than GET/HEAD, no writes.
- The vendored renderer must be version- and hash-pinned; a mismatch must be surfaced.

## Related prior cycles

None. The viewer is standalone; it adds no logic to the validator, workflow, or skills.

## Carried-forward residual risks

None. No prior cycle deferred a residual risk this cycle addresses.
