import os

class Config:
    """Application configuration, loaded from environment variables."""
    
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")
    
    SQLALCHEMY_DATABASE_URI = os.environ.get("SUPABASE_DB_URL")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
