from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Topic:
    name: str
    query: str
    max_results: int = 20
    sort_by: str = "submittedDate"
    sort_order: str = "descending"
    tags: list[str] = field(default_factory=list)
    zotero_collection_id: str | None = None
    zotero_tags: list[str] = field(default_factory=list)
    prompt_path: str | None = None


@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published: datetime
    updated: datetime | None
    categories: list[str]
    primary_category: str | None
    abs_url: str
    pdf_url: str | None
    doi: str | None = None
    topics: list[str] = field(default_factory=list)
    topic_tags: list[str] = field(default_factory=list)
    zotero_collections: list[str] = field(default_factory=list)
    zotero_tags: list[str] = field(default_factory=list)
    summary: str | None = None
    contributions: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    audience: str | None = None
    summary_error: str | None = None
    prompt_path: str | None = None
    zotero_item_key: str | None = None
    zotero_status: str | None = None
    zotero_error: str | None = None


@dataclass(frozen=True)
class AppConfig:
    database_path: str
    report_dir: str
    log_path: str
    topics: list[Topic]
    arxiv_base_url: str
    llm: dict
    zotero: dict
