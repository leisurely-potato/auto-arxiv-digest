from datetime import datetime, timezone

from auto_paper.models import Paper
from auto_paper.zotero_client import paper_to_zotero_item, sync_papers


def make_paper():
    return Paper(
        arxiv_id="2401.1",
        title="Paper",
        authors=["Alice"],
        abstract="Abstract",
        published=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated=None,
        categories=["cs.AI", "cs.CL"],
        primary_category="cs.AI",
        abs_url="https://arxiv.org/abs/2401.1",
        pdf_url="https://arxiv.org/pdf/2401.1",
        topics=["Agents", "RAG"],
        topic_tags=["agent"],
        zotero_collections=["col-1", "col-2"],
        zotero_tags=["LLM"],
        keywords=["规划"],
    )


def test_zotero_payload_has_collections_and_tags():
    item = paper_to_zotero_item(make_paper())
    assert item["collections"] == ["col-1", "col-2"]
    tags = {tag["tag"] for tag in item["tags"]}
    assert {"agent", "LLM", "cs.AI", "cs.CL", "规划"}.issubset(tags)


def test_sync_skips_existing_item():
    class Client:
        enabled = True

        def create_item(self, paper):
            raise AssertionError("should not create")

    paper = make_paper()
    paper.zotero_item_key = "ABC"
    sync_papers(Client(), [paper])
    assert paper.zotero_item_key == "ABC"
