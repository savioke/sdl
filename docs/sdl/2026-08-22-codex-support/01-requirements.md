# 01 — Requirements

<!-- SR-1: Product security context. SR-2: Threat model inputs. -->

## Summary

Distribute the existing skills-only SDL plugin through Codex as well as Claude Code, with a Codex manifest and marketplace catalog, paired installer and release tooling, and both distributions pinned to the same immutable release tag.

## Scope

In scope: the `.codex-plugin` manifest, the external `.agents` marketplace
catalog, Codex CLI installation instructions, version 2.1.0 release metadata,
paired release validation, and the one-time bootstrap merge order.

Out of scope: changing any SDL skill workflow, adding MCP servers or hooks,
publishing to a public universal directory, Codex IDE-extension installation,
and requiring Codex to honor Claude-specific model, fork, or background hints.

## Assets touched <!-- SR-1 -->

- The skill, helper, and template files shipped in `plugins/sdl`.
- The immutable Git tag and the Claude and Codex marketplace pins.
- Maintainer GitHub credentials used by the existing release script.
- Developer-local Claude and Codex plugin configuration.

## Trust boundaries crossed <!-- SR-2 -->

- The marketplace catalog tells a Codex workstation which Git tree to install.
- The release script pushes tags and updates two host-facing catalogs.
- The release checker reads both remote catalogs as untrusted JSON.

## Data classification <!-- SR-1 -->

All repository and marketplace data is public. No credentials, PII, customer
data, or new secret material is stored or processed.

## External inputs introduced <!-- SR-2 -->

- The Codex catalog JSON fetched from the marketplace repository.
- Presence and exit status of the local `codex` executable during installation.

## Security requirements <!-- SR-3, SR-4 -->

- The Claude and Codex source manifests must declare the same semantic version.
- Both marketplace catalogs must resolve to the same immutable release tag.
- Release automation must validate both catalogs before mutating a tag and move
  both pins only after the new tag exists remotely.
- During bootstrap, the established Claude catalog must remain on the released
  v2.0.0 tree until v2.1.0 is actually released.
- The Codex manifest must pass the Codex plugin validator and expose only the
  repository's existing skills.
- A Codex installation failure must warn independently and must not prevent the
  installer from completing setup for another available host.

## Related prior cycles

- `2026-07-09-split-marketplace`
- `2026-08-03-release-process`
- `2026-08-06-use-sub-agent-for-dep-update`

## Carried-forward residual risks

- `baseline:B7`: distribution metadata and tags are privileged supply-chain
  controls and must remain synchronized across supported hosts.
