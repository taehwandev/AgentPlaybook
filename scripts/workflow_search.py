"""Natural-language document search for workflow.py.

The query path is intentionally local and dependency-free. It is not a RAG
pipeline; it expands vague task requests into reusable workflow facets, then
ranks the same markdown corpus the route command uses and follows the local
document graph from matched seed docs.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Sequence

from workflow_doc_graph import expand_doc_matches
from workflow_search_facets import facet_docs, query_terms


RAW_TERM_WEIGHT = 2
EXPANDED_TERM_WEIGHT = 1
GRAPH_RELATION_BOOST = 12
GRAPH_SEED_LIMIT = 12


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
    """Return docs ranked by natural-language relevance to *query*."""
    raw_terms, expanded_terms, matched_facets, doc_boosts = query_terms(query)
    if not raw_terms and not expanded_terms and not doc_boosts:
        return []

    descriptions = _parse_index_descriptions(root)
    documents: dict[str, Dict[str, object]] = {}
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

        score = doc_boosts.get(rel, 0)
        score += _score_terms(raw_terms, RAW_TERM_WEIGHT, lower_desc, lower_title, lower_headings, lower_body)
        score += _score_terms(expanded_terms, EXPANDED_TERM_WEIGHT, lower_desc, lower_title, lower_headings, lower_body)

        documents[rel] = {
            "path": rel,
            "title": title,
            "description": index_desc,
            "score": score,
            "matched_facets": [facet for facet in matched_facets if rel in facet_docs(facet)],
        }
        if score > 0:
            results.append(documents[rel])

    _append_graph_expansions(root, documents, results, doc_boosts, max_results)
    results.sort(key=lambda x: (-int(x["score"]), str(x["path"])))
    return results[:max_results]


def _append_graph_expansions(
    root: Path,
    documents: dict[str, Dict[str, object]],
    results: List[Dict[str, object]],
    doc_boosts: dict[str, int],
    max_results: int,
) -> None:
    seed_candidates = list(doc_boosts) or [str(item["path"]) for item in results[:GRAPH_SEED_LIMIT]]
    seed_docs = _unique_strings(seed_candidates)
    if not seed_docs:
        return
    result_paths = {str(item["path"]) for item in results}
    graph_matches = expand_doc_matches(
        root,
        seed_docs,
        max_depth=1,
        max_docs=max(max_results * 2, GRAPH_SEED_LIMIT),
    )
    for match in graph_matches:
        path = str(match["path"])
        item = documents.get(path)
        if not item:
            continue
        depth = int(match.get("depth") or 1)
        item["score"] = int(item.get("score") or 0) + max(1, GRAPH_RELATION_BOOST - depth)
        reasons = item.setdefault("graph_reasons", [])
        if isinstance(reasons, list):
            reasons.append(f"{match['relation']} via {match['source']}")
        if path not in result_paths:
            results.append(item)
            result_paths.add(path)


def _unique_strings(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _score_terms(
    terms: Sequence[str],
    weight: int,
    lower_desc: str,
    lower_title: str,
    lower_headings: str,
    lower_body: str,
) -> int:
    score = 0
    for term in terms:
        if term in lower_desc:
            score += 4 * weight
        if term in lower_title:
            score += 3 * weight
        if term in lower_headings:
            score += 2 * weight
        if term in lower_body:
            score += weight
    return score


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
        facets = item.get("matched_facets")
        suffix = ""
        if isinstance(facets, list) and facets:
            suffix = f" (matched facets: {', '.join(str(facet) for facet in facets)})"
        graph_reasons = item.get("graph_reasons")
        if isinstance(graph_reasons, list) and graph_reasons:
            suffix += f" (graph: {', '.join(str(reason) for reason in graph_reasons[:2])})"
        print(f"- `{item['path']}` — {label}{suffix}")
    print()
    print("To get a structured route:")
    print(
        "  python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route <command>"
        ' --request "<request>"'
    )
