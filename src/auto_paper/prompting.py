from __future__ import annotations

from pathlib import Path
import re

from .models import Paper, Topic

TOKEN_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


class PromptError(RuntimeError):
    pass


def choose_prompt_path(topic: Topic, global_prompt_path: str) -> str:
    return topic.prompt_path or global_prompt_path


def render_prompt(path: str | Path, paper: Paper, topic_name: str) -> str:
    prompt_path = Path(path)
    if not prompt_path.exists():
        raise PromptError(f"prompt file not found: {prompt_path}")
    template = prompt_path.read_text(encoding="utf-8")
    values = {
        "title": paper.title,
        "authors": ", ".join(paper.authors),
        "abstract": paper.abstract,
        "topic_name": topic_name,
        "categories": ", ".join(paper.categories),
        "primary_category": paper.primary_category or "",
        "published": paper.published.date().isoformat(),
        "updated": paper.updated.date().isoformat() if paper.updated else "",
        "abs_url": paper.abs_url,
        "pdf_url": paper.pdf_url or "",
        "arxiv_id": paper.arxiv_id,
    }

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise PromptError(f"unknown prompt variable: {key}")
        return values[key]

    return TOKEN_RE.sub(replace, template)
