import os


class Config:
    """Application configuration, loaded from environment variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SUPABASE_DB_URL",
        "postgresql+psycopg2://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres?sslmode=require",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
