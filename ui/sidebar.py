import streamlit as st
from config.constants import PROMPTS


def render_sidebar():
    """Отрисовывает боковую панель с настройками"""
    with st.sidebar:
        hf_token = _render_ai_access()
        model_name = _render_model_selector()
        
        st.write("---")
        task_type = _render_task_selector()
        
        st.write("---")
        whisper_model = _render_whisper_settings()
        
        st.write("---")
        yt_language = _render_youtube_settings()
        
        st.write("---")
        st.caption("🔐 Ваш ключ не сохраняется и используется только в текущей сессии.")
    
    return hf_token, model_name, task_type, whisper_model, yt_language


def _render_ai_access():
    st.header("🔑 Доступ к ИИ")
    return st.text_input(
        "Ключ доступа:",
        type="password",
        help="Получите ключ в настройках вашего аккаунта"
    )


def _render_model_selector():
    return st.selectbox(
        "Модель ИИ:",
        ["Qwen/Qwen2.5-7B-Instruct", "meta-llama/Llama-3.1-8B-Instruct", "ai-forever/ruGPT-3.5"],
        index=0
    )


def _render_task_selector():
    st.header("🎯 Тип задачи")
    return st.selectbox(
        "Что сделать?",
        ["Краткий пересказ", "Подробный конспект", "Тезисы", "План статьи"]
    )


def _render_whisper_settings():
    st.header("🎵 Аудио/Видео")
    return st.selectbox(
        "Качество распознавания:",
        ["tiny", "base", "small", "medium"],
        index=1,
        help="Быстро — для коротких записей, сбалансированно — для лучшего качества"
    )


def _render_youtube_settings():
    st.header("🌐 YouTube")
    return st.selectbox(
        "Язык субтитров:",
        ["ru", "en", "auto"],
        index=0,
        help="Русские, английские или автоматически"
    )
