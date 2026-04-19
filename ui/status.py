import streamlit as st


def render_processing_status(status: str):
    """Отображает статус обработки с соответствующим стилем"""
    if not status:
        return
    
    if status.startswith("✅"):
        st.success(status)
    elif status.startswith("⚠️"):
        st.warning(status)
    elif status.startswith("❌"):
        st.error(status)