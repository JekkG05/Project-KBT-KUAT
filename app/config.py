import os
from supabase import create_client


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "secret"
    )


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
