from __future__ import annotations

from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from .models import Paper, Topic

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


class ArxivClient:
    def __init__(self, base_url: str = "https://export.arxiv.org/api/query", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout

    def search(self, topic: Topic) -> list[Paper]:
        params = {
            "search_query": topic.query,
            "start": 0,
            "max_results": topic.max_results,
            "sortBy": topic.sort_by,
            "sortOrder": topic.sort_order,
        }
        url = f"{self.base_url}?{urlencode(params)}"
        with urlopen(url, timeout=self.timeout) as response:
            payload = response.read()
        papers = parse_arxiv_feed(payload)
        for paper in papers:
            attach_topic(paper, topic)
        return papers


def parse_arxiv_feed(payload: bytes | str) -> list[Paper]:
    root = ET.fromstring(payload)
    papers = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        paper = _parse_entry(entry)
        papers.append(paper)
    return papers


def attach_topic(paper: Paper, topic: Topic) -> None:
    if topic.name not in paper.topics:
        paper.topics.append(topic.name)
    paper.topic_tags = _merge(paper.topic_tags, topic.tags)
    if topic.zotero_collection_id:
        paper.zotero_collections = _merge(paper.zotero_collections, [topic.zotero_collection_id])
    paper.zotero_tags = _merge(paper.zotero_tags, topic.zotero_tags)


def _parse_entry(entry: ET.Element) -> Paper:
    title = _text(entry, f"{ATOM_NS}title")
    abstract = _text(entry, f"{ATOM_NS}summary")
    published = _parse_dt(_text(entry, f"{ATOM_NS}published"))
    updated_text = _text(entry, f"{ATOM_NS}updated")
    updated = _parse_dt(updated_text) if updated_text else None
    authors = [_text(author, f"{ATOM_NS}name") for author in entry.findall(f"{ATOM_NS}author")]
    categories = [
        category.attrib["term"]
        for category in entry.findall(f"{ATOM_NS}category")
        if "term" in category.attrib
    ]
    primary_el = entry.find(f"{ARXIV_NS}primary_category")
    primary = primary_el.attrib.get("term") if primary_el is not None else (categories[0] if categories else None)
    doi = _text(entry, f"{ARXIV_NS}doi") or None
    abs_url = ""
    pdf_url = None
    for link in entry.findall(f"{ATOM_NS}link"):
        rel = link.attrib.get("rel")
        href = link.attrib.get("href", "")
        title_attr = link.attrib.get("title")
        if rel == "alternate":
            abs_url = href
        if title_attr == "pdf" or href.endswith(".pdf"):
            pdf_url = href
    arxiv_id = _arxiv_id(_text(entry, f"{ATOM_NS}id"), abs_url)

    return Paper(
        arxiv_id=arxiv_id,
        title=_normalize(title),
        authors=[_normalize(author) for author in authors if author],
        abstract=_normalize(abstract),
        published=published,
        updated=updated,
        categories=categories,
        primary_category=primary,
        abs_url=abs_url or f"https://arxiv.org/abs/{arxiv_id}",
        pdf_url=pdf_url,
        doi=doi,
    )


def merge_duplicate_papers(papers: list[Paper]) -> list[Paper]:
    by_id: dict[str, Paper] = {}
    for paper in papers:
        existing = by_id.get(paper.arxiv_id)
        if existing is None:
            by_id[paper.arxiv_id] = paper
            continue
        existing.topics = _merge(existing.topics, paper.topics)
        existing.topic_tags = _merge(existing.topic_tags, paper.topic_tags)
        existing.zotero_collections = _merge(existing.zotero_collections, paper.zotero_collections)
        existing.zotero_tags = _merge(existing.zotero_tags, paper.zotero_tags)
    return list(by_id.values())


def _text(node: ET.Element, path: str) -> str:
    found = node.find(path)
    return found.text.strip() if found is not None and found.text else ""


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _normalize(value: str) -> str:
    return " ".join(value.split())


def _arxiv_id(entry_id: str, abs_url: str) -> str:
    source = abs_url or entry_id
    return source.rstrip("/").split("/")[-1]


def _merge(left: list[str], right: list[str]) -> list[str]:
    seen = set(left)
    out = list(left)
    for item in right:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out
