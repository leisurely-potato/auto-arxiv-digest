from __future__ import annotations

import argparse
from datetime import date
from datetime import datetime
from pathlib import Path
import sys

from .arxiv_client import ArxivClient, merge_duplicate_papers
from .config import load_config
from .db import Database
from .llm_client import LLMClient
from .report import write_markdown_report
from .summarizer import Summarizer
from .zotero_client import ZoteroClient, sync_papers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="auto-paper")
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--log-path", default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    daily = subparsers.add_parser("daily")
    daily.add_argument("--date", default=date.today().isoformat())
    daily.add_argument("--sync-zotero", action="store_true")
    daily.add_argument("--no-llm", action="store_true")

    sync = subparsers.add_parser("sync-zotero")

    args = parser.parse_args(argv)
    try:
        if args.command == "daily":
            return run_daily(args.config, args.date, args.sync_zotero, args.no_llm, args.log_path)
        if args.command == "sync-zotero":
            return run_sync_zotero(args.config, args.log_path)
    except Exception as exc:
        print(f"auto-paper failed: {exc}", file=sys.stderr)
        return 1
    return 0


def run_daily(
    config_path: str,
    run_date: str,
    sync_zotero_enabled: bool,
    no_llm: bool = False,
    log_path: str | None = None,
) -> int:
    config = load_config(config_path)
    resolved_log_path = log_path or config.log_path
    db = Database(config.database_path)
    db.init()
    db.upsert_topics(config.topics)
    run_id = db.start_run(run_date)
    try:
        client = ArxivClient(config.arxiv_base_url)
        all_papers = []
        for topic in config.topics:
            all_papers.extend(client.search(topic))
        papers = merge_duplicate_papers(all_papers)
        new_papers = db.save_papers(papers)

        if not no_llm:
            llm_client = LLMClient(config.llm)
            prompt_path = config.llm.get("prompt_path", "prompts/summary.zh.md")
            max_papers = int(config.llm.get("max_papers_per_run", 20))
            summarizer = Summarizer(llm_client, prompt_path, max_papers)
            summarizer.summarize(new_papers, {topic.name: topic for topic in config.topics})
            for paper in new_papers:
                db.update_summary(paper)

        if sync_zotero_enabled:
            zotero_client = ZoteroClient({**config.zotero, "enabled": True})
            sync_papers(zotero_client, new_papers)
            for paper in new_papers:
                db.update_zotero(paper)

        report_date = date.fromisoformat(run_date)
        path = write_markdown_report(new_papers, report_date, config.report_dir)
        db.finish_run(run_id, "success", f"wrote {path}")
        write_log(resolved_log_path, f"daily success date={run_date} new={len(new_papers)} report={path}")
        print(path)
        return 0
    except Exception as exc:
        db.finish_run(run_id, "failed", str(exc))
        write_log(resolved_log_path, f"daily failed date={run_date} error={exc}")
        raise
    finally:
        db.close()


def run_sync_zotero(config_path: str, log_path: str | None = None) -> int:
    config = load_config(config_path)
    resolved_log_path = log_path or config.log_path
    db = Database(config.database_path)
    db.init()
    db.upsert_topics(config.topics)
    try:
        papers = db.get_unsynced_zotero_papers()
        client = ZoteroClient({**config.zotero, "enabled": True})
        sync_papers(client, papers)
        for paper in papers:
            db.update_zotero(paper)
        failed = [paper for paper in papers if paper.zotero_status == "failed"]
        write_log(resolved_log_path, f"zotero sync total={len(papers)} failed={len(failed)}")
        print(f"synced={len(papers) - len(failed)} failed={len(failed)}")
        return 1 if failed else 0
    finally:
        db.close()


def write_log(log_path: str, message: str) -> None:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{timestamp} {message}\n")


if __name__ == "__main__":
    raise SystemExit(main())
