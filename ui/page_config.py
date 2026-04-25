import streamlit as st


def setup_page():
    """Настраивает страницу Streamlit"""
    st.set_page_config(
        page_title="Анализатор документов",
        page_icon="📄",
        layout="centered"
    )
    st.title("📄 Универсальный анализатор документов")
    st.write(
        "Загрузите файл (PDF, Word, Excel, аудио или видео) "
        "или ссылку на YouTube, чтобы получить краткое содержание с помощью ИИ."
    )


def init_session_state():
    """Инициализирует хранилище данных сессии"""
    defaults = {
        # Основные данные
        "extracted_text": None,
        "file_info": None,
        "processing_status": None,
        "llm_result": None,
        "youtube_url": "",
        
        # 🔹 Ключи для управления виджетами (ОБЯЗАТЕЛЬНО!)
        "file_uploader_counter": 0,
        "youtube_field_key": 0,
        "youtube_input_value": "",
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

if "llm_result" not in st.session_state:
    st.session_state.llm_result = ""
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "font_size" not in st.session_state:
    st.session_state.font_size = 16
if "font_family" not in st.session_state:
    st.session_state.font_family = "Arial"
if "font_color" not in st.session_state:
    st.session_state.font_color = "#FFFFFF"