from datetime import date, datetime, timezone

from auto_paper.models import Paper
from auto_paper.report import render_markdown_report


def paper():
    return Paper(
        arxiv_id="2401.1",
        title="Useful Paper",
        authors=["Alice"],
        abstract="Original abstract",
        published=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated=None,
        categories=["cs.AI"],
        primary_category="cs.AI",
        abs_url="https://arxiv.org/abs/2401.1",
        pdf_url="https://arxiv.org/pdf/2401.1",
        topics=["Agents"],
    )


def test_report_contains_paper_fields():
    markdown = render_markdown_report([paper()], date(2026, 5, 28))
    assert "# arXiv Daily Report - 2026-05-28" in markdown
    assert "## Agents" in markdown
    assert "Useful Paper" in markdown
    assert "https://arxiv.org/abs/2401.1" in markdown


def test_empty_report():
    markdown = render_markdown_report([], date(2026, 5, 28))
    assert "今日无新增论文" in markdown
