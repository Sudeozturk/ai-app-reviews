import pytest

from reviews.config import get_database_url


def test_database_url_ortam_degiskeninden_okunur(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:1/test")
    assert get_database_url() == "postgresql://u:p@localhost:1/test"


def test_database_url_yoksa_anlasilir_hata_verir(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_database_url()
