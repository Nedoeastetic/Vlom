import streamlit as st


def render_youtube_form(current_url: str):
    """
    Отрисовывает форму для ввода YouTube-ссылки.
    
    🔹 Использует динамический ключ для сброса поля при очистке
    """
    st.write("---")
    st.subheader("🔗 Или обработайте видео с YouTube")
    
    # Инициализируем счётчик ключей если нужно
    if 'youtube_field_key' not in st.session_state:
        st.session_state.youtube_field_key = 0
    
    # 🔹 Динамический ключ для поля ввода
    input_key = f"youtube_input_{st.session_state.youtube_field_key}"
    
    # Определяем значение для отображения
    display_value = st.session_state.get('youtube_input_value', '') or current_url or ''
    
    with st.form("youtube_form"):
        youtube_url = st.text_input(
            "Ссылка на YouTube:",
            value=display_value,
            placeholder="https://www.youtube.com/watch?v=...  ",
            key=input_key
        )
        submitted = st.form_submit_button("🚀 Получить текст из видео")
    
    return youtube_url, submitted


def handle_youtube_submit(youtube_url: str, current_stored_url: str):
    """Обновляет youtube_url в session_state при изменении"""
    if youtube_url and youtube_url != current_stored_url:
        st.session_state.youtube_url = youtube_url
        st.session_state.youtube_input_value = youtube_url