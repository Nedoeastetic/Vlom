# 🔧 НАСТРОЙКА FFmpeg — ДО ВСЕХ ИМПОРТОВ!
# =============================================================================
import os
import sys

def setup_ffmpeg_path():
    """Добавляет ffmpeg в PATH до импорта любых библиотек"""
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
        return True
    except Exception as e:
        print(f"⚠️ Warning: ffmpeg not found: {e}")
        return False

# 🔹 ВЫЗЫВАЕМ ПЕРЕД ВСЕМ ОСТАЛЬНЫМ!
setup_ffmpeg_path()

# =============================================================================
# 📦 ТЕПЕРЬ ИМПОРТИРУЕМ ВСЁ ОСТАЛЬНОЕ
# =============================================================================
import streamlit as st
import tempfile
import re
import json
import urllib.request
from markitdown import MarkItDown
from huggingface_hub import InferenceClient

# Импорт модулей проекта
from utils.ffmpeg_setup import setup_ffmpeg_env, get_ffmpeg_path
from services.transcription import transcribe_media
from services.document_extractor import extract_from_document
from services.youtube_service import get_youtube_transcript_ytdlp, extract_video_id
from config.constants import DOC_EXTENSIONS, MEDIA_EXTENSIONS, PROMPTS, CHAR_LIMIT

# Импорт UI-модулей
from ui import (
    setup_page,
    init_session_state,
    render_sidebar,
    render_file_uploader,
    render_youtube_form,
    handle_youtube_submit,
    render_cleanup_button,
    render_processing_status,
    render_extracted_text,
    render_source_caption,
    render_ai_analysis_section,
    handle_ai_analysis,
    render_saved_result,
    render_help_expander,
    render_rutube_vk_help,
)

# =============================================================================
# 🔧 ИНИЦИАЛИЗАЦИЯ
# =============================================================================
setup_ffmpeg_env()
FFMPEG_PATH = get_ffmpeg_path()

setup_page()
init_session_state()

# =============================================================================
# ⚙️ ОТРИСОВКА ИНТЕРФЕЙСА
# =============================================================================
hf_token, model_name, task_type, whisper_model, yt_language = render_sidebar()

render_cleanup_button()

uploaded_file = render_file_uploader()

youtube_url, yt_submitted = render_youtube_form(st.session_state.youtube_url)
handle_youtube_submit(youtube_url, st.session_state.youtube_url)

# =============================================================================
# 🔄 ЛОГИКА ОБРАБОТКИ
# =============================================================================
extracted_text = st.session_state.extracted_text
file_info = st.session_state.file_info
processing_status = st.session_state.processing_status

# --- Обработка загруженного файла ---
if uploaded_file is not None and not st.session_state.extracted_text:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower().lstrip(".")
    file_size_mb = uploaded_file.size / (1024 * 1024)
    file_info = {"name": uploaded_file.name, "size_mb": file_size_mb, "ext": file_ext, "source": "file"}
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    
    try:
        if file_ext in MEDIA_EXTENSIONS:
            with st.spinner(f"🎤 Распознаём речь в файле..."):
                extracted_text = transcribe_media(tmp_path, model_size=whisper_model)
                processing_status = "✅ Распознавание завершено!" if not extracted_text.startswith("❌") else extracted_text
        elif file_ext in DOC_EXTENSIONS:
            with st.spinner(f"📄 Обрабатываем документ..."):
                extracted_text = extract_from_document(tmp_path, file_ext)
                processing_status = "✅ Текст получен!" if not extracted_text.startswith("❌") else extracted_text
        else:
            processing_status = f"❌ Формат .{file_ext} не поддерживается"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    
    st.session_state.extracted_text = extracted_text
    st.session_state.file_info = file_info
    st.session_state.processing_status = processing_status

# --- Обработка YouTube ---
elif yt_submitted and youtube_url and not st.session_state.extracted_text:
    if "youtube.com" in youtube_url or "youtu.be" in youtube_url:
        video_id = extract_video_id(youtube_url)
        if video_id:
            file_info = {"name": f"YouTube: {video_id}", "size_mb": 0, "ext": ".youtube", "source": "youtube"}
            
            with st.spinner("🌐 Получаем текст видео с YouTube..."):
                extracted_text = get_youtube_transcript_ytdlp(
                    youtube_url,
                    language=yt_language if yt_language != "auto" else "ru"
                )
                
                if extracted_text.startswith("❌") or extracted_text.startswith("⚠️"):
                    processing_status = extracted_text
                else:
                    processing_status = "✅ Текст видео получен!"
            
            st.session_state.extracted_text = extracted_text
            st.session_state.file_info = file_info
            st.session_state.processing_status = processing_status
        else:
            st.error("❌ Не удалось извлечь ID видео из ссылки")
    else:
        st.error("❌ Это не ссылка на YouTube")

# --- Показ статуса ---
render_processing_status(processing_status)

# =============================================================================
# 📊 ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ
# =============================================================================
if extracted_text and not extracted_text.startswith("❌"):
    render_extracted_text(extracted_text, file_info)
    render_source_caption(file_info)
    
    # =============================================================================
    # 🤖 АНАЛИЗ С ПОМОЩЬЮ ИИ
    # =============================================================================
    text_for_llm = render_ai_analysis_section(task_type, file_info, extracted_text)
    handle_ai_analysis(hf_token, model_name, task_type, text_for_llm, extracted_text)
    render_saved_result(task_type)

# =============================================================================
# 💡 СПРАВКА
# =============================================================================
render_help_expander()
render_rutube_vk_help()