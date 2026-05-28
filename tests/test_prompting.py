from datetime import datetime, timezone

import pytest

from auto_paper.models import Paper, Topic
from auto_paper.prompting import PromptError, choose_prompt_path, render_prompt


def test_topic_prompt_overrides_global():
    topic = Topic(name="RAG", query="x", prompt_path="prompts/rag.md")
    assert choose_prompt_path(topic, "prompts/default.md") == "prompts/rag.md"


def test_render_prompt(tmp_path):
    path = tmp_path / "prompt.md"
    path.write_text("Title: {{title}}\nTopic: {{topic_name}}", encoding="utf-8")
    paper = Paper(
        arxiv_id="1",
        title="Paper",
        authors=["Alice"],
        abstract="Abstract",
        published=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated=None,
        categories=["cs.AI"],
        primary_category="cs.AI",
        abs_url="https://arxiv.org/abs/1",
        pdf_url=None,
    )
    assert "Title: Paper" in render_prompt(path, paper, "Agents")


def test_unknown_prompt_variable_fails(tmp_path):
    path = tmp_path / "prompt.md"
    path.write_text("{{missing}}", encoding="utf-8")
    paper = Paper(
        arxiv_id="1",
        title="Paper",
        authors=[],
        abstract="",
        published=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated=None,
        categories=[],
        primary_category=None,
        abs_url="https://arxiv.org/abs/1",
        pdf_url=None,
    )
    with pytest.raises(PromptError):
        render_prompt(path, paper, "Agents")
