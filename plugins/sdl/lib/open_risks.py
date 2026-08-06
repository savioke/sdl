#!/usr/bin/env python3
"""List the residual risks still open across every SDL cycle.

`sdl-spec` has to know which earlier cycles left something unfinished before it
can ask whether the new cycle takes any of it on. That answer is already fully
recorded — it just isn't collected anywhere:

  * `04-verification.md` residual-risk tables hold the items, with a disposition
    of `accept`, `defer`, or `mitigate-later`.
  * `.sdl-meta.yml` `carry_forward:` records which items a later cycle claimed.

Open, then, is: disposition is `defer` or `mitigate-later`, and no cycle has
claimed it. `accept`ed risks are decisions, not debts, so they are not listed
unless --all is given.

Reading N cycle files to re-derive this on every new cycle is work that grows
with the repo and produces the same answer every time. Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

OPEN_DISPOSITIONS = {"defer", "mitigate-later"}
RISK_ID_RE = re.compile(r"^R\d+$")
# `carry_forward:` is either an inline [] / [a, b] or a block of "- item" lines.
CARRY_INLINE_RE = re.compile(r"^carry_forward:\s*\[(?P<items>.*)\]\s*$", re.MULTILINE)
CARRY_BLOCK_RE = re.compile(r"^carry_forward:\s*$(?P<body>(?:\n\s+-\s*\S+)*)", re.MULTILINE)
STATUS_RE = re.compile(r"^status:\s*(?P<status>\S+)\s*$", re.MULTILINE)


@dataclass
class Risk:
    cycle: str
    rid: str
    description: str
    severity: str
    disposition: str
    target: str
    status: str

    @property
    def ref(self) -> str:
        return f"{self.cycle}:{self.rid}"


def table_cells(line: str) -> list[str] | None:
    """Cells of a markdown table row, or None if the line is not one."""
    s = line.strip()
    if not s.startswith("|"):
        return None
    return [c.strip() for c in s.strip("|").split("|")]


def parse_risks(cycle_dir: Path, status: str) -> list[Risk]:
    """Residual-risk rows from one cycle's 04-verification.md.

    Anchored on the ID cell matching R<n> rather than on the surrounding
    heading, so an unrelated five-column table elsewhere in the file cannot be
    mistaken for the risk register. Rows with an empty description are template
    scaffolding, not risks.
    """
    path = cycle_dir / "04-verification.md"
    if not path.is_file():
        return []
    risks = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        cells = table_cells(line)
        if not cells or len(cells) < 5 or not RISK_ID_RE.match(cells[0]):
            continue
        if not cells[1]:
            continue
        risks.append(Risk(
            cycle=cycle_dir.name,
            rid=cells[0],
            description=cells[1],
            severity=cells[2],
            disposition=cells[3].lower(),
            target=cells[4],
            status=status,
        ))
    return risks


def parse_meta(cycle_dir: Path) -> tuple[str, set[str]]:
    """A cycle's status and the set of risk refs its carry_forward claims."""
    meta = cycle_dir / ".sdl-meta.yml"
    if not meta.is_file():
        return "unknown", set()
    text = meta.read_text(encoding="utf-8", errors="replace")
    m = STATUS_RE.search(text)
    status = m.group("status") if m else "unknown"

    claimed: set[str] = set()
    inline = CARRY_INLINE_RE.search(text)
    if inline:
        claimed = {i.strip() for i in inline.group("items").split(",") if i.strip()}
    else:
        block = CARRY_BLOCK_RE.search(text)
        if block:
            claimed = {ln.strip().lstrip("-").strip()
                       for ln in block.group("body").splitlines() if ln.strip()}
    return status, {c for c in claimed if c}


def collect(sdl_dir: Path) -> tuple[list[Risk], set[str]]:
    risks: list[Risk] = []
    claimed: set[str] = set()
    for cycle in sorted(p for p in sdl_dir.iterdir() if p.is_dir()):
        status, cycle_claimed = parse_meta(cycle)
        claimed |= cycle_claimed
        risks.extend(parse_risks(cycle, status))
    return risks, claimed


def truncate(s: str, width: int) -> str:
    return s if len(s) <= width else s[: width - 1].rstrip() + "…"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List residual risks still open across SDL cycles.")
    parser.add_argument("--repo", default=".", help="repo root")
    parser.add_argument("--all", action="store_true",
                        help="include accepted risks and ones already claimed")
    parser.add_argument("--full", action="store_true",
                        help="do not truncate descriptions")
    args = parser.parse_args()

    sdl_dir = Path(args.repo).resolve() / "docs" / "sdl"
    if not sdl_dir.is_dir():
        print(f"no {sdl_dir} — nothing to report", file=sys.stderr)
        return 1

    risks, claimed = collect(sdl_dir)
    if not args.all:
        risks = [r for r in risks
                 if r.disposition in OPEN_DISPOSITIONS and r.ref not in claimed]

    if not risks:
        print("no open residual risks")
        return 0

    width = 10_000 if args.full else 96
    label = "residual risk(s)" if args.all else "open residual risk(s)"
    print(f"{len(risks)} {label}:\n")
    for r in risks:
        flag = "  [claimed]" if r.ref in claimed else ""
        print(f"  {r.ref}  ({r.severity}, {r.disposition}, cycle {r.status}){flag}")
        print(f"      {truncate(r.description, width)}")
        if r.target and r.target not in ("—", "-", "none"):
            print(f"      → {truncate(r.target, width)}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
