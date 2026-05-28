from datetime import datetime, timezone

from auto_paper.db import Database
from auto_paper.models import Paper, Topic


def make_paper(arxiv_id="2401.1"):
    return Paper(
        arxiv_id=arxiv_id,
        title="Paper",
        authors=["Alice"],
        abstract="Abstract",
        published=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated=None,
        categories=["cs.AI"],
        primary_category="cs.AI",
        abs_url=f"https://arxiv.org/abs/{arxiv_id}",
        pdf_url=None,
        topics=["Agents"],
        topic_tags=["agent"],
        zotero_collections=["col-1"],
    )


def test_save_papers_deduplicates(tmp_path):
    db = Database(tmp_path / "papers.sqlite3")
    db.init()
    db.upsert_topics([Topic(name="Agents", query="x", tags=["agent"], zotero_collection_id="col-1")])
    first = db.save_papers([make_paper()])
    second = db.save_papers([make_paper()])
    assert len(first) == 1
    assert second == []
    assert db.get_paper("2401.1").topics == ["Agents"]
    db.close()


def test_unsynced_papers_hydrate_zotero_metadata(tmp_path):
    db = Database(tmp_path / "papers.sqlite3")
    db.init()
    db.upsert_topics([Topic(name="Agents", query="x", tags=["agent"], zotero_collection_id="col-1")])
    db.save_papers([make_paper()])
    papers = db.get_unsynced_zotero_papers()
    assert papers[0].zotero_collections == ["col-1"]
    assert papers[0].topic_tags == ["agent"]
    db.close()
