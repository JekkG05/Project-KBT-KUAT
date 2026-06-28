import os
from dotenv import load_dotenv
from supabase import create_client


load_dotenv()


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret"
    )


    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False



SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)


SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
