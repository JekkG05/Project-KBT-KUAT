import os
from supabase import create_client


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY"
    )



supabase = create_client(

    os.getenv("SUPABASE_URL"),

    os.getenv("SUPABASE_KEY")

)
