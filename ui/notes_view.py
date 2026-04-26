import streamlit as st
from db.user_manager import get_user_notes

def render_my_notes():
    st.subheader("📝 Мои конспекты")
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.info("Авторизуйтесь, чтобы видеть свои заметки.")
        return

    notes = get_user_notes(user_id)
    if not notes:
        st.info("У вас пока нет сохранённых конспектов.")
        return

    for note in notes:
        with st.expander(f"📌 {note['notename']} (ID: {note['id']})"):
            st.write(note["content"])
            st.download_button(
                "📥 Скачать",
                data=note["content"],
                file_name=f"{note['notename']}.md",
                mime="text/markdown",
                key=f"dl_{note['id']}"
            )