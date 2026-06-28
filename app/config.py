from supabase import create_client
import os


SUPABASE_URL = "https://eljxtoaeurxbdcisklcu.supabase.co"

SUPABASE_KEY = os.getenv("SUPABASE_KEY")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
