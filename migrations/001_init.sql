CREATE TABLE IF NOT EXISTS papers (
    arxiv_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    authors_json TEXT NOT NULL,
    abstract TEXT NOT NULL,
    published TEXT NOT NULL,
    updated TEXT,
    categories_json TEXT NOT NULL,
    primary_category TEXT,
    abs_url TEXT NOT NULL,
    pdf_url TEXT,
    doi TEXT,
    summary TEXT,
    contributions_json TEXT NOT NULL DEFAULT '[]',
    keywords_json TEXT NOT NULL DEFAULT '[]',
    audience TEXT,
    summary_error TEXT,
    prompt_path TEXT,
    zotero_item_key TEXT,
    zotero_status TEXT,
    zotero_error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS topics (
    name TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    tags_json TEXT NOT NULL DEFAULT '[]',
    zotero_collection_id TEXT,
    zotero_tags_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS paper_topics (
    arxiv_id TEXT NOT NULL,
    topic_name TEXT NOT NULL,
    PRIMARY KEY (arxiv_id, topic_name),
    FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id),
    FOREIGN KEY (topic_name) REFERENCES topics(name)
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    status TEXT NOT NULL,
    message TEXT
);
