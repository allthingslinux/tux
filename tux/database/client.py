import os
from typing import cast

from dotenv import load_dotenv

from supabase import Client, create_client

load_dotenv()

SUPABASE_URL: str = cast(str, os.getenv("SUPABASE_URL", ""))
SUPABASE_KEY: str = cast(str, os.getenv("SUPABASE_KEY", ""))

client: Client = create_client(
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_KEY,
)
