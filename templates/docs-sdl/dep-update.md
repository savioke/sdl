# Dependency update record

<!-- Routine-tier supply-chain update evidence (docs/dependency-updates.md).
     Requires `class: dependency-update` in .sdl-meta.yml. validate.py parses
     the table below — keep its shape. Major bumps fail validation: escalate
     to a full cycle instead. -->

## Updates

<!-- One row per dependency. Versions like 1.2.3 or v1.2.3.
     source: dependabot | renovate | scanner | human -->

| package | from | to | source |
|---------|------|----|--------|
|         |      |    |        |

## Checks

<!-- CI re-verifies what it can (pin↔tag via check_pins, ecosystem integrity
     hashes). The rest is attestation by the author — checking a box you did
     not do falsifies the audit trail. -->

- [ ] Pins/hashes verified against upstream (check_pins or ecosystem integrity mode)
- [ ] Advisory lookup for the new versions (OSV / GitHub Advisory DB)
- [ ] Release notes reviewed against documented promises (baseline, threat models)
- [ ] No escalation trigger applies (docs/dependency-updates.md triage table)

## Notes

<!-- Anything surprising: why the bump exists (advisory?), behavior changes
     considered, links. One or two sentences is normal. -->
