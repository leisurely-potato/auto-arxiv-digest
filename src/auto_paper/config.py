from __future__ import annotations

import tomllib
from pathlib import Path

from .models import AppConfig, Topic


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    with config_path.open("rb") as fh:
        raw = tomllib.load(fh)

    app = raw.get("app", {})
    arxiv = raw.get("arxiv", {})
    llm = raw.get("llm", {})
    zotero = raw.get("zotero", {})

    topics = [
        Topic(
            name=item["name"],
            query=item["query"],
            max_results=int(item.get("max_results", 20)),
            sort_by=item.get("sort_by", "submittedDate"),
            sort_order=item.get("sort_order", "descending"),
            tags=list(item.get("tags", [])),
            zotero_collection_id=item.get("zotero_collection_id"),
            zotero_tags=list(item.get("zotero_tags", [])),
            prompt_path=item.get("prompt_path"),
        )
        for item in raw.get("topics", [])
    ]
    if not topics:
        raise ValueError("config must define at least one [[topics]] entry")

    return AppConfig(
        database_path=app.get("database_path", "data/auto_paper.sqlite3"),
        report_dir=app.get("report_dir", "reports"),
        log_path=app.get("log_path", "logs/auto-paper.log"),
        topics=topics,
        arxiv_base_url=arxiv.get("base_url", "https://export.arxiv.org/api/query"),
        arxiv=arxiv,
        llm=llm,
        zotero=zotero,
    )
