from auto_paper.cli import main


def test_cli_returns_error_for_missing_config():
    assert main(["--config", "missing.toml", "daily", "--date", "2026-05-28"]) == 1
