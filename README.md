# auto-paper

`auto-paper` 是一个每日 arXiv 论文收集系统：按主题检索论文，写入 SQLite 去重，生成 Markdown 日报，可选调用大模型生成中文摘要，并按分类同步到 Zotero。

## 快速开始

```bash
uv venv
cp config.example.toml config.toml
set -a; source .env; set +a  # 如果启用 LLM 或 Zotero
uv run auto-paper --config config.toml daily --date 2026-05-29
```

日报默认写入 `reports/YYYY-MM-DD.md`，数据库默认写入 `data/auto_paper.sqlite3`，运行日志默认写入 `logs/auto-paper.log`。

## 配置

核心配置在 `config.toml`：

- `[[topics]]`：每个主题包含 arXiv 查询语句、标签和 Zotero collection。
- `[arxiv]`：控制 arXiv API 地址、请求间隔和重试。
- `[llm]`：控制是否启用摘要、模型、API 地址和 prompt。
- `[zotero]`：控制 Zotero library 和 API key 环境变量名。

LLM 和 Zotero 默认关闭。示例配置使用 DeepSeek 的 OpenAI-compatible API。启用时在 `.env` 或 shell 环境中设置：

```bash
DEEPSEEK_API_KEY=...
ZOTERO_API_KEY=...
```

启用 DeepSeek 摘要时：

```toml
[llm]
enabled = true
provider = "openai_compatible"
base_url = "https://api.deepseek.com/chat/completions"
api_key_env = "DEEPSEEK_API_KEY"
model = "deepseek-v4-flash"
prompt_path = "prompts/summary.zh.md"
max_papers_per_run = 20
max_tokens = 2000
retries = 2
retry_delay = 1.0
```

边缘计算、边缘缓存、边缘智能方向可以这样配置：

```toml
[[topics]]
name = "Edge Computing"
query = "(cat:cs.NI OR cat:cs.DC) AND (all:\"edge computing\" OR all:\"mobile edge computing\" OR all:MEC)"
max_results = 20
tags = ["edge-computing", "mec"]

[[topics]]
name = "Edge Caching"
query = "(cat:cs.NI OR cat:cs.DC) AND (all:\"edge caching\" OR all:\"cache placement\" OR all:\"content caching\" OR all:\"coded caching\")"
max_results = 20
tags = ["edge-caching", "cache-placement"]

[[topics]]
name = "Edge Intelligence"
query = "(cat:cs.AI OR cat:cs.LG OR cat:cs.NI) AND (all:\"edge intelligence\" OR all:\"edge AI\" OR all:\"federated learning\" OR all:\"on-device learning\")"
max_results = 20
tags = ["edge-intelligence", "edge-ai", "federated-learning"]
```

## arXiv API 限速

项目使用 arXiv legacy API：`https://export.arxiv.org/api/query`。arXiv 官方要求所有由你控制的机器合计不要超过 1 次请求 / 3 秒，并且一次只保持一个连接。

默认配置会在同一个进程内串行化请求，并保证相邻 arXiv 请求至少间隔 3 秒：

```toml
[arxiv]
base_url = "https://export.arxiv.org/api/query"
rate_limit_seconds = 3.0
retries = 3
retry_delay = 3.0
```

如果在多台机器或多个 cron 任务中运行，需要在调度层避免重叠执行。

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
uv run --extra dev pytest
```
