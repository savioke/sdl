# 03 — Implementation

## Summary of changes

Documentation- and printed-text-only change, no runtime logic. Updated the "To update later" footer in `scripts/install.sh` and the update instructions in `docs/developer-guide.md` and `Plan.md` to state that `git pull` makes Copilot current immediately (symlinked skills) but Claude Code additionally needs `/plugin marketplace update savioke` and a reload, because its plugin marketplace is a local clone that does not auto-refresh. Corrected `Plan.md`'s inaccurate "every tool sees the new version immediately" sentence.

## Mitigations implemented <!-- SI-1 -->

No threats recorded in `02-threat-model.md` (documentation/printed-text change). Nothing to mitigate; baseline:B3 disposition unchanged per the threat model.

## Secure coding practices applied <!-- SI-2 -->

- **Workstation scripts (baseline:B3):** The `scripts/install.sh` change is confined to heredoc-printed text — no new network fetch, no privileged operation, no executable logic. `shellcheck` is unaffected (the added lines are literal heredoc content, not parsed shell).
- **Secrets:** No secrets, keys, or tokens introduced.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None.

## Deviations from spec or threat model

None. Implementation matches `01`/`02`.
