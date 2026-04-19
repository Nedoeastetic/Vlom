import streamlit as st


def render_extracted_text(extracted_text: str, file_info: dict):
    """Отображает извлечённый текст и кнопки скачивания"""
    st.subheader("📋 Доступные действия")
    
    is_large = file_info.get("size_mb", 0) > 5 or len(extracted_text) > 100000
    filename_base = file_info['name'].replace(':', '_')
    
    if is_large:
        st.info(f"📁 Текст очень большой. Для удобства предпросмотр отключён.")
        _render_download_button(
            data=extracted_text, 
            filename=f"{filename_base}_text.md", 
            key="download_original_large"
        )
    else:
        with st.expander("📄 Показать извлечённый текст"):
            st.code(extracted_text, language="markdown")
        _render_download_button(
            data=extracted_text, 
            filename=f"{filename_base}_text.md", 
            key="download_original_small"
        )
    
    st.write("---")


def _render_download_button(data: str, filename: str, key: str, label: str = "📥 Скачать исходный текст"):
    """Вспомогательная функция для отрисовки кнопки скачивания"""
    st.download_button(
        label=label,
        data=data,
        file_name=filename,
        mime="text/markdown",
        key=key
    )