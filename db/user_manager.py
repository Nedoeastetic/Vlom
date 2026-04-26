from .supabase_client import get_supabase_client
from typing import Optional, Dict


# =============================================================================
# АУТЕНТИФИКАЦИЯ
# =============================================================================

def sign_up(username: str, email: str, password: str) -> tuple[Optional[Dict], Optional[str]]:
    """
    Регистрирует пользователя через Supabase Auth.
    Профиль в public.users создаётся триггером БД.
    """
    supabase = get_supabase_client()
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"username": username}
            }
        })
        user = response.user
        if not user:
            return None, "Не удалось создать пользователя."

        # Supabase может вернуть пользователя, но без подтверждённого email.
        # Проверяем, требуется ли подтверждение.
        if user.identities is not None and len(user.identities) == 0:
            return None, "Пользователь с таким email уже существует."

        return {"id": user.id, "username": username, "email": email}, None

    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg or "duplicate" in error_msg.lower():
            return None, "Пользователь с таким email уже существует."
        return None, f"Ошибка регистрации: {e}"


def sign_in(email: str, password: str) -> tuple[Optional[Dict], Optional[str]]:
    """
    Выполняет вход через Supabase Auth.
    """
    supabase = get_supabase_client()
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        user = response.user
        if not user:
            return None, "Неверный email или пароль."

        # Берём username из метаданных Auth (там точно есть, даже если триггер не успел)
        username = (user.user_metadata or {}).get("username") or email.split("@")[0]

        # Дополнительно пробуем взять из public.users
        try:
            profile = supabase.table("users").select("username").eq("id", user.id).execute()
            if profile.data:
                username = profile.data[0]["username"]
        except Exception:
            pass  # не критично, используем username из метаданных

        return {"id": user.id, "username": username, "email": user.email}, None

    except Exception as e:
        error_msg = str(e).lower()
        if "email not confirmed" in error_msg:
            return None, "📧 Email не подтверждён. Проверьте почту или отключите подтверждение в настройках Supabase."
        if "invalid" in error_msg or "credentials" in error_msg:
            return None, "Неверный email или пароль."
        return None, f"Ошибка входа: {e}"


def sign_out() -> bool:
    supabase = get_supabase_client()
    try:
        supabase.auth.sign_out()
        return True
    except Exception:
        return False


# =============================================================================
# ЗАМЕТКИ
# =============================================================================

def save_note(user_id: str, note_name: str, content: str) -> Optional[Dict]:
    supabase = get_supabase_client()
    try:
        response = supabase.table("notes").insert({
            "userid": user_id,
            "notename": note_name,
            "content": content,
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Ошибка сохранения заметки: {e}")
        return None


def get_user_notes(user_id: str) -> list:
    supabase = get_supabase_client()
    try:
        response = (
            supabase.table("notes")
            .select("*")
            .eq("userid", user_id)
            .order("id", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"❌ Ошибка получения заметок: {e}")
        return []


def delete_note(note_id: str, user_id: str) -> bool:
    supabase = get_supabase_client()
    try:
        supabase.table("notes").delete().eq("id", note_id).eq("userid", user_id).execute()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления заметки: {e}")
        return False