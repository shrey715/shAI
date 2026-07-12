import history


def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr(history, "HISTORY_DIR", tmp_path)
    monkeypatch.setattr(history, "HISTORY_FILE", tmp_path / "history.jsonl")


def test_load_empty_when_no_file(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    assert history.load() == []


def test_append_and_load_roundtrip(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    history.append({"query": "list files", "status": "executed"})
    history.append({"query": "check disk usage", "status": "not_executed"})

    entries = history.load()
    assert len(entries) == 2
    assert entries[0]["query"] == "list files"
    assert entries[1]["query"] == "check disk usage"


def test_load_respects_limit(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    for i in range(5):
        history.append({"query": f"q{i}"})

    entries = history.load(limit=2)
    assert [e["query"] for e in entries] == ["q3", "q4"]


def test_clear_removes_file(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    history.append({"query": "list files"})
    assert history.HISTORY_FILE.exists()

    history.clear()
    assert not history.HISTORY_FILE.exists()
    assert history.load() == []
