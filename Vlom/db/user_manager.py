from __future__ import annotations

from typing import Dict, Optional

from .supabase_client import get_supabase_client


# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================

def _remember_db_error(message: str) -> None:
    """Сохраняет последнюю ошибку для отображения в интерфейсе."""
    try:
        import streamlit as st
        st.session_state.last_folders_db_error = message
    except Exception:
        pass


def clear_last_db_error() -> None:
    try:
        import streamlit as st
        st.session_state.pop("last_folders_db_error", None)
    except Exception:
        pass


def get_last_db_error() -> str | None:
    try:
        import streamlit as st
        return st.session_state.get("last_folders_db_error")
    except Exception:
        return None


# =============================================================================
# АУТЕНТИФИКАЦИЯ
# =============================================================================

def sign_up(
    username: str,
    email: str,
    password: str,
) -> tuple[Optional[Dict], Optional[str]]:
    supabase = get_supabase_client()

    try:
        response = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"data": {"username": username}},
            }
        )
        user = response.user

        if not user:
            return None, "Не удалось создать пользователя."
        if user.identities is not None and len(user.identities) == 0:
            return None, "Пользователь с таким email уже существует."

        return {
            "id": user.id,
            "username": username,
            "email": email,
        }, None
    except Exception as error:
        error_text = str(error).lower()
        if "already registered" in error_text or "duplicate" in error_text:
            return None, "Пользователь с таким email уже существует."
        return None, f"Ошибка регистрации: {error}"


def sign_in(
    email: str,
    password: str,
) -> tuple[Optional[Dict], Optional[str]]:
    supabase = get_supabase_client()

    try:
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        user = response.user

        if not user:
            return None, "Неверный email или пароль."

        username = (
            (user.user_metadata or {}).get("username")
            or email.split("@")[0]
        )

        try:
            profile = (
                supabase.table("users")
                .select("username")
                .eq("id", user.id)
                .execute()
            )
            if profile.data:
                username = profile.data[0]["username"]
        except Exception:
            pass

        return {
            "id": user.id,
            "username": username,
            "email": user.email,
        }, None
    except Exception as error:
        error_text = str(error).lower()
        if "email not confirmed" in error_text:
            return None, "Email не подтверждён."
        if "invalid" in error_text or "credentials" in error_text:
            return None, "Неверный email или пароль."
        return None, f"Ошибка входа: {error}"


def sign_out() -> bool:
    try:
        get_supabase_client().auth.sign_out()
        return True
    except Exception:
        return False


# =============================================================================
# ПАПКИ
# =============================================================================

def create_folder(user_id: str, folder_name: str) -> Optional[Dict]:
    """Создаёт папку и обязательно повторно читает её из БД."""
    clear_last_db_error()
    name = folder_name.strip()

    if not name:
        _remember_db_error("Название папки не может быть пустым.")
        return None

    client = get_supabase_client()

    try:
        client.table("note_folders").insert(
            {"userid": user_id, "name": name}
        ).execute()

        # Не полагаемся на response.data: PostgREST может вернуть [].
        verify = (
            client.table("note_folders")
            .select("id, userid, name, created_at")
            .eq("userid", user_id)
            .eq("name", name)
            .limit(1)
            .execute()
        )

        return verify.data[0] if verify.data else None
    except Exception as error:
        message = f"Ошибка создания папки: {error}"
        _remember_db_error(message)
        print(message)
        return None


def get_user_folders(user_id: str) -> list[Dict]:
    """Возвращает актуальный список папок без локального кэширования."""
    clear_last_db_error()

    try:
        response = (
            get_supabase_client()
            .table("note_folders")
            .select("id, userid, name, created_at")
            .eq("userid", user_id)
            .order("name")
            .execute()
        )
        return response.data or []
    except Exception as error:
        message = f"Ошибка получения папок: {error}"
        _remember_db_error(message)
        print(message)
        return []


def rename_folder(folder_id: str, user_id: str, new_name: str) -> bool:
    clear_last_db_error()
    name = new_name.strip()

    if not name:
        _remember_db_error("Название папки не может быть пустым.")
        return False

    client = get_supabase_client()

    try:
        client.table("note_folders").update({"name": name}).eq(
            "id", folder_id
        ).eq("userid", user_id).execute()

        verify = (
            client.table("note_folders")
            .select("id")
            .eq("id", folder_id)
            .eq("userid", user_id)
            .eq("name", name)
            .limit(1)
            .execute()
        )
        return bool(verify.data)
    except Exception as error:
        message = f"Ошибка переименования папки: {error}"
        _remember_db_error(message)
        print(message)
        return False


def delete_folder(folder_id: str, user_id: str) -> bool:
    clear_last_db_error()
    client = get_supabase_client()

    try:
        client.table("note_folders").delete().eq(
            "id", folder_id
        ).eq("userid", user_id).execute()

        verify = (
            client.table("note_folders")
            .select("id")
            .eq("id", folder_id)
            .eq("userid", user_id)
            .limit(1)
            .execute()
        )
        return not bool(verify.data)
    except Exception as error:
        message = f"Ошибка удаления папки: {error}"
        _remember_db_error(message)
        print(message)
        return False


# =============================================================================
# КОНСПЕКТЫ
# =============================================================================

def save_note(
    user_id: str,
    note_name: str,
    content: str,
    folder_id: str | None = None,
) -> Optional[Dict]:
    clear_last_db_error()
    client = get_supabase_client()

    payload = {
        "userid": user_id,
        "notename": note_name.strip() or "Без названия",
        "content": content,
        "folder_id": folder_id,
    }

    try:
        response = client.table("notes").insert(payload).execute()
        if response.data:
            return response.data[0]

        verify = (
            client.table("notes")
            .select("*")
            .eq("userid", user_id)
            .eq("notename", payload["notename"])
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        return verify.data[0] if verify.data else None
    except Exception as error:
        message = f"Ошибка сохранения конспекта: {error}"
        _remember_db_error(message)
        print(message)
        return None


def get_user_notes(
    user_id: str,
    folder_id: str | None = None,
    *,
    only_unfiled: bool = False,
) -> list[Dict]:
    clear_last_db_error()

    try:
        query = (
            get_supabase_client()
            .table("notes")
            .select("*")
            .eq("userid", user_id)
        )

        if only_unfiled:
            query = query.is_("folder_id", "null")
        elif folder_id is not None:
            query = query.eq("folder_id", folder_id)

        response = query.order("id", desc=True).execute()
        return response.data or []
    except Exception as error:
        message = f"Ошибка получения конспектов: {error}"
        _remember_db_error(message)
        print(message)
        return []


def update_note(
    note_id: str | int,
    user_id: str,
    *,
    note_name: str | None = None,
    content: str | None = None,
    folder_id: str | None = None,
    update_folder: bool = False,
) -> bool:
    """Обновляет конспект и проверяет сохранённые значения повторным SELECT."""
    clear_last_db_error()
    payload: dict = {}

    if note_name is not None:
        payload["notename"] = note_name.strip() or "Без названия"
    if content is not None:
        payload["content"] = content
    if update_folder:
        payload["folder_id"] = folder_id

    if not payload:
        return True

    client = get_supabase_client()

    try:
        client.table("notes").update(payload).eq("id", note_id).eq(
            "userid", user_id
        ).execute()

        verify = (
            client.table("notes")
            .select("id, notename, content, folder_id")
            .eq("id", note_id)
            .eq("userid", user_id)
            .limit(1)
            .execute()
        )

        if not verify.data:
            return False

        saved = verify.data[0]

        if "notename" in payload and saved.get("notename") != payload["notename"]:
            return False
        if "content" in payload and saved.get("content") != payload["content"]:
            return False
        if update_folder:
            saved_folder = saved.get("folder_id")
            expected = str(folder_id) if folder_id is not None else None
            actual = str(saved_folder) if saved_folder is not None else None
            if actual != expected:
                return False

        return True
    except Exception as error:
        message = f"Ошибка обновления конспекта: {error}"
        _remember_db_error(message)
        print(message)
        return False


def move_note_to_folder(
    note_id: str | int,
    user_id: str,
    folder_id: str | None,
) -> bool:
    return update_note(
        note_id,
        user_id,
        folder_id=folder_id,
        update_folder=True,
    )


def delete_note(note_id: str | int, user_id: str) -> bool:
    clear_last_db_error()
    client = get_supabase_client()

    try:
        client.table("notes").delete().eq("id", note_id).eq(
            "userid", user_id
        ).execute()

        verify = (
            client.table("notes")
            .select("id")
            .eq("id", note_id)
            .eq("userid", user_id)
            .limit(1)
            .execute()
        )
        return not bool(verify.data)
    except Exception as error:
        message = f"Ошибка удаления конспекта: {error}"
        _remember_db_error(message)
        print(message)
        return False
