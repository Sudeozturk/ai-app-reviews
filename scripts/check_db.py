from reviews.db import get_pgvector_version

if __name__ == "__main__":
    print(f"Bağlantı başarılı, pgvector sürümü: {get_pgvector_version()}")
