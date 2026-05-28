# Prompt Templates

LLM 摘要默认使用 `prompts/summary.zh.md`。可以在 `config.toml` 的 `[llm]`
里设置全局 `prompt_path`，也可以在单个 `[[topics]]` 里设置 `prompt_path`
覆盖全局模板。

可用变量：

- `{{title}}`
- `{{authors}}`
- `{{abstract}}`
- `{{topic_name}}`
- `{{categories}}`
- `{{primary_category}}`
- `{{published}}`
- `{{updated}}`
- `{{abs_url}}`
- `{{pdf_url}}`
- `{{arxiv_id}}`
