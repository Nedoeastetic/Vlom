# ui/display.py
import streamlit as st


def show_status_message(status: str):
    """Отображает сообщение статуса с правильным стилем."""
    if status.startswith("✅"):
        st.success(status)
    elif status.startswith("⚠️"):
        st.warning(status)
    elif status.startswith("❌"):
        st.error(status)


def show_extracted_text(text: str, file_info: dict):
    """Отображает извлечённый текст и кнопку скачивания."""
    is_large = file_info.get("size_mb", 0) > 5 or len(text) > 100000
    
    if is_large:
        st.info(f"📁 Текст очень большой. Для удобства предпросмотр отключён.")
        st.download_button(
            label="📥 Скачать исходный текст",
            data=text,
            file_name=f"{file_info['name'].replace(':', '_')}_text.md",
            mime="text/markdown",
            key="download_original_large"
        )
    else:
        with st.expander("📄 Показать извлечённый текст"):
            st.code(text, language="markdown")
        st.download_button(
            label="📥 Скачать исходный текст",
            data=text,
            file_name=f"{file_info['name'].replace(':', '_')}_text.md",
            mime="text/markdown",
            key="download_original_small"
        )


def show_llm_result(result: str, task_type: str, original_text: str):
    """Отображает результат ИИ-анализа."""
    st.write("---")
    st.success("✅ Результат готов!")
    st.write(result)
    st.download_button(
        label="📥 Скачать результат",
        data=result,
        file_name=f"summary_{task_type.replace(' ', '_')}.md",
        mime="text/markdown",
        key="download_result_saved"
    )
    
    with st.expander("📊 Информация", key="info_expander_new"):
        st.write(f"**Исходный текст:** {len(original_text):,} символов")
        st.write(f"**Результат:** {len(result):,} символов")
        if len(original_text) > 0:
            compression = round((1 - len(result)/len(original_text)) * 100, 1)
            st.write(f"**Сокращение:** {compression}%")