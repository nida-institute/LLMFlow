"""`load-db --register` must actually record the database in the registry (LLMFlow#183).

The flag was parsed but never wired (a TODO in cli.py), so `--register` printed
success while the registry stayed empty. `run_load_db` is mocked here so the tests
don't need a real BaseX install — the bug is purely the missing registration wiring.
"""
from unittest.mock import patch

import llmflow.cli as cli
from llmflow.registry import Registry


def test_load_db_register_records_database(monkeypatch, tmp_path):
    monkeypatch.setenv("SP_REGISTRY_PATH", str(tmp_path))
    with patch("llmflow.load_db.run_load_db") as mock_load:
        cli.main(["load-db", "basex", "macula-hebrew", "--register"])
        mock_load.assert_called_once()
    dbs = Registry().databases.list()
    assert any(d["name"] == "macula-hebrew" and d["type"] == "basex" for d in dbs)


def test_load_db_without_register_does_not_record(monkeypatch, tmp_path):
    monkeypatch.setenv("SP_REGISTRY_PATH", str(tmp_path))
    with patch("llmflow.load_db.run_load_db"):
        cli.main(["load-db", "basex", "macula-hebrew"])
    assert Registry().databases.list() == []


def test_load_db_register_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("SP_REGISTRY_PATH", str(tmp_path))
    with patch("llmflow.load_db.run_load_db"):
        cli.main(["load-db", "basex", "macula-hebrew", "--register"])
        cli.main(["load-db", "basex", "macula-hebrew", "--register", "--force"])
    dbs = [d for d in Registry().databases.list() if d["name"] == "macula-hebrew"]
    assert len(dbs) == 1
