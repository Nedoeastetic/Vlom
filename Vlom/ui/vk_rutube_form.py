import streamlit as st

def render_vk_rutube_form(current_url: str):
    st.write("---")
    st.subheader("🔗 Или обработайте видео с VK / Rutube")

    if 'vk_rutube_field_key' not in st.session_state:
        st.session_state.vk_rutube_field_key = 0

    input_key = f"vk_rutube_input_{st.session_state.vk_rutube_field_key}"
    display_value = st.session_state.get('vk_rutube_input_value', '') or current_url or ''

    with st.form("vk_rutube_form"):
        url = st.text_input(
            "Ссылка на VK Видео или Rutube:",
            value=display_value,
            placeholder="https://vk.com/video... или https://rutube.ru/video/...",
            key=input_key
        )
        submitted = st.form_submit_button("🚀 Получить текст из VK/Rutube")

    return url, submitted

def handle_vk_rutube_submit(url: str, current_stored_url: str):
    if url and url != current_stored_url:
        st.session_state.vk_rutube_url = url
        st.session_state.vk_rutube_input_value = url
def render_rutube_vk_help():
    with st.expander("💡 Инструкция для VK Видео и Rutube"):
        st.markdown("""
        **📌 Как вставить ссылку:**
        - **VK:** `https://vk.com/video-123456_789012`
        - **Rutube:** `https://rutube.ru/video/a1b2c3d4/`

        **⚠️ Требования:**
        - Видео должно быть **общедоступным** (не приватным)
        - Обработка идёт через скачивание аудио + Whisper (1–3 мин)
        - Если видео удалено или заблокировано по регионам — обработка завершится ошибкой
        """)