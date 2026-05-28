from auto_paper.arxiv_client import attach_topic, merge_duplicate_papers, parse_arxiv_feed
from auto_paper.models import Topic


FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.00001v1</id>
    <updated>2024-01-02T00:00:00Z</updated>
    <published>2024-01-01T00:00:00Z</published>
    <title> A Test Paper </title>
    <summary> This is a test abstract. </summary>
    <author><name>Alice</name></author>
    <author><name>Bob</name></author>
    <arxiv:primary_category term="cs.AI" />
    <category term="cs.AI" />
    <category term="cs.CL" />
    <link href="http://arxiv.org/abs/2401.00001v1" rel="alternate" type="text/html" />
    <link title="pdf" href="http://arxiv.org/pdf/2401.00001v1" rel="related" type="application/pdf" />
  </entry>
</feed>
"""


def test_parse_arxiv_feed():
    papers = parse_arxiv_feed(FEED)
    assert len(papers) == 1
    paper = papers[0]
    assert paper.arxiv_id == "2401.00001v1"
    assert paper.title == "A Test Paper"
    assert paper.authors == ["Alice", "Bob"]
    assert paper.primary_category == "cs.AI"
    assert paper.pdf_url == "http://arxiv.org/pdf/2401.00001v1"


def test_merge_duplicate_papers_keeps_topic_metadata():
    paper1, paper2 = parse_arxiv_feed(FEED)[0], parse_arxiv_feed(FEED)[0]
    attach_topic(paper1, Topic(name="A", query="x", tags=["tag-a"], zotero_collection_id="c1"))
    attach_topic(paper2, Topic(name="B", query="x", tags=["tag-b"], zotero_collection_id="c2"))
    merged = merge_duplicate_papers([paper1, paper2])
    assert len(merged) == 1
    assert merged[0].topics == ["A", "B"]
    assert merged[0].zotero_collections == ["c1", "c2"]
