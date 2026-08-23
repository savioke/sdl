# 02 — Threat Model

<!-- SR-2: Threat model. SD-1, SD-2: Secure design and defense in depth. -->

## Components and data flows

- Codex plugin manifest: declares the existing skills and Codex UI metadata.
- Claude and Codex catalogs: independently route hosts to a shared Git tag.
- Installer: invokes the Codex CLI when it is available on the workstation.
- Release and release-check tools: validate and advance both catalogs together.

## Threats <!-- SR-2 -->

<!-- STRIDE-lite. One subsection per threat with a stable ID (T1, T2, …)
     so 03-implementation.md and 04-verification.md can reference it.
     Proportionality: only threats presently reachable in the code as written
     get a stanza. Most changes have zero to two. Speculative, not-reachable-today,
     or owned-elsewhere concerns go as one-liners in the two sections below, not here. -->

### T1 — Host catalog drift

- **Category:** Tampering
- **Component / flow:** release tooling to the Claude and Codex catalogs
- **Description:** Divergent catalog pins can make the same plugin identity
  install different trees on different hosts, including delivering a security
  fix to only one host or deliberately targeting one host with altered content.
- **Likelihood / Impact:** medium / medium
- **Mitigation:** Require matching source-manifest versions, validate and update
  both catalogs in one release operation, and pin both to an exact Git tag.
- **Mitigation type:** preventive
- **Defense in depth notes:** The daily release check reads both catalogs and
  detects a missing, malformed, or unexpected pin.

### T2 — Bootstrap creates an unavailable release

- **Category:** Denial of service
- **Component / flow:** initial Codex catalog and first paired release
- **Description:** The paired release script requires both catalogs to exist,
  while moving the established Claude entry to v2.1.0 before that tag exists
  would break current installations.
- **Likelihood / Impact:** medium / medium
- **Mitigation:** Merge the marketplace catalog first while both entries remain
  pinned to released v2.0.0, then create and push v2.1.0 before advancing either
  public pin.
- **Mitigation type:** preventive
- **Defense in depth notes:** During the brief bootstrap gap only the new Codex
  route is unavailable because v2.0.0 predates its manifest; Claude remains on
  its known-good release.

## Threats inherited from prior cycles <!-- SR-2 -->

- `2026-08-03-release-process` T1 (malformed remote manifest): the same bounds
  and type validation now applies to both remote catalogs.
- `2026-08-03-release-process` T3 and `baseline:B7` (privileged distribution):
  tag and catalog write authority remains unchanged.
- `baseline:B2` (skill integrity): both hosts resolve the same reviewed tree.

## Out-of-scope threats

- Codex sandboxing, approval policy, caching, and host authentication are owned
  by Codex and workstation administrators.
- Claude-specific `model`, `context`, and `background` skill hints may be ignored
  by Codex and run inline; this affects latency/cost, not SDL evidence integrity.
- Codex IDE-extension plugin installation is not currently supported by Codex.

## Noted for future cycles

- Adopt a stable Codex sub-agent model hint if one becomes available, but never
  make audit evidence depend on asynchronous or model-specific execution.
- Revisit T1 if hosts gain separate release cadences or product-specific gating.
