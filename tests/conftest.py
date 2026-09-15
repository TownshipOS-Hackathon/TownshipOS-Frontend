import pytest


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    from core import llm
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path / "cache")
    yield
