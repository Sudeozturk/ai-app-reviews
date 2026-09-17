# AI Asistan Uygulamaları Yorum Analizi

Yapay zekâ asistanı uygulamalarının mağaza yorumlarını toplayan, LLM ile
kategorilere ayıran ve zaman içindeki şikayet örüntülerini analiz eden bir proje.

## Kurulum

Gereksinimler: Python 3.11+, Docker.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # şifreyi düzenle
docker compose up -d
python scripts/check_db.py
```

## Testler

```bash
pytest                       # tümü (Docker çalışırken)
pytest -m "not integration"  # sadece birim testleri
ruff check .
```

## Durum

Aşama 0: proje iskeleti, Postgres + pgvector, CI. Tamamlandı.