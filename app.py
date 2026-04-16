import streamlit as st
import tempfile
import os
import sys
import re
import json
import urllib.request
from markitdown import MarkItDown
from huggingface_hub import InferenceClient

# =============================================================================
# 🔧 НАСТРОЙКА FFmpeg
# =============================================================================
def get_ffmpeg_path():
    """Возвращает полный путь к ffmpeg бинарнику"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        return None

def setup_ffmpeg_env():
    """Добавляет ffmpeg в PATH для subprocess-вызовов"""
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path:
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        current_path = os.environ.get("PATH", "")
        if ffmpeg_dir not in current_path:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path
        return True
    return False

# Вызываем при старте
setup_ffmpeg_env()
FFMPEG_PATH = get_ffmpeg_path()

# =============================================================================
# 🎤 ТРАНСКРИПЦИЯ АУДИО/ВИДЕО
# =============================================================================
def transcribe_media(file_path: str, model_size: str = "base") -> str:
    """
    Транскрибирует аудио/видео файл.
    Поддерживает: .wav, .mp3, .m4a, .mp4, .mkv, .avi, .mov, .flv
    """
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, info = model.transcribe(file_path, beam_size=1, language="ru")
        text = " ".join([segment.text.strip() for segment in segments])
        return text if text else "⚠️ Речь не распознана"
    except ImportError:
        return "❌ Функция распознавания речи временно недоступна"
    except Exception as e:
        return f"❌ Не удалось распознать речь: {e}"

# =============================================================================
# 📄 ИЗВЛЕЧЕНИЕ ТЕКСТА ИЗ ДОКУМЕНТОВ
# =============================================================================
def extract_from_document(file_path: str, file_ext: str) -> str:
    """Извлекает текст из документов: pdf, docx, pptx, xlsx, msg"""
    try:
        md = MarkItDown()
        result = md.convert(file_path)
        return result.text_content or "⚠️ Текст не извлечён"
    except Exception as e:
        return f"❌ Не удалось обработать документ: {e}"

# =============================================================================
# 🌐 YOUTUBE: ПОЛУЧЕНИЕ СУБТИТРОВ
# =============================================================================
def get_youtube_transcript_ytdlp(video_url: str, language: str = "ru") -> str:
    """
    Получает субтитры с YouTube.
    Правильно парсит JSON и VTT форматы.
    """
    try:
        import yt_dlp
        
        # Извлекаем ID видео
        video_id = extract_video_id(video_url)
        if not video_id:
            return "❌ Не удалось извлечь ID видео из ссылки"
        
        # Настройки для получения информации о субтитрах
        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            if not info:
                return "❌ Не удалось получить информацию о видео"
            
            # Проверяем доступные субтитры
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            
            if not subtitles and not automatic_captions:
                return "❌ Для этого видео нет доступных субтитров\n\n💡 Попробуйте скачать аудио и обработать его как файл"
            
            # Пытаемся получить нужный язык
            caption_url = None
            subs_lang = language if language != 'auto' else 'ru'
            
            # Приоритет: ручные субтитры → авто → английский
            for lang in [subs_lang, 'en', 'en-US', 'ru-RU']:
                if lang in subtitles:
                    for sub in subtitles[lang]:
                        if sub.get('ext') == 'vtt':
                            caption_url = sub.get('url')
                            break
                    if caption_url:
                        break
            
            # Если ручных нет, пробуем авто
            if not caption_url:
                for lang in [subs_lang, 'en', 'en-US']:
                    if lang in automatic_captions:
                        for sub in automatic_captions[lang]:
                            if sub.get('ext') in ['vtt', 'json3', 'srv3']:
                                caption_url = sub.get('url')
                                break
                        if caption_url:
                            break
            
            if not caption_url:
                available_langs = list(subtitles.keys()) + list(automatic_captions.keys())
                return f"❌ Субтитры на языке '{subs_lang}' не найдены\n\n💡 Доступные языки: {', '.join(available_langs[:5])}"
            
            # Скачиваем субтитры
            with urllib.request.urlopen(caption_url) as response:
                raw_content = response.read().decode('utf-8')
            
            # Определяем формат и парсим
            if raw_content.strip().startswith('{'):
                # JSON формат
                text = parse_json_subtitles(raw_content)
            else:
                # VTT формат
                text = clean_vtt(raw_content)
            
            return text if text.strip() else "⚠️ Субтитры пустые"
            
    except ImportError:
        return "❌ Функция работы с YouTube временно недоступна"
    except Exception as e:
        return f"❌ Не удалось получить данные с YouTube: {e}"


def parse_json_subtitles(json_text: str) -> str:
    """
    Парсит JSON-субтитры YouTube.
    Извлекает только текст, игнорируя таймкоды и метаданные.
    """
    try:
        data = json.loads(json_text)
        text_lines = []
        
        # Формат srv3: events → segs → utf8
        events = data.get('events', [])
        for event in events:
            segs = event.get('segs', [])
            for seg in segs:
                utf8_text = seg.get('utf8', '')
                if utf8_text and utf8_text.strip():
                    # Очищаем от лишних символов
                    cleaned = utf8_text.strip()
                    if cleaned != '\n':
                        text_lines.append(cleaned)
        
        # Собираем текст
        result = ' '.join(text_lines)
        
        # Убираем двойные пробелы и чистим
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
        
    except json.JSONDecodeError:
        return "❌ Не удалось распарсить данные субтитров"
    except Exception as e:
        return f"❌ Ошибка обработки данных: {e}"


def clean_vtt(vtt_text: str) -> str:
    """Очищает VTT-субтитры от таймкодов и тегов"""
    lines = vtt_text.split('\n')
    clean_lines = []
    in_header = True
    
    for line in lines:
        # Пропускаем заголовок VTT
        if line.strip() == 'WEBVTT' or line.strip().startswith('Kind:') or line.strip().startswith('Language:'):
            continue
        if in_header and line.strip() == '':
            in_header = False
            continue
        if in_header:
            continue
        
        # Пропускаем таймкоды
        if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3}', line.strip()):
            continue
        
        # Пропускаем номера позиций
        if re.match(r'^\d+$', line.strip()):
            continue
        
        # Удаляем HTML-теги
        line = re.sub(r'<[^>]+>', '', line)
        
        # Удаляем служебные символы VTT
        line = re.sub(r'NOTE.*', '', line)
        line = re.sub(r'STYLE.*', '', line)
        
        if line.strip():
            clean_lines.append(line.strip())
    
    return ' '.join(clean_lines)


def extract_video_id(url: str) -> str:
    """Извлекает ID видео из YouTube URL"""
    patterns = [
        r'(?:v=|/)([a-zA-Z0-9_-]{11})(?:\?|&|/|$)',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'embed/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""

# =============================================================================
# 🌐 ИНТЕРФЕЙС: НАСТРОЙКА И ХРАНЕНИЕ ДАННЫХ
# =============================================================================
st.set_page_config(page_title="Анализатор документов", page_icon="📄", layout="centered")
st.title("📄 Универсальный анализатор документов")
st.write("Загрузите файл (PDF, Word, Excel, аудио или видео) или ссылку на YouTube, чтобы получить краткое содержание с помощью ИИ.")

# 🔹 ИНИЦИАЛИЗАЦИЯ ХРАНЕНИЯ ДАННЫХ (сохраняет данные между обновлениями страницы)
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = None
if "file_info" not in st.session_state:
    st.session_state.file_info = None
if "processing_status" not in st.session_state:
    st.session_state.processing_status = None
if "llm_result" not in st.session_state:
    st.session_state.llm_result = None
if "youtube_url" not in st.session_state:
    st.session_state.youtube_url = ""

# =============================================================================
# ⚙️ БОКОВАЯ ПАНЕЛЬ
# =============================================================================
with st.sidebar:
    st.header("🔑 Доступ к ИИ")
    hf_token = st.text_input("Ключ доступа:", type="password", 
                             help="Получите ключ в настройках вашего аккаунта")
    
    model_name = st.selectbox(
        "Модель ИИ:",
        ["Qwen/Qwen2.5-7B-Instruct", "meta-llama/Llama-3.1-8B-Instruct", "ai-forever/ruGPT-3.5"],
        index=0
    )
    
    st.write("---")
    st.header("🎯 Тип задачи")
    task_type = st.selectbox(
        "Что сделать?",
        ["Краткий пересказ", "Подробный конспект", "Тезисы", "План статьи"]
    )
    
    prompts = {
        "Краткий пересказ": "Сделай краткий пересказ текста на русском. Выдели 3-5 главных мыслей.",
        "Подробный конспект": "Сделай подробный конспект текста с разделами и подпунктами. Сохрани важную информацию.",
        "Тезисы": "Выдели основные тезисы текста в виде маркированного списка. Только ключевые утверждения.",
        "План статьи": "Составь структурированный план статьи с разделами и подразделами."
    }
    
    st.write("---")
    st.header("🎵 Аудио/Видео")
    whisper_model = st.selectbox(
        "Качество распознавания:",
        ["tiny", "base", "small", "medium"],
        index=1,
        help="Быстро — для коротких записей, сбалансированно — для лучшего качества"
    )
    
    st.write("---")
    st.header("🌐 YouTube")
    yt_language = st.selectbox(
        "Язык субтитров:",
        ["ru", "en", "auto"],
        index=0,
        help="Русские, английские или автоматически"
    )
    
    st.write("---")
    st.caption("🔐 Ваш ключ не сохраняется и используется только в текущей сессии.")

# =============================================================================
# 🗑️ КНОПКА ОЧИСТКИ ДАННЫХ (на основной странице)
# =============================================================================
if st.session_state.extracted_text or st.session_state.youtube_url:
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Очистить всё", key="clear_all_btn"):
            st.session_state.extracted_text = None
            st.session_state.file_info = None
            st.session_state.processing_status = None
            st.session_state.llm_result = None
            st.session_state.youtube_url = ""
            st.rerun()
    st.write("")  # Отступ

# =============================================================================
# 📁 ЗАГРУЗКА ФАЙЛА
# =============================================================================
DOC_EXTENSIONS = ["pdf", "docx", "pptx", "xlsx", "xls", "msg"]
MEDIA_EXTENSIONS = ["wav", "mp3", "m4a", "mp4", "mkv", "avi", "mov", "flv"]
ALL_EXTENSIONS = DOC_EXTENSIONS + MEDIA_EXTENSIONS

uploaded_file = st.file_uploader("📎 Прикрепите файл", type=ALL_EXTENSIONS, key="file_uploader_main")

# =============================================================================
# 🔗 YOUTUBE: ОТДЕЛЬНЫЙ ВИДЖЕТ
# =============================================================================
st.write("---")
st.subheader("🔗 Или обработайте видео с YouTube")
with st.form("youtube_form"):
    youtube_url = st.text_input(
        "Ссылка на YouTube:",
        value=st.session_state.youtube_url,
        placeholder="https://www.youtube.com/watch?v=...  ",
        key="youtube_url_input"
    )
    yt_submit = st.form_submit_button("🚀 Получить текст из видео")

# Сохраняем введённую ссылку в session_state для возможности очистки
if youtube_url != st.session_state.youtube_url:
    st.session_state.youtube_url = youtube_url

# =============================================================================
# 🔄 ОБРАБОТКА (только если нет сохранённых данных)
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
    
    # 🔹 СОХРАНЯЕМ В ХРАНИЛИЩЕ
    st.session_state.extracted_text = extracted_text
    st.session_state.file_info = file_info
    st.session_state.processing_status = processing_status

# --- Обработка YouTube ---
elif yt_submit and youtube_url and not st.session_state.extracted_text:
    if "youtube.com" in youtube_url or "youtu.be" in youtube_url:
        video_id = extract_video_id(youtube_url)
        if video_id:
            file_info = {"name": f"YouTube: {video_id}", "size_mb": 0, "ext": ".youtube", "source": "youtube"}
            
            with st.spinner("🌐 Получаем текст видео с YouTube..."):
                extracted_text = get_youtube_transcript_ytdlp(youtube_url, language=yt_language if yt_language != "auto" else "ru")
                
                if extracted_text.startswith("❌") or extracted_text.startswith("⚠️"):
                    processing_status = extracted_text
                else:
                    processing_status = "✅ Текст видео получен!"
            
            # 🔹 СОХРАНЯЕМ В ХРАНИЛИЩЕ
            st.session_state.extracted_text = extracted_text
            st.session_state.file_info = file_info
            st.session_state.processing_status = processing_status
        else:
            st.error("❌ Не удалось извлечь ID видео из ссылки")
    else:
        st.error("❌ Это не ссылка на YouTube")

# --- Показ статуса ---
if processing_status:
    if processing_status.startswith("✅"):
        st.success(processing_status)
    elif processing_status.startswith("⚠️"):
        st.warning(processing_status)
    elif processing_status.startswith("❌"):
        st.error(processing_status)

# =============================================================================
# 📊 ОТОБРАЖЕНИЕ РЕЗУЛЬТАТА
# =============================================================================
if extracted_text and not extracted_text.startswith("❌"):
    st.subheader("📋 Доступные действия")
    
    is_large = file_info.get("size_mb", 0) > 5 or len(extracted_text) > 100000
    
    if is_large:
        st.info(f"📁 Текст очень большой. Для удобства предпросмотр отключён.")
        st.download_button(
            label="📥 Скачать исходный текст",
            data=extracted_text,
            file_name=f"{file_info['name'].replace(':', '_')}_text.md",
            mime="text/markdown",
            key="download_original_large"
        )
    else:
        with st.expander("📄 Показать извлечённый текст"):
            st.code(extracted_text, language="markdown")
        st.download_button(
            label="📥 Скачать исходный текст",
            data=extracted_text,
            file_name=f"{file_info['name'].replace(':', '_')}_text.md",
            mime="text/markdown",
            key="download_original_small"
        )
    
    st.write("---")
    
    # =============================================================================
    # 🤖 АНАЛИЗ С ПОМОЩЬЮ ИИ
    # =============================================================================
    st.subheader("✨ Анализ с помощью ИИ")
    st.info(f"📌 Задача: **{task_type}**")
    
    if file_info.get("ext") in MEDIA_EXTENSIONS:
        st.caption("🎵 Источник: аудио или видеофайл")
    elif file_info.get("ext") == ".youtube":
        st.caption("🌐 Источник: видео с YouTube")
    
    CHAR_LIMIT = 40000
    text_for_llm = extracted_text
    if len(text_for_llm) > CHAR_LIMIT:
        st.warning(f"⚠️ Текст очень большой. Для анализа будет использована только первая часть.")
        text_for_llm = text_for_llm[:CHAR_LIMIT]
    
    if st.button("🚀 Проанализировать с ИИ", key="analyze_ai_btn"):
        if not hf_token:
            st.warning("⚠️ Введите ключ доступа в меню слева.")
        else:
            with st.spinner("🤖 Идёт анализ..."):
                try:
                    client = InferenceClient(model=model_name, token=hf_token)
                    system_prompt = f"Ты ИИ помощник. Думай внимательно, тщательно проверяй свои ответы. {prompts[task_type]} Отвечай на русском языке."
                    
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Текст для обработки:\n\n{text_for_llm}"}
                        ],
                        max_tokens=10000,
                        temperature=0.3
                    )
                    
                    result_text = response.choices[0].message.content.strip()
                    
                    # 🔹 СОХРАНЯЕМ РЕЗУЛЬТАТ В ХРАНИЛИЩЕ
                    st.session_state.llm_result = result_text
                    
                    st.download_button(
                        label="📥 Скачать результат",
                        data=result_text,
                        file_name=f"summary_{task_type.replace(' ', '_')}.md",
                        mime="text/markdown",
                        key="download_result_new"
                    )
                    
                    with st.expander("📊 Информация", key="info_expander_new"):
                        st.write(f"**Исходный текст:** {len(extracted_text):,} символов")
                        st.write(f"**Результат:** {len(result_text):,} символов")
                        if len(extracted_text) > 0:
                            compression = round((1 - len(result_text)/len(extracted_text)) * 100, 1)
                            st.write(f"**Сокращение:** {compression}%")
                    
                except Exception as e:
                    st.error(f"❌ Ошибка при обращении к ИИ: {e}")

    # =============================================================================
    # 🔹 ПОКАЗ СОХРАНЁННОГО РЕЗУЛЬТАТА (если есть)
    # =============================================================================
    if st.session_state.llm_result:
        st.write("---")
        st.success("✅ Результат готов!")
        st.write(st.session_state.llm_result)
        st.download_button(
            label="📥 Скачать результат",
            data=st.session_state.llm_result,
            file_name=f"summary_{task_type.replace(' ', '_')}.md",
            mime="text/markdown",
            key="download_result_saved"
        )

# =============================================================================
# 💡 СПРАВКА ПО ФОРМАТАМ
# =============================================================================
with st.expander("💡 Справка по форматам", key="help_expander"):
    st.markdown("""
    **📄 Документы:** `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.msg`
    
    **🎵 Аудио и видео:** `.wav`, `.mp3`, `.m4a`, `.mp4`, `.mkv`, `.avi`
    
    **🌐 YouTube:**
    - Автоматически извлекает доступные субтитры
    - Видео должно иметь субтитры (вручную добавленные или автоматические)
    - Если субтитров нет — скачайте аудио с видео и загрузите его как файл
    
    **⚡ Советы:**
    - Для анализа используется часть текста, чтобы ускорить обработку
    - Быстрый режим — для коротких записей, сбалансированный — для лучшего качества
    
    **💾 Работа с данными:**
    - Текст и результаты сохраняются, пока вы находитесь на странице
    - Кнопка "Очистить всё" удаляет всю информацию и сбрасывает форму YouTube
    """)