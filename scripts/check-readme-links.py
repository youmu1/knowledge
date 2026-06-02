#!/usr/bin/env python3
"""Verify README.md links every content .md and targets exist."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

SKIP_PARTS = {".obsidian", ".github", ".git", "scripts"}


def collect_md_files(root: Path) -> list[str]:
    out: list[str] = []
    for p in root.rglob("*.md"):
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        out.append(p.relative_to(root).as_posix())
    return sorted(out)


def extract_readme_links(readme_text: str) -> set[str]:
    links: set[str] = set()
    for m in re.finditer(r"\]\(([^)]+)\)", readme_text):
        raw = m.group(1).split("#")[0].strip()
        if raw.startswith("http://") or raw.startswith("https://"):
            continue
        if raw.startswith("../"):
            continue
        if raw.startswith("./"):
            raw = raw[2:]
        links.add(unquote(raw))
    return links


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    readme_path = root / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")
    links = extract_readme_links(readme_text)
    all_md = collect_md_files(root)

    broken = [p for p in sorted(links) if not (root / p).exists()]
    missing = [f for f in all_md if f != "README.md" and f not in links]

    if broken:
        print("Broken links in README.md:")
        for p in broken:
            print(f"  - {p}")
    if missing:
        print("Markdown files not linked from README.md:")
        for p in missing:
            print(f"  - {p}")

    if broken or missing:
        print(
            f"\nSummary: {len(broken)} broken, {len(missing)} unlinked "
            f"(of {len(all_md)} md files, {len(links)} links in README)"
        )
        return 1

    print(
        f"OK: README.md links all {len(all_md) - 1} content files "
        f"({len(links)} links, targets exist)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
