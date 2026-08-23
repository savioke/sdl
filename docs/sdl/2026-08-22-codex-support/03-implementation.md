# 03 — Implementation

<!-- SI-1: Security implementation review. SI-2: Secure coding standards. -->

## Summary of changes

Added a Codex manifest for the existing SDL skills, a host-specific Codex
marketplace catalog, Codex installation documentation, and paired release
checks. Both source manifests declare 2.1.0; the bootstrapped marketplace
catalogs remain at released v2.0.0 until the 2.1.0 release advances them.

## Mitigations implemented <!-- SI-1 -->

<!-- One row per threat ID from 02-threat-model.md.
     Link the mitigation to the file/line and the commit that introduced it. -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Require matching plugin versions and update/check both host catalogs together. | `plugins/sdl/.codex-plugin/plugin.json`, `scripts/release.sh`, `scripts/check_release.py`, `scripts/test_check_release.py` | working tree |
| T2 | Document and enforce marketplace-first bootstrap, then tag-before-pin release ordering. | `docs/releasing.md`, `scripts/release.sh`, external `.agents/plugins/marketplace.json` | working tree |

## Secure coding practices applied <!-- SI-2 -->

- Both local manifest versions are compared before release-side effects.
- Existing strict semantic-version, shell-quoting, and bounded remote-read
  controls are reused for both catalogs.
- Catalog paths and Codex CLI subcommands are static; no evaluated input or
  generated shell command was introduced.
- The Codex catalog follows its schema by omitting the duplicated plugin version;
  the checker still validates it if a future catalog adds one.
- Installer failures are independently reported for each optional host.
- No hooks, MCP servers, executables, or runtime dependencies were added to the
  plugin bundle.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None.

## Deviations from spec or threat model

None. Claude-specific sub-agent frontmatter is intentionally unchanged; Codex
may ignore those hints and execute the skill inline.
