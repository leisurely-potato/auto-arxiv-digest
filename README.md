# auto-paper

`auto-paper` 是一个每日 arXiv 论文收集系统：按主题检索论文，写入 SQLite 去重，生成 Markdown 日报，可选调用大模型生成中文摘要，并按分类同步到 Zotero。

## 快速开始

```bash
uv venv
cp config.example.toml config.toml
uv run auto-paper --config config.toml daily --date 2026-05-28
```

日报默认写入 `reports/YYYY-MM-DD.md`，数据库默认写入 `data/auto_paper.sqlite3`，运行日志默认写入 `logs/auto-paper.log`。

## 配置

核心配置在 `config.toml`：

- `[[topics]]`：每个主题包含 arXiv 查询语句、标签和 Zotero collection。
- `[llm]`：控制是否启用摘要、模型、API 地址和 prompt。
- `[zotero]`：控制 Zotero library 和 API key 环境变量名。

LLM 和 Zotero 默认关闭。示例配置使用 DeepSeek 的 OpenAI-compatible API。启用时在 `.env` 或 shell 环境中设置：

```bash
DEEPSEEK_API_KEY=...
ZOTERO_API_KEY=...
```

## 自定义 Prompt

默认 prompt 位于 `prompts/summary.zh.md`。可以在 `[llm]` 中设置全局模板：

```toml
[llm]
enabled = true
prompt_path = "prompts/summary.zh.md"
```

也可以在某个 topic 中覆盖：

```toml
[[topics]]
name = "RAG"
query = "cat:cs.CL AND (retrieval OR RAG)"
prompt_path = "prompts/rag.zh.md"
```

模板变量见 `prompts/README.md`。

## Zotero 分类

Zotero 使用 Collection + 标签：

- 每篇论文创建一个 Zotero item。
- 命中多个 topic 时进入多个 collection。
- 标签包含 topic 标签、Zotero 标签、arXiv 分类和 LLM 关键词。
- 不自动创建 collection，必须在配置里提供 `zotero_collection_id`。

单独同步未入库论文：

```bash
uv run auto-paper --config config.toml sync-zotero
```

日报后同步：

```bash
uv run auto-paper --config config.toml daily --sync-zotero
```

## 定时任务

推荐使用 `scripts/run_daily.sh` 作为统一入口：

```bash
chmod +x scripts/run_daily.sh scripts/install_cron.sh
scripts/run_daily.sh
```

默认定时脚本只生成日报。需要同时同步 Zotero 时：

```bash
AUTO_PAPER_SYNC_ZOTERO=1 scripts/run_daily.sh
```

安装 cron：

```bash
AUTO_PAPER_CRON="0 8 * * *" scripts/install_cron.sh
```

也可以参考 `systemd/auto-paper.service` 和 `systemd/auto-paper.timer`。

## 测试

```bash
uv run pytest
```
