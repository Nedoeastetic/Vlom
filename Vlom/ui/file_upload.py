import streamlit as st
from config.constants import ALL_EXTENSIONS


def render_file_uploader(key_prefix: str = "file_uploader"):
    """
    Отрисовывает виджет загрузки файла с динамическим ключом.
    
    🔹 Ключ меняется при увеличении file_uploader_counter,
       что заставляет Streamlit создать новый виджет (сбросить файл)
    """
    # Получаем счётчик или создаём
    if 'file_uploader_counter' not in st.session_state:
        st.session_state.file_uploader_counter = 0
    
    # 🔹 Уникальный ключ = префикс + счётчик
    unique_key = f"{key_prefix}_{st.session_state.file_uploader_counter}"
    
    uploaded_file = st.file_uploader(
        "📎 Прикрепите файл",
        type=ALL_EXTENSIONS,
        key=unique_key,
        label_visibility="visible"
    )
    
    return uploaded_file