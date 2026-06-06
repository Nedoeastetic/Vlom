import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_client: Client | None = None


def get_supabase_client() -> Client:
    """Возвращает singleton-клиент Supabase (anon/public доступ)."""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise RuntimeError(
                "❌ Не заданы переменные окружения SUPABASE_URL и/или SUPABASE_KEY.\n"
                "Создайте файл `.env` в корне проекта и укажите их там."
            )
        _client = create_client(url, key)
    return _client