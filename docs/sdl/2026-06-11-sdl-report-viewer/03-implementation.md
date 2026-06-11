# 03 — Implementation

## Summary of changes

Added `scripts/sdl-serve.py`, a stdlib-only launcher that starts an `http.server` bound to `127.0.0.1`. Its `do_GET` routes `/` and `/_viewer/*` to the install's `viewer/` dir, `/_manifest` to a server-built JSON tree of `docs/sdl/`, and every other path to a file under the target repo's `docs/sdl/`; `safe_join` enforces that resolved paths stay within their root. Added `viewer/index.html` (single-page app: fetch manifest, build sidebar, render markdown with `marked`, `.yml` as plain text) and `viewer/marked.min.js` (vendored marked v12.0.2). Documented the command in `docs/developer-guide.md` and the `install.sh` usage footer. `sync-to-repo.sh` is untouched, so consumer repos gain nothing.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | `safe_join` unquotes, `normpath`-collapses, `resolve()`s, and requires the target to equal or descend from the resolved root; else 404. `resolve()` also defeats symlink escapes. Localhost-only bind and GET/HEAD-only handler bound the impact. | `scripts/sdl-serve.py` `safe_join` + `do_GET` + `HTTPServer(("127.0.0.1", …))` | 848a814 |
| T2 | marked pinned to v12.0.2, committed and PR-reviewed; SHA-256 recomputed at startup and warned on mismatch against the pinned constant. | `scripts/sdl-serve.py` `MARKED_SHA256` check; `viewer/marked.min.js` | 848a814 |

## Secure coding practices applied <!-- SI-2 -->

- **Path containment:** all filesystem mapping goes through `safe_join`; no request path reaches the filesystem without the resolve-and-contain check. Verified against `../`, URL-encoded `%2e%2e`, and `_viewer/../scripts/` probes (all 404).
- **Least exposure:** binds `127.0.0.1` (not `0.0.0.0`); read-only (GET/HEAD only — no other method handled); no writes anywhere.
- **No untrusted deserialization / no shell:** manifest is built from `pathlib` directory walks and emitted with `json.dumps`; `.sdl-meta.yml` is parsed by a minimal scalar line-split, not a YAML loader, and only whitelisted fields are read. No `subprocess`, no `eval`.
- **Dependency integrity:** vendored renderer pinned by version and SHA-256, checked at startup.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

One vendored client-side asset: `marked` v12.0.2 (MIT), `viewer/marked.min.js`, sha256 `15fabce5b65898b32b03f5ed25e9f891a729ad4c0d6d877110a7744aa847a894`. It runs only in the developer's browser and is absent from CI and from consumer repos. No Python dependencies added (stdlib only).

## Deviations from spec or threat model

None. Implementation matches `01`/`02`.
