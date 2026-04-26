# -*- coding: utf-8 -*-
"""
Unified query entry for:
1. wiki entities / sources / chain relations
2. Xiaozuowen KB as an attached external knowledge source

Usage:
    python wiki_query.py "Huawei"
    python wiki_query.py "中际旭创"
    python wiki_query.py "NVL72"
"""

import sqlite3
import sys
from pathlib import Path

from wiki_entity_registry import expand_query_terms, normalize_entity_name

sys.stdout.reconfigure(encoding="utf-8")

WIKI_ROOT = Path("D:/claude/wiki")
KB_SQLITE = Path("D:/codex/references/merged_stock_kb.sqlite3")


def build_query_terms(query: str) -> list[str]:
    return [term.lower() for term in expand_query_terms(query) if term]


def contains_any(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def unique_preserve(items: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for item in items:
        value = item.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def search_entities(query: str) -> list[dict]:
    results = []
    entities_dir = WIKI_ROOT / "entities"
    if not entities_dir.exists():
        return results

    terms = build_query_terms(query)
    for entity_dir in entities_dir.iterdir():
        if not entity_dir.is_dir():
            continue
        for md_file in entity_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            if not contains_any(content, terms):
                continue
            matched = [line.strip() for line in content.splitlines() if contains_any(line, terms)][:5]
            results.append({
                "type": "entity",
                "name": entity_dir.name,
                "file": str(md_file.relative_to(WIKI_ROOT)),
                "matched": matched,
            })
    return results


def search_sources(query: str) -> list[dict]:
    results = []
    sources_dir = WIKI_ROOT / "sources"
    if not sources_dir.exists():
        return results

    terms = build_query_terms(query)
    for md_file in sources_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8", errors="ignore")
        if not contains_any(content, terms):
            continue

        title = ""
        tldr = ""
        matched = []
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if line.startswith("title:"):
                title = line.replace("title:", "", 1).strip()
            if line.strip().lower() == "## tl;dr" and idx + 1 < len(lines):
                tldr = lines[idx + 1].strip()
            if contains_any(line, terms):
                matched.append(line.strip())

        results.append({
            "type": "source",
            "title": title or md_file.stem,
            "file": str(md_file.relative_to(WIKI_ROOT)),
            "matched": matched[:3],
            "tldr": tldr,
        })
    return results


def search_chain_relations(query: str) -> list[dict]:
    results = []
    sources_dir = WIKI_ROOT / "sources"
    if not sources_dir.exists():
        return results

    terms = build_query_terms(query)
    for md_file in sources_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8", errors="ignore")
        in_chain = False
        for line in content.splitlines():
            lowered = line.lower()
            if "chain relations" in lowered:
                in_chain = True
                continue
            if in_chain and line.startswith("##"):
                in_chain = False
            if in_chain and contains_any(line, terms):
                results.append({
                    "type": "chain_relation",
                    "file": str(md_file.relative_to(WIKI_ROOT)),
                    "matched": line.strip(),
                })
    return results


def kb_conn() -> sqlite3.Connection | None:
    if not KB_SQLITE.exists():
        return None
    conn = sqlite3.connect(KB_SQLITE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA case_sensitive_like = ON")
    return conn


def query_kb_stock(query: str, *, limit: int = 3) -> dict | None:
    conn = kb_conn()
    if conn is None:
        return None

    q = query.strip()
    matches = conn.execute(
        "SELECT DISTINCT stock, stock_code FROM post_stock "
        "WHERE stock = ? OR stock_code LIKE ? LIMIT 5",
        (q, f"%{q}%"),
    ).fetchall()
    if not matches:
        matches = conn.execute(
            "SELECT DISTINCT stock, stock_code FROM post_stock "
            "WHERE stock LIKE ? LIMIT 5",
            (f"%{q}%",),
        ).fetchall()
    if not matches:
        conn.close()
        return None

    stock_name = matches[0]["stock"]
    stock_codes = matches[0]["stock_code"].split(",") if matches[0]["stock_code"] else []
    posts = [
        dict(row)
        for row in conn.execute(
            "SELECT p.post_id, p.date, p.content "
            "FROM posts p JOIN post_stock ps ON ps.post_id = p.post_id "
            "WHERE ps.stock = ? ORDER BY p.date DESC LIMIT ?",
            (stock_name, int(limit)),
        ).fetchall()
    ]
    total_posts = conn.execute(
        "SELECT COUNT(*) FROM post_stock WHERE stock = ?",
        (stock_name,),
    ).fetchone()[0]
    conn.close()

    return {
        "name": stock_name,
        "codes": stock_codes,
        "total_posts": int(total_posts),
        "matched_posts": len(posts),
        "posts": posts,
        "source": "sqlite",
    }


def search_kb_posts(query: str, *, top: int = 5, limit: int = 15, match_mode: str = "phrase") -> dict:
    conn = kb_conn()
    if conn is None:
        return {
            "query": query,
            "match_mode": match_mode,
            "terms": [],
            "total_hits": 0,
            "stocks": [],
        }

    terms = [term for term in query.strip().split() if term]
    if not query.strip():
        conn.close()
        return {
            "query": query,
            "match_mode": match_mode,
            "terms": terms,
            "total_hits": 0,
            "stocks": [],
        }

    if match_mode == "and" and terms:
        where = " AND ".join(["p.content LIKE ? COLLATE BINARY"] * len(terms))
        params = [f"%{term}%" for term in terms]
    elif match_mode == "or" and terms:
        where = " OR ".join(["p.content LIKE ? COLLATE BINARY"] * len(terms))
        params = [f"%{term}%" for term in terms]
        where = f"({where})"
    else:
        where = "p.content LIKE ? COLLATE BINARY"
        params = [f"%{query}%"]
        match_mode = "phrase"

    sql = (
        "SELECT ps.stock, p.post_id, p.date, p.content "
        "FROM posts p JOIN post_stock ps ON ps.post_id = p.post_id "
        f"WHERE {where} ORDER BY p.date DESC LIMIT {int(limit)}"
    )
    hits_by_stock: dict[str, list[dict]] = {}
    total = 0
    for row in conn.execute(sql, params):
        hits_by_stock.setdefault(row["stock"], []).append(dict(row))
        total += 1
    conn.close()

    ranked = sorted(hits_by_stock.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:top]
    return {
        "query": query,
        "match_mode": match_mode,
        "terms": terms,
        "total_hits": total,
        "stocks": [{"name": name, "hits": len(posts), "posts": posts} for name, posts in ranked],
    }


def choose_kb_match_mode(query: str) -> str:
    return "and" if " " in query.strip() else "phrase"


def search_xiaozuowen(query: str, entity_results: list[dict]) -> tuple[list[dict], list[dict]]:
    canonical = normalize_entity_name(query)
    candidates = [query]
    if canonical != query:
        candidates.append(canonical)
    candidates.extend(result["name"] for result in entity_results[:5])
    candidates = unique_preserve(candidates)

    stock_results = []
    seen_stocks = set()
    for candidate in candidates:
        result = query_kb_stock(candidate, limit=3)
        if not result:
            continue
        if result["name"] in seen_stocks:
            continue
        seen_stocks.add(result["name"])
        stock_results.append(result)

    search_results = []
    for candidate in unique_preserve([query, canonical]):
        result = search_kb_posts(
            candidate,
            top=5,
            limit=15,
            match_mode=choose_kb_match_mode(candidate),
        )
        if result["total_hits"] > 0:
            search_results.append(result)
            break

    return stock_results, search_results


def preview(text: str, max_len: int = 160) -> str:
    compact = " ".join(text.strip().split())
    return compact[:max_len]


def format_answer(
    query: str,
    entity_results: list[dict],
    source_results: list[dict],
    chain_results: list[dict],
    kb_stock_results: list[dict],
    kb_search_results: list[dict],
) -> None:
    canonical = normalize_entity_name(query)
    kb_stock_count = len(kb_stock_results)
    kb_hit_count = sum(result["matched_posts"] for result in kb_stock_results)
    kb_hit_count += sum(result["total_hits"] for result in kb_search_results)

    print(f"\n{'=' * 60}")
    print(f"Query: {query}")
    if canonical != query:
        print(f"Canonical: {canonical}")
    print(f"{'=' * 60}")

    print(
        f"\nResults: {len(entity_results)} entity hits | "
        f"{len(source_results)} source hits | "
        f"{len(chain_results)} chain hits | "
        f"{kb_stock_count} KB stocks / {kb_hit_count} KB hits"
    )

    if entity_results:
        print("\n## Entities")
        for item in entity_results[:10]:
            print(f"\n### [[{item['name']}]]")
            for line in item["matched"][:3]:
                print(f"  > {line}")

    if source_results:
        print("\n## Sources")
        for item in source_results[:10]:
            print(f"\n### {item['title']} (source: {item['file']})")
            if item["tldr"]:
                print(f"  TL;DR: {item['tldr']}")
            for line in item["matched"][:3]:
                print(f"  > {line}")

    if chain_results:
        print("\n## Chain Relations")
        for item in chain_results[:10]:
            print(f"  {item['matched']}")

    if kb_stock_results or kb_search_results:
        print("\n## Xiaozuowen KB")
        for item in kb_stock_results[:5]:
            print(
                f"\n### {item['name']} "
                f"({item['matched_posts']}/{item['total_posts']} posts, source={item['source']})"
            )
            for post in item["posts"][:3]:
                print(f"  [{post.get('date', '')}] {preview(post.get('content', ''))}")

        for result in kb_search_results[:1]:
            print(
                f"\n### Keyword hits: {result['query']} "
                f"({result['total_hits']} posts, match_mode={result['match_mode']})"
            )
            for stock in result["stocks"][:5]:
                first_post = stock["posts"][0] if stock["posts"] else {}
                print(
                    f"  {stock['name']} ({stock['hits']} posts) "
                    f"{preview(first_post.get('content', ''))}"
                )

    print(f"\n{'=' * 60}")
    print("Sources above come from wiki/ plus the attached Xiaozuowen KB.")

    if not any([entity_results, source_results, chain_results, kb_stock_results, kb_search_results]):
        print("\nNo relevant results found in wiki or Xiaozuowen KB.")


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "光模块"
    print(f"[Wiki Query] search: {query}")

    entity_results = search_entities(query)
    source_results = search_sources(query)
    chain_results = search_chain_relations(query)
    kb_stock_results, kb_search_results = search_xiaozuowen(query, entity_results)

    format_answer(
        query,
        entity_results,
        source_results,
        chain_results,
        kb_stock_results,
        kb_search_results,
    )


if __name__ == "__main__":
    main()
