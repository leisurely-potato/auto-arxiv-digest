from __future__ import annotations

from .llm_client import LLMClient
from .models import Paper, Topic
from .prompting import choose_prompt_path, render_prompt


class Summarizer:
    def __init__(self, llm_client: LLMClient, global_prompt_path: str, max_papers: int = 20):
        self.llm_client = llm_client
        self.global_prompt_path = global_prompt_path
        self.max_papers = max_papers

    def summarize(self, papers: list[Paper], topics: dict[str, Topic]) -> list[Paper]:
        if not self.llm_client.enabled:
            return papers
        summarized = 0
        for paper in papers:
            if paper.summary:
                continue
            if summarized >= self.max_papers:
                break
            topic_name = paper.topics[0] if paper.topics else next(iter(topics))
            topic = topics[topic_name]
            prompt_path = choose_prompt_path(topic, self.global_prompt_path)
            paper.prompt_path = prompt_path
            try:
                prompt = render_prompt(prompt_path, paper, topic_name)
                result = self.llm_client.summarize(prompt)
                apply_summary(paper, result)
                summarized += 1
            except Exception as exc:
                paper.summary_error = str(exc)
        return papers


def apply_summary(paper: Paper, result: dict) -> None:
    paper.summary = _string(result.get("summary"))
    paper.contributions = _list(result.get("contributions"))
    paper.keywords = _list(result.get("keywords"))
    paper.audience = _string(result.get("audience"))


def _string(value: object) -> str | None:
    return str(value).strip() if value is not None and str(value).strip() else None


def _list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
