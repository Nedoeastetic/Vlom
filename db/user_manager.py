# db/user_manager.py
from .supabase_client import get_supabase_client
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta

NOTE_TTL_DAYS = 7  # Срок хранения конспектов


# =============================================================================
# АУТЕНТИФИКАЦИЯ
# =============================================================================

def sign_up(username: str, email: str, password: str) -> tuple[Optional[Dict], Optional[str]]:
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

        if user.identities is not None and len(user.identities) == 0:
            return None, "Пользователь с таким email уже существует."

        return {"id": user.id, "username": username, "email": email}, None

    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg or "duplicate" in error_msg.lower():
            return None, "Пользователь с таким email уже существует."
        return None, f"Ошибка регистрации: {e}"


def sign_in(email: str, password: str) -> tuple[Optional[Dict], Optional[str]]:
    supabase = get_supabase_client()
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        user = response.user
        if not user:
            return None, "Неверный email или пароль."

        username = (user.user_metadata or {}).get("username") or email.split("@")[0]

        try:
            profile = supabase.table("users").select("username").eq("id", user.id).execute()
            if profile.data:
                username = profile.data[0]["username"]
        except Exception:
            pass

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
    """Сохраняет заметку со сроком хранения 7 дней."""
    supabase = get_supabase_client()
    try:
        expires_at = (datetime.now(timezone.utc) + timedelta(days=NOTE_TTL_DAYS)).isoformat()
        response = supabase.table("notes").insert({
            "userid": user_id,
            "notename": note_name,
            "content": content,
            "expires_at": expires_at,
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Ошибка сохранения заметки: {e}")
        return None


def get_user_notes(user_id: str) -> list:
    """Возвращает только актуальные (не просроченные) заметки пользователя."""
    supabase = get_supabase_client()
    try:
        now = datetime.now(timezone.utc).isoformat()
        response = (
            supabase.table("notes")
            .select("*")
            .eq("userid", user_id)
            .gt("expires_at", now)       # только те, у которых expires_at > сейчас
            .order("expires_at", desc=False)  # ближайшие к истечению — первые
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"❌ Ошибка получения заметок: {e}")
        return []


def delete_note(note_id: str, user_id: str) -> bool:
    """Удаляет заметку по ID."""
    supabase = get_supabase_client()
    try:
        supabase.table("notes").delete().eq("id", note_id).eq("userid", user_id).execute()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления заметки: {e}")
        return False


def delete_expired_notes() -> int:
    """Удаляет все просроченные заметки. Возвращает количество удалённых."""
    supabase = get_supabase_client()
    try:
        now = datetime.now(timezone.utc).isoformat()
        response = supabase.table("notes").delete().lt("expires_at", now).execute()
        return len(response.data) if response.data else 0
    except Exception as e:
        print(f"❌ Ошибка очистки просроченных заметок: {e}")
        return 0


def days_until_expiry(expires_at_str: str) -> int:
    """Возвращает количество дней до истечения срока заметки."""
    try:
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        delta = expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)
    except Exception:
        return 0