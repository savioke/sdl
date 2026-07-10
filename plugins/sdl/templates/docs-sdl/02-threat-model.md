# 02 — Threat Model

<!-- SR-2: Threat model. SD-1, SD-2: Secure design and defense in depth. -->

## Components and data flows

<!-- Brief inventory of the components and flows introduced or modified.
     One bullet per component is fine for small features. -->

## Threats <!-- SR-2 -->

<!-- STRIDE-lite. One subsection per threat with a stable ID (T1, T2, …)
     so 03-implementation.md and 04-verification.md can reference it.
     Proportionality: only threats presently reachable in the code as written
     get a stanza. Most changes have zero to two. Speculative, not-reachable-today,
     or owned-elsewhere concerns go as one-liners in the two sections below, not here. -->

### T1 — <short name>

- **Category:** <Spoofing | Tampering | Repudiation | Information disclosure | Denial of service | Elevation of privilege>
- **Component / flow:**
- **Description:**
- **Likelihood / Impact:** <low | medium | high> / <low | medium | high>
- **Mitigation:** <design choice or control that addresses this threat>
- **Mitigation type:** <preventive | detective | corrective>
- **Defense in depth notes:** <SD-2: any complementary controls>

## Threats inherited from prior cycles <!-- SR-2 -->

<!-- Reference threats from related_cycles in .sdl-meta.yml that still apply.
     Do not re-litigate; link and confirm scope. -->

## Out-of-scope threats

<!-- One line each. Concerns owned elsewhere (IAM scope, platform default, an
     upstream layer covered by baseline.md or a prior cycle) or explicitly
     deferred/accepted, with rationale and owner. No stanzas here. -->

## Noted for future cycles

<!-- One line each. Concerns not reachable with the code as written but worth a
     signpost for the next maintainer if the code grows a certain way. No stanzas. -->
