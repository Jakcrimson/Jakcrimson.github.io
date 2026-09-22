#!/usr/bin/env python3
"""Validate every post against the site's controlled vocabulary.

The point of _data/taxonomy.yml is that tags stay a closed set. This keeps them
that way: a typo or an ad-hoc tag fails the build instead of quietly creating a
one-post topic page.

Run from the repository root:

    python3 tools/check_taxonomy.py
"""
from __future__ import annotations

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "_posts")


def load_yaml(path: str):
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    with io.open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def scalar_list(front: str, key: str) -> list[str]:
    """Read `key: [a, b]` from a front-matter block."""
    m = re.search(rf"^{key}:\s*\[(.*?)\]\s*$", front, re.M)
    if not m:
        return []
    return [v.strip().strip('"').strip("'") for v in m.group(1).split(",") if v.strip()]


def scalar(front: str, key: str) -> str | None:
    m = re.search(rf"^{key}:[ \t]*(.*)$", front, re.M)
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'") or None


def main() -> int:
    taxonomy = load_yaml(os.path.join(ROOT, "_data", "taxonomy.yml"))
    institutions = load_yaml(os.path.join(ROOT, "_data", "institutions.yml"))
    if taxonomy is None or institutions is None:
        print("PyYAML is not installed — skipping taxonomy check.")
        return 0

    topics = {t["id"] for t in taxonomy["topics"]}
    kinds = {k["id"] for k in taxonomy["kinds"]}
    orgs = {i["id"] for i in institutions}

    problems: list[str] = []
    used_topics: set[str] = set()

    names = sorted(n for n in os.listdir(POSTS) if n.endswith(".md"))
    for name in names:
        with io.open(os.path.join(POSTS, name), encoding="utf-8") as fh:
            text = fh.read()
        m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
        if not m:
            problems.append(f"{name}: no front matter")
            continue
        front = m.group(1)

        kind = scalar(front, "kind")
        if kind is None:
            problems.append(f"{name}: missing `kind`")
        elif kind not in kinds:
            problems.append(f"{name}: unknown kind {kind!r} (allowed: {', '.join(sorted(kinds))})")

        affiliation = scalar(front, "affiliation")
        if affiliation is None:
            problems.append(f"{name}: missing `affiliation`")
        elif affiliation not in orgs:
            problems.append(f"{name}: unknown affiliation {affiliation!r}")

        tags = scalar_list(front, "tags")
        if not tags:
            problems.append(f"{name}: no tags")
        for t in tags:
            if t not in topics:
                problems.append(f"{name}: tag {t!r} is not in the taxonomy")
            else:
                used_topics.add(t)

        if not scalar(front, "description"):
            problems.append(f"{name}: missing `description` (used in listings and search results)")

    orphans = sorted(topics - used_topics)

    print(f"checked {len(names)} posts against {len(topics)} topics")
    if orphans:
        # Not an error: a declared topic with no posts simply gets no page.
        print(f"note: {len(orphans)} declared topic(s) unused — {', '.join(orphans)}")

    if problems:
        print(f"\n{len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    print("taxonomy OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
