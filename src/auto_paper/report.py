from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

from .models import Paper


def write_markdown_report(papers: list[Paper], report_date: date, report_dir: str | Path) -> Path:
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_date.isoformat()}.md"
    path.write_text(render_markdown_report(papers, report_date), encoding="utf-8")
    return path


def render_markdown_report(papers: list[Paper], report_date: date) -> str:
    lines = [f"# arXiv Daily Report - {report_date.isoformat()}", ""]
    if not papers:
        lines.extend(["今日无新增论文。", ""])
        return "\n".join(lines)

    by_topic: dict[str, list[Paper]] = defaultdict(list)
    for paper in papers:
        topics = paper.topics or ["Uncategorized"]
        for topic in topics:
            by_topic[topic].append(paper)

    for topic in sorted(by_topic):
        lines.extend([f"## {topic}", ""])
        for paper in by_topic[topic]:
            lines.extend(_paper_lines(paper))
    return "\n".join(lines)


def _paper_lines(paper: Paper) -> list[str]:
    lines = [
        f"### {paper.title}",
        "",
        f"- Authors: {', '.join(paper.authors)}",
        f"- Published: {paper.published.date().isoformat()}",
        f"- arXiv: [{paper.arxiv_id}]({paper.abs_url})",
    ]
    if paper.pdf_url:
        lines.append(f"- PDF: {paper.pdf_url}")
    if paper.categories:
        lines.append(f"- Categories: {', '.join(paper.categories)}")
    if paper.summary:
        lines.extend(["", "**LLM Summary**", "", paper.summary])
        if paper.contributions:
            lines.extend(["", "**Contributions**"])
            lines.extend([f"- {item}" for item in paper.contributions])
        if paper.keywords:
            lines.append(f"- Keywords: {', '.join(paper.keywords)}")
        if paper.audience:
            lines.append(f"- Audience: {paper.audience}")
    else:
        lines.extend(["", "**Abstract**", "", paper.abstract])
    if paper.summary_error:
        lines.extend(["", f"> Summary failed: {paper.summary_error}"])
    lines.append("")
    return lines
