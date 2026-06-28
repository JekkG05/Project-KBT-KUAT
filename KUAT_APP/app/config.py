import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)


def _normalize_database_url(url: str | None) -> str:
    """Supabase memakai PostgreSQL. Fallback SQLite hanya untuk demo lokal tanpa .env."""
    if not url:
        return f"sqlite:///{INSTANCE_DIR / 'kuat.db'}"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "kuat-dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
