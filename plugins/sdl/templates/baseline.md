# SDL Baseline

<!-- Repo-level security baseline. Authored ONCE when the repo adopts SDL (run the
     sdl-baseline skill), updated rarely — only when the standing architecture,
     exposure model, or standing risk register actually changes. Per-feature cycles
     under docs/sdl/<date-slug>/ reference this file instead of re-deriving it. -->

## System overview

<!-- What this service/repo is, and its major components. A few bullets. -->

## Deployment and exposure model

<!-- How and where this runs, and who can reach it. This is the single most
     load-bearing fact for every threat model: "single operator on a trusted
     workstation", "public internet behind authn", "internal VPC only", etc.
     State it once here so cycles don't re-explain it each time. -->

## Trust boundaries and standing data flows

<!-- The boundaries that exist in the codebase today: where untrusted input enters,
     where privileged operations execute, where data crosses an authz line.
     One bullet per boundary. Cycles add only the NEW boundary they introduce. -->

## Assets and data classification

<!-- Standing assets: credentials, data stores, PII, customer data, infra metadata.
     Their classification. Cycles reference these; they list only what they add. -->

## Standing security requirements

<!-- Repo-wide controls that every change inherits: authn posture, input-validation
     conventions, secret-handling rules, logging policy. -->

## Standing risk register

<!-- The pre-existing security posture: known issues, accepted risks, and deferred
     work that exists independent of any one feature cycle. Each gets a stable ID
     (B1, B2, …) so cycles can reference "inherits baseline:B2" in one line instead
     of rediscovering and re-dispositioning it every time. Move an item here once it
     is established as a standing condition rather than a single cycle's finding. -->

| ID  | Description | Severity | Disposition | Owner / trigger to revisit |
|-----|-------------|----------|-------------|----------------------------|
| B1  |             |          | accept \| defer \| mitigate-later |  |

## Maintenance

<!-- Update this file when the exposure model changes, a standing risk is closed or
     added, or a major component is introduced/removed. It is not per-cycle; most
     PRs leave it untouched. The sdl-review skill will suggest an update when a
     cycle's residual risk looks like a standing condition rather than a one-off. -->
