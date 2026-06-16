"""Keyword-based document search for workflow.py."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List


def _parse_index_descriptions(root: Path) -> Dict[str, str]:
    """Return path → one-line description extracted from index.md."""
    index_path = root / "index.md"
    if not index_path.exists():
        return {}
    lines = index_path.read_text(encoding="utf-8", errors="ignore").split("\n")

    # Join indented continuation lines onto the preceding bullet line.
    joined: List[str] = []
    for line in lines:
        if joined and not line.startswith("-") and line.startswith("  ") and line.strip():
            joined[-1] = joined[-1].rstrip() + " " + line.strip()
        else:
            joined.append(line)

    path_re = re.compile(r"`([^`]+\.md)`")
    descriptions: Dict[str, str] = {}
    for line in joined:
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        paths = path_re.findall(stripped)
        if not paths:
            continue
        # Description = bullet content with all backtick-quoted items removed.
        desc = path_re.sub("", stripped.lstrip("-").strip()).strip().rstrip(":,").strip()
        for p in paths:
            descriptions.setdefault(p, desc)
    return descriptions


def search_docs(root: Path, query: str, max_results: int = 8) -> List[Dict[str, object]]:
    """Return docs ranked by keyword relevance to *query*."""
    terms = [t.lower() for t in re.split(r"\s+", query.strip()) if t]
    if not terms:
        return []

    descriptions = _parse_index_descriptions(root)
    results: List[Dict[str, object]] = []

    for path in sorted(root.rglob("*.md")):
        rel = str(path.relative_to(root))
        if rel.startswith("scripts/"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        title = ""
        headings: List[str] = []
        body_lines: List[str] = []
        in_frontmatter = False

        for i, line in enumerate(text.split("\n")):
            if i == 0 and line.strip() == "---":
                in_frontmatter = True
                continue
            if in_frontmatter:
                if line.strip() == "---":
                    in_frontmatter = False
                continue
            if line.startswith("# ") and not title:
                title = line[2:].strip()
            elif line.startswith("## ") or line.startswith("### "):
                headings.append(line.lstrip("#").strip())
            else:
                body_lines.append(line)

        index_desc = descriptions.get(rel, "")
        lower_desc = index_desc.lower()
        lower_title = title.lower()
        lower_headings = " ".join(headings).lower()
        lower_body = " ".join(body_lines)[:2000].lower()

        score = 0
        for term in terms:
            if term in lower_desc:
                score += 4
            if term in lower_title:
                score += 3
            if term in lower_headings:
                score += 2
            if term in lower_body:
                score += 1

        if score > 0:
            results.append({
                "path": rel,
                "title": title,
                "description": index_desc,
                "score": score,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def print_query_results(query: str, results: List[Dict[str, object]]) -> None:
    print(f'# AgentPlaybook Document Query: "{query}"')
    print()
    if not results:
        print("No matching documents found.")
        print()
        print("Try broader terms or run `workflow.py list` to browse available concerns.")
        return
    print(f"Top {len(results)} result(s):")
    print()
    for item in results:
        label = item.get("description") or item.get("title") or item["path"]
        print(f"- `{item['path']}` — {label}")
    print()
    print("To get a structured route:")
    print(
        "  python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route <command>"
        ' --request "<request>"'
    )
