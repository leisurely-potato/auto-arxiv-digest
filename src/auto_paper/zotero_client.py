from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import Paper


class ZoteroClient:
    def __init__(self, config: dict):
        self.enabled = bool(config.get("enabled", False))
        self.api_key_env = config.get("api_key_env", "ZOTERO_API_KEY")
        self.library_type = config.get("library_type", "user")
        self.library_id = str(config.get("library_id", ""))
        self.base_url = config.get("base_url", "https://api.zotero.org")
        self.timeout = int(config.get("timeout", 60))

    def create_item(self, paper: Paper) -> str:
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"missing API key env var: {self.api_key_env}")
        if not paper.zotero_collections:
            raise RuntimeError(f"paper {paper.arxiv_id} has no Zotero collection mapping")

        url = f"{self.base_url}/{self.library_type}s/{self.library_id}/items"
        payload = [paper_to_zotero_item(paper)]
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Zotero-API-Key": api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError) as exc:
            raise RuntimeError(f"Zotero request failed: {exc}") from exc
        success = data.get("successful", {})
        first = success.get("0") or next(iter(success.values()), None)
        if not first or "key" not in first:
            raise RuntimeError(f"Zotero response did not include item key: {data}")
        return first["key"]


def paper_to_zotero_item(paper: Paper) -> dict:
    tags = _tags(paper)
    creators = [
        {"creatorType": "author", "name": author}
        for author in paper.authors
    ]
    return {
        "itemType": "journalArticle",
        "title": paper.title,
        "creators": creators,
        "abstractNote": paper.summary or paper.abstract,
        "date": paper.published.date().isoformat(),
        "url": paper.abs_url,
        "DOI": paper.doi or "",
        "archive": "arXiv",
        "archiveID": paper.arxiv_id,
        "collections": paper.zotero_collections,
        "tags": [{"tag": tag} for tag in tags],
        "extra": _extra(paper),
    }


def sync_papers(client: ZoteroClient, papers: list[Paper]) -> list[Paper]:
    if not client.enabled:
        return papers
    for paper in papers:
        if paper.zotero_item_key:
            continue
        try:
            paper.zotero_item_key = client.create_item(paper)
            paper.zotero_status = "synced"
            paper.zotero_error = None
        except Exception as exc:
            paper.zotero_status = "failed"
            paper.zotero_error = str(exc)
    return papers


def _tags(paper: Paper) -> list[str]:
    candidates = []
    candidates.extend(paper.topic_tags)
    candidates.extend(paper.zotero_tags)
    if paper.primary_category:
        candidates.append(paper.primary_category)
    candidates.extend(paper.categories)
    candidates.extend(paper.keywords)
    seen = set()
    out = []
    for item in candidates:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _extra(paper: Paper) -> str:
    lines = [f"arXiv: {paper.arxiv_id}"]
    if paper.pdf_url:
        lines.append(f"PDF: {paper.pdf_url}")
    if paper.audience:
        lines.append(f"Audience: {paper.audience}")
    if paper.contributions:
        lines.append("Contributions:")
        lines.extend([f"- {item}" for item in paper.contributions])
    return "\n".join(lines)
