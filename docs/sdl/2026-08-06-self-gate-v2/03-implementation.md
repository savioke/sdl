# 03 — Implementation

<!-- SI-1: Security implementation review. SI-2: Secure coding standards. -->

## Summary of changes

One functional line: `.github/workflows/sdl.yml` now calls
`savioke/sdl/.github/workflows/sdl-validate.yml@v2`, and its comment records why
the ref moves with each major and why it can only move after the tag exists,
rather than the temporary note explaining why it was stuck at `@v1`. The rest is
`docs/sdl/baseline.md`, where six statements described the `@v1` channel as
current: the distribution bullet, the "this repo → consumer CI" crossing point,
the self-gate standing requirement, and the text of B4, B5, and B6. Each now
names the moving major alias — `@v2` today — rather than a literal tag, except
B4, where the version was never the point at all (any repo can call the reusable
workflow at any ref, which is what it now says). Nothing consumers receive is touched: no validator, no reusable
workflow, no plugin version, no release.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Ref moved to the moving major alias consumers pin, and verified against the tree behind the tag (resolve step, `--push`, `cycle_in_diff` all present at `v2`) rather than against the tag name. The PR carrying the change is itself gated by `@v2`, so the adoption cannot merge if the gate it adopts cannot validate this repo. | `.github/workflows/sdl.yml:15` | this branch |

## Secure coding practices applied <!-- SI-2 -->

- **Verify the artifact, not the label.** A tag name is an assertion; the tree
  behind it is the fact. `v2` was read directly for the three markers that
  distinguish the 2.0.0 gate from the 1.x one before the ref was changed.
- **Pin to the channel you ship, not a better one.** An immutable `@v2.0.0`
  would be safer for this repo alone and would defeat the purpose — the point of
  the self-gate is that this repo takes the same alias-move risk (`baseline:B5`)
  it asks consumers to take, and so notices a bad release first.
- **Correct the record with the change.** The baseline is read by every later
  cycle instead of being re-derived; leaving it describing a retired channel
  would propagate the error into work that never looks at this diff.
- **Leave the audit trail alone.** Merged cycle folders and pre-2.0.0 changelog
  entries still say `@v1` because they were accurate when written. Only
  documents that assert a present state were edited.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None. No packages, no action pins, no plugin version bump — this cycle ships no
release, and `plugin.json` stays at 2.0.0. The one dependency that changes is
this repo's own CI dependency on the released gate, from `@v1` to `@v2`.

## Deviations from spec or threat model

None. One decision is worth recording rather than leaving implicit: `baseline.md`
was pulled into scope after the ref change, on the grounds that the baseline is a
description of the present and had six statements that stopped being true when
2.0.0 shipped. Rewording them to name "the moving major alias" instead of a
literal tag is a small generalization beyond a mechanical `v1`→`v2` swap, made so
the same statements do not need revisiting at every major.
