from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sqlite3

from .models import Paper, Topic


MIGRATION = Path(__file__).resolve().parents[2] / "migrations" / "001_init.sql"


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def init(self) -> None:
        self.conn.executescript(MIGRATION.read_text(encoding="utf-8"))
        self.conn.commit()

    def upsert_topics(self, topics: list[Topic]) -> None:
        for topic in topics:
            self.conn.execute(
                """
                INSERT INTO topics(name, query, tags_json, zotero_collection_id, zotero_tags_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    query=excluded.query,
                    tags_json=excluded.tags_json,
                    zotero_collection_id=excluded.zotero_collection_id,
                    zotero_tags_json=excluded.zotero_tags_json
                """,
                (
                    topic.name,
                    topic.query,
                    json.dumps(topic.tags, ensure_ascii=False),
                    topic.zotero_collection_id,
                    json.dumps(topic.zotero_tags, ensure_ascii=False),
                ),
            )
        self.conn.commit()

    def save_papers(self, papers: list[Paper]) -> list[Paper]:
        new_papers = []
        for paper in papers:
            existed = self.get_paper(paper.arxiv_id) is not None
            if existed:
                self._merge_paper_topics(paper)
            else:
                self._insert_paper(paper)
                new_papers.append(paper)
            for topic in paper.topics:
                self.conn.execute(
                    "INSERT OR IGNORE INTO paper_topics(arxiv_id, topic_name) VALUES (?, ?)",
                    (paper.arxiv_id, topic),
                )
        self.conn.commit()
        return new_papers

    def update_summary(self, paper: Paper) -> None:
        self.conn.execute(
            """
            UPDATE papers SET
                summary=?,
                contributions_json=?,
                keywords_json=?,
                audience=?,
                summary_error=?,
                prompt_path=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE arxiv_id=?
            """,
            (
                paper.summary,
                json.dumps(paper.contributions, ensure_ascii=False),
                json.dumps(paper.keywords, ensure_ascii=False),
                paper.audience,
                paper.summary_error,
                paper.prompt_path,
                paper.arxiv_id,
            ),
        )
        self.conn.commit()

    def update_zotero(self, paper: Paper) -> None:
        self.conn.execute(
            """
            UPDATE papers SET
                zotero_item_key=?,
                zotero_status=?,
                zotero_error=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE arxiv_id=?
            """,
            (paper.zotero_item_key, paper.zotero_status, paper.zotero_error, paper.arxiv_id),
        )
        self.conn.commit()

    def get_paper(self, arxiv_id: str) -> Paper | None:
        row = self.conn.execute("SELECT * FROM papers WHERE arxiv_id=?", (arxiv_id,)).fetchone()
        if row is None:
            return None
        return self._paper_from_row(row)

    def get_unsynced_zotero_papers(self) -> list[Paper]:
        rows = self.conn.execute(
            """
            SELECT * FROM papers
            WHERE zotero_item_key IS NULL
            ORDER BY published DESC
            """
        ).fetchall()
        papers = [self._paper_from_row(row) for row in rows]
        for paper in papers:
            self._hydrate_topic_metadata(paper)
        return papers

    def start_run(self, run_date: str) -> int:
        cursor = self.conn.execute(
            "INSERT INTO runs(run_date, status) VALUES (?, ?)",
            (run_date, "running"),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def finish_run(self, run_id: int, status: str, message: str = "") -> None:
        self.conn.execute(
            "UPDATE runs SET completed_at=CURRENT_TIMESTAMP, status=?, message=? WHERE id=?",
            (status, message, run_id),
        )
        self.conn.commit()

    def _insert_paper(self, paper: Paper) -> None:
        self.conn.execute(
            """
            INSERT INTO papers(
                arxiv_id, title, authors_json, abstract, published, updated,
                categories_json, primary_category, abs_url, pdf_url, doi,
                summary, contributions_json, keywords_json, audience,
                summary_error, prompt_path, zotero_item_key, zotero_status, zotero_error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper.arxiv_id,
                paper.title,
                json.dumps(paper.authors, ensure_ascii=False),
                paper.abstract,
                paper.published.isoformat(),
                paper.updated.isoformat() if paper.updated else None,
                json.dumps(paper.categories, ensure_ascii=False),
                paper.primary_category,
                paper.abs_url,
                paper.pdf_url,
                paper.doi,
                paper.summary,
                json.dumps(paper.contributions, ensure_ascii=False),
                json.dumps(paper.keywords, ensure_ascii=False),
                paper.audience,
                paper.summary_error,
                paper.prompt_path,
                paper.zotero_item_key,
                paper.zotero_status,
                paper.zotero_error,
            ),
        )

    def _merge_paper_topics(self, paper: Paper) -> None:
        stored = self.get_paper(paper.arxiv_id)
        if stored is None:
            return
        paper.summary = stored.summary
        paper.contributions = stored.contributions
        paper.keywords = stored.keywords
        paper.audience = stored.audience
        paper.prompt_path = stored.prompt_path
        paper.zotero_item_key = stored.zotero_item_key
        paper.zotero_status = stored.zotero_status
        paper.zotero_error = stored.zotero_error

    def _paper_from_row(self, row: sqlite3.Row) -> Paper:
        paper = Paper(
            arxiv_id=row["arxiv_id"],
            title=row["title"],
            authors=json.loads(row["authors_json"]),
            abstract=row["abstract"],
            published=datetime.fromisoformat(row["published"]),
            updated=datetime.fromisoformat(row["updated"]) if row["updated"] else None,
            categories=json.loads(row["categories_json"]),
            primary_category=row["primary_category"],
            abs_url=row["abs_url"],
            pdf_url=row["pdf_url"],
            doi=row["doi"],
            summary=row["summary"],
            contributions=json.loads(row["contributions_json"]),
            keywords=json.loads(row["keywords_json"]),
            audience=row["audience"],
            summary_error=row["summary_error"],
            prompt_path=row["prompt_path"],
            zotero_item_key=row["zotero_item_key"],
            zotero_status=row["zotero_status"],
            zotero_error=row["zotero_error"],
        )
        paper.topics = [
            item["topic_name"]
            for item in self.conn.execute(
                "SELECT topic_name FROM paper_topics WHERE arxiv_id=? ORDER BY topic_name",
                (paper.arxiv_id,),
            ).fetchall()
        ]
        return paper

    def _hydrate_topic_metadata(self, paper: Paper) -> None:
        rows = self.conn.execute(
            """
            SELECT t.tags_json, t.zotero_collection_id, t.zotero_tags_json
            FROM topics t
            JOIN paper_topics pt ON pt.topic_name = t.name
            WHERE pt.arxiv_id = ?
            """,
            (paper.arxiv_id,),
        ).fetchall()
        for row in rows:
            paper.topic_tags = _merge(paper.topic_tags, json.loads(row["tags_json"]))
            if row["zotero_collection_id"]:
                paper.zotero_collections = _merge(paper.zotero_collections, [row["zotero_collection_id"]])
            paper.zotero_tags = _merge(paper.zotero_tags, json.loads(row["zotero_tags_json"]))


def _merge(left: list[str], right: list[str]) -> list[str]:
    seen = set(left)
    out = list(left)
    for item in right:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out
