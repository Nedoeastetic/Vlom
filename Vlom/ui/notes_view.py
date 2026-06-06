from __future__ import annotations

import html
import re

import streamlit as st
from streamlit_quill import st_quill

from db.user_manager import (
    create_folder,
    delete_folder,
    delete_note,
    get_last_db_error,
    get_user_folders,
    get_user_notes,
    move_note_to_folder,
    rename_folder,
    update_note,
)


UNFILED_KEY = "__unfiled__"
ALL_NOTES_KEY = "__all__"


def _safe_filename(value: str) -> str:
    filename = re.sub(r"[^\w\-]+", "_", value.strip(), flags=re.UNICODE)
    return filename.strip("_") or "note"


def _looks_like_html(value: str) -> bool:
    return bool(re.search(r"</?[a-z][^>]*>", value or "", flags=re.IGNORECASE))


def _folder_options(folders: list[dict]) -> dict[str, str | None]:
    options: dict[str, str | None] = {"Без папки": None}

    for folder in folders:
        options[str(folder["name"])] = str(folder["id"])

    return options


def _clear_note_editor() -> None:
    for key in (
        "saved_note_editor_id",
        "saved_note_editor_name",
        "saved_note_editor_content",
        "saved_note_editor_folder_id",
    ):
        st.session_state.pop(key, None)


def _create_folder_panel(user_id: str) -> None:
    """Создание папки с явным сообщением об ошибке Supabase."""

    with st.sidebar.expander("➕ Новая папка", expanded=False):
        folder_name = st.text_input(
            "Название папки",
            placeholder="Например: Математика",
            key="new_folder_name_sidebar",
        )

        if st.button(
            "Создать папку",
            key="create_folder_sidebar_btn",
            use_container_width=True,
        ):
            name = folder_name.strip()

            if not name:
                st.warning("Введите название папки.")
            else:
                created = create_folder(user_id, name)

                if created:
                    st.session_state.selected_folder_key = str(created["id"])
                    st.session_state.folder_flash = (
                        f"Папка «{created['name']}» создана."
                    )
                    st.rerun()
                else:
                    error = get_last_db_error()
                    st.error(
                        error
                        or "Не удалось создать папку. Возможно, папка "
                           "с таким названием уже существует."
                    )


def _render_folder_sidebar(
    user_id: str,
    folders: list[dict],
    notes: list[dict],
) -> str:
    """Показывает каждую пользовательскую папку отдельной кнопкой."""

    st.sidebar.markdown("### 📁 Папки конспектов")

    flash = st.session_state.pop("folder_flash", None)
    if flash:
        st.sidebar.success(flash)

    _create_folder_panel(user_id)

    if st.sidebar.button(
        "🔄 Обновить папки",
        key="refresh_folders_btn",
        use_container_width=True,
    ):
        st.rerun()

    selected = st.session_state.get("selected_folder_key", ALL_NOTES_KEY)

    counts: dict[str, int] = {ALL_NOTES_KEY: len(notes), UNFILED_KEY: 0}

    for folder in folders:
        counts[str(folder["id"])] = 0

    for note in notes:
        folder_id = note.get("folder_id")

        if folder_id is None:
            counts[UNFILED_KEY] += 1
        else:
            key = str(folder_id)
            counts[key] = counts.get(key, 0) + 1

    if st.sidebar.button(
        f"📚 Все конспекты ({counts[ALL_NOTES_KEY]})",
        key="folder_all_notes",
        type="primary" if selected == ALL_NOTES_KEY else "secondary",
        use_container_width=True,
    ):
        st.session_state.selected_folder_key = ALL_NOTES_KEY
        st.rerun()

    if counts[UNFILED_KEY] > 0:
        if st.sidebar.button(
            f"🗒️ Без папки ({counts[UNFILED_KEY]})",
            key="folder_unfiled_notes",
            type="primary" if selected == UNFILED_KEY else "secondary",
            use_container_width=True,
        ):
            st.session_state.selected_folder_key = UNFILED_KEY
            st.rerun()

    for folder in folders:
        folder_id = str(folder["id"])
        folder_name = str(folder["name"])

        if st.sidebar.button(
            f"📁 {folder_name} ({counts.get(folder_id, 0)})",
            key=f"folder_button_{folder_id}",
            type="primary" if selected == folder_id else "secondary",
            use_container_width=True,
        ):
            st.session_state.selected_folder_key = folder_id
            st.rerun()

    return selected


def _render_folder_management(
    user_id: str,
    folders: list[dict],
    selected_key: str,
) -> None:
    selected_folder = next(
        (
            folder
            for folder in folders
            if str(folder["id"]) == selected_key
        ),
        None,
    )

    if selected_folder is None:
        return

    folder_id = str(selected_folder["id"])
    folder_name = str(selected_folder["name"])

    with st.expander("⚙️ Настройки папки", expanded=False):
        new_name = st.text_input(
            "Новое название",
            value=folder_name,
            key=f"rename_folder_input_{folder_id}",
        )

        col_rename, col_delete = st.columns(2)

        with col_rename:
            if st.button(
                "Переименовать",
                key=f"rename_folder_btn_{folder_id}",
                use_container_width=True,
            ):
                if rename_folder(folder_id, user_id, new_name):
                    st.success("Папка переименована.")
                    st.rerun()
                else:
                    st.error("Не удалось переименовать папку.")

        with col_delete:
            if st.button(
                "Удалить папку",
                key=f"delete_folder_btn_{folder_id}",
                use_container_width=True,
            ):
                if delete_folder(folder_id, user_id):
                    st.session_state.selected_folder_key = UNFILED_KEY
                    st.success(
                        "Папка удалена. Конспекты перемещены в «Без папки»."
                    )
                    st.rerun()
                else:
                    st.error("Не удалось удалить папку.")


def _open_note_editor(note: dict) -> None:
    st.session_state.saved_note_editor_id = note["id"]
    st.session_state.saved_note_editor_name = note.get(
        "notename",
        "Без названия",
    )
    st.session_state.saved_note_editor_content = note.get("content", "")
    st.session_state.saved_note_editor_folder_id = note.get("folder_id")
    st.rerun()


def _render_saved_note_editor(
    user_id: str,
    folders: list[dict],
) -> bool:
    note_id = st.session_state.get("saved_note_editor_id")

    if note_id is None:
        return False

    st.subheader("✏️ Редактирование сохранённого конспекта")

    note_name = st.text_input(
        "Название конспекта",
        value=st.session_state.get("saved_note_editor_name", ""),
        key="saved_note_name_editor",
    )

    options = _folder_options(folders)
    labels = list(options.keys())
    current_folder_id = st.session_state.get("saved_note_editor_folder_id")
    current_label = next(
        (
            label
            for label, folder_id in options.items()
            if folder_id == (
                str(current_folder_id)
                if current_folder_id is not None
                else None
            )
        ),
        "Без папки",
    )

    folder_label = st.selectbox(
        "Папка",
        labels,
        index=labels.index(current_label),
        key="saved_note_folder_editor",
    )

    edited_content = st_quill(
        value=st.session_state.get("saved_note_editor_content", ""),
        html=True,
        toolbar=[
            ["bold", "italic", "underline", "strike"],
            [{"header": [1, 2, 3, False]}],
            [{"size": ["small", False, "large", "huge"]}],
            [{"font": []}, {"color": []}, {"background": []}],
            [{"list": "ordered"}, {"list": "bullet"}],
            [{"align": []}],
            ["blockquote", "link", "clean"],
        ],
        key=f"saved_note_quill_{note_id}",
    )

    if edited_content is None:
        edited_content = st.session_state.get("saved_note_editor_content", "")

    col_save, col_cancel = st.columns(2)

    with col_save:
        if st.button(
            "💾 Сохранить изменения",
            key=f"save_saved_note_{note_id}",
            type="primary",
            use_container_width=True,
        ):
            if not note_name.strip():
                st.warning("Название не может быть пустым.")
            elif not edited_content:
                st.warning("Конспект не может быть пустым.")
            else:
                folder_id = options[folder_label]
                updated = update_note(
                    note_id,
                    user_id,
                    note_name=note_name,
                    content=edited_content,
                    folder_id=folder_id,
                    update_folder=True,
                )

                if updated:
                    _clear_note_editor()
                    st.success("Конспект обновлён.")
                    st.rerun()
                else:
                    st.error("Не удалось обновить конспект.")

    with col_cancel:
        if st.button(
            "Отмена",
            key=f"cancel_saved_note_{note_id}",
            use_container_width=True,
        ):
            _clear_note_editor()
            st.rerun()

    return True


def _filter_notes(notes: list[dict], selected_key: str) -> list[dict]:
    if selected_key == ALL_NOTES_KEY:
        return notes
    if selected_key == UNFILED_KEY:
        return [note for note in notes if note.get("folder_id") is None]

    return [
        note
        for note in notes
        if str(note.get("folder_id")) == selected_key
    ]


def _selected_title(folders: list[dict], selected_key: str) -> str:
    if selected_key == ALL_NOTES_KEY:
        return "Все конспекты"
    if selected_key == UNFILED_KEY:
        return "Без папки"

    folder = next(
        (
            folder
            for folder in folders
            if str(folder["id"]) == selected_key
        ),
        None,
    )

    return str(folder["name"]) if folder else "Конспекты"


def render_my_notes() -> None:
    """Показывает пользовательские папки и сохранённые конспекты."""

    user_id = st.session_state.get("user_id")

    if not user_id:
        st.info("Авторизуйтесь, чтобы использовать папки конспектов.")
        return

    folders = get_user_folders(user_id)
    folders_error = get_last_db_error()
    notes = get_user_notes(user_id)

    if folders_error:
        st.error(folders_error)
        st.info(
            "Проверьте SQL-миграцию, RLS-политики и выполнен ли вход "
            "в Supabase Auth."
        )

    selected_key = _render_folder_sidebar(user_id, folders, notes)

    if _render_saved_note_editor(user_id, folders):
        return

    title = _selected_title(folders, selected_key)
    st.subheader(f"📁 {title}")

    _render_folder_management(user_id, folders, selected_key)

    filtered_notes = _filter_notes(notes, selected_key)

    if not filtered_notes:
        if not folders and not notes:
            st.info(
                "Создайте первую папку в боковой панели, затем сохраните "
                "в неё конспект."
            )
        else:
            st.info("В этой папке пока нет конспектов.")
        return

    folder_options = _folder_options(folders)
    folder_labels = list(folder_options.keys())

    for note in filtered_notes:
        note_id = note["id"]
        note_name = str(note.get("notename") or "Без названия")
        content = str(note.get("content") or "")
        current_folder_id = note.get("folder_id")

        with st.container(border=True):
            st.markdown(f"### {html.escape(note_name)}")

            if _looks_like_html(content):
                st.markdown(content, unsafe_allow_html=True)
            else:
                st.markdown(content)

            current_label = next(
                (
                    label
                    for label, folder_id in folder_options.items()
                    if folder_id == (
                        str(current_folder_id)
                        if current_folder_id is not None
                        else None
                    )
                ),
                "Без папки",
            )

            target_label = st.selectbox(
                "Переместить в папку",
                folder_labels,
                index=folder_labels.index(current_label),
                key=f"move_note_select_{note_id}",
            )

            col_move, col_edit, col_download, col_delete = st.columns(4)

            with col_move:
                if st.button(
                    "📂 Переместить",
                    key=f"move_note_btn_{note_id}",
                    use_container_width=True,
                ):
                    target_folder_id = folder_options[target_label]
                    current_value = (
                        str(current_folder_id)
                        if current_folder_id is not None
                        else None
                    )

                    if target_folder_id == current_value:
                        st.info("Конспект уже находится в выбранной папке.")
                    elif move_note_to_folder(
                        note_id,
                        user_id,
                        target_folder_id,
                    ):
                        st.session_state.folder_flash = (
                            f"Конспект «{note_name}» перемещён в «{target_label}»."
                        )
                        st.session_state.selected_folder_key = (
                            str(target_folder_id)
                            if target_folder_id is not None
                            else UNFILED_KEY
                        )
                        st.rerun()
                    else:
                        st.error(
                            get_last_db_error()
                            or "Не удалось переместить конспект."
                        )

            with col_edit:
                if st.button(
                    "✏️ Изменить",
                    key=f"edit_note_btn_{note_id}",
                    use_container_width=True,
                ):
                    _open_note_editor(note)

            with col_download:
                st.download_button(
                    "📥 Скачать",
                    data=content,
                    file_name=f"{_safe_filename(note_name)}.html",
                    mime="text/html; charset=utf-8",
                    key=f"download_note_{note_id}",
                    use_container_width=True,
                )

            with col_delete:
                if st.button(
                    "🗑️ Удалить",
                    key=f"delete_note_btn_{note_id}",
                    use_container_width=True,
                ):
                    if delete_note(note_id, user_id):
                        st.rerun()
                    else:
                        st.error("Не удалось удалить конспект.")
