from io import BytesIO
from urllib.error import HTTPError

from auto_paper.arxiv_client import ArxivClient, attach_topic, merge_duplicate_papers, parse_arxiv_feed
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


def test_arxiv_client_rate_limits_sequential_requests(monkeypatch):
    class Response:
        def __enter__(self):
            return BytesIO(FEED)

        def __exit__(self, exc_type, exc, tb):
            return False

    sleeps = []
    times = iter([10.0, 10.0, 11.0, 13.0])
    monkeypatch.setattr("auto_paper.arxiv_client.urlopen", lambda *_, **__: Response())
    monkeypatch.setattr("auto_paper.arxiv_client.time.monotonic", lambda: next(times))
    monkeypatch.setattr("auto_paper.arxiv_client.time.sleep", sleeps.append)
    ArxivClient._last_request_at = 0.0

    client = ArxivClient(rate_limit_seconds=3.0)
    topic = Topic(name="A", query="x", max_results=1)

    client.search(topic)
    client.search(topic)

    assert sleeps == [2.0]


def test_arxiv_client_retries_429(monkeypatch):
    class Response:
        def __enter__(self):
            return BytesIO(FEED)

        def __exit__(self, exc_type, exc, tb):
            return False

    calls = iter(
        [
            HTTPError("url", 429, "Too Many Requests", None, None),
            Response(),
        ]
    )

    def fake_urlopen(*_, **__):
        result = next(calls)
        if isinstance(result, HTTPError):
            raise result
        return result

    monkeypatch.setattr("auto_paper.arxiv_client.urlopen", fake_urlopen)
    monkeypatch.setattr("auto_paper.arxiv_client.time.monotonic", lambda: 10.0)
    monkeypatch.setattr("auto_paper.arxiv_client.time.sleep", lambda _: None)
    ArxivClient._last_request_at = 0.0

    client = ArxivClient(rate_limit_seconds=0.0, retries=1, retry_delay=0.0)

    assert len(client.search(Topic(name="A", query="x", max_results=1))) == 1
