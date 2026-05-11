import streamlit as st
from huggingface_hub import InferenceClient
from config.constants import PROMPTS, CHAR_LIMIT, MEDIA_EXTENSIONS
from config.token_manager import token_manager  # 🔹 ИМПОРТ МЕНЕДЖЕРА ТОКЕНОВ


def render_ai_analysis_section(task_type: str, file_info: dict, extracted_text: str) -> str:
    """
    Отрисовывает секцию анализа с помощью ИИ.
    
    Возвращает:
        str: Текст, подготовленный для отправки в ИИ (возможно, обрезанный)
    """
    st.subheader("✨ Анализ с помощью ИИ")
    st.info(f"📌 Задача: **{task_type}**")
    
    # Показываем подпись об источнике
    render_source_caption(file_info)
    
    # Обрезаем текст, если он слишком большой для контекстного окна
    text_for_llm = extracted_text
    if len(text_for_llm) > CHAR_LIMIT:
        st.warning(f"⚠️ Текст очень большой. Для анализа будет использована только первая часть.")
        text_for_llm = text_for_llm[:CHAR_LIMIT]
    
    return text_for_llm


def render_source_caption(file_info: dict):
    """Отображает подпись об источнике данных"""
    if file_info.get("ext") in MEDIA_EXTENSIONS:
        st.caption("🎵 Источник: аудио или видеофайл")
    elif file_info.get("ext") == ".youtube":
        st.caption("🌐 Источник: видео с YouTube")


def handle_ai_analysis(
    hf_token: str,  # 🔹 Теперь этот параметр игнорируется (токены берутся из token_manager)
    model_name: str,
    task_type: str,
    text_for_llm: str,
    extracted_text: str,
    button_key: str = "analyze_ai_btn"
) -> str | None:
    """
    Обрабатывает нажатие кнопки анализа ИИ.
    Автоматически ротирует токены при ошибке 429.
    """
    if not st.button("🚀 Проанализировать с ИИ", key=button_key):
        return None
    
    # 🔹 Проверяем наличие токенов в системе (вместо проверки hf_token)
    if not token_manager.is_configured():
        st.error(
            "❌ Токены Hugging Face не настроены.\n\n"
            "💡 Добавьте в файл `.env`:\n"
            "```\n"
            "HF_TOKEN_1=hf_ваш_первый_токен\n"
            "HF_TOKEN_2=hf_ваш_второй_токен\n"
            "```"
        )
        return None
    
    with st.spinner("🤖 Идёт анализ..."):
        max_retries = len(token_manager.tokens)  # Пробуем каждый токен один раз
        
        for attempt in range(max_retries):
            current_token = token_manager.get_token()
            
            if not current_token:
                st.error("❌ Не удалось получить токен")
                return None
            
            try:
                # 🔹 Создаем клиент с текущим токеном из пула
                client = InferenceClient(
                    model=model_name,
                    token=current_token.strip()  # 🔹 .strip() на всякий случай
                )
                
                system_prompt = (
                    f"Ты ИИ помощник. Думай внимательно, тщательно проверяй свои ответы. "
                    f"{PROMPTS[task_type]} Отвечай на русском языке."
                )
                
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Текст для обработки:\n\n{text_for_llm}"}
                    ],
                    max_tokens=10000,
                    temperature=0.3
                )
                
                result_text = response.choices[0].message.content.strip()
                st.session_state.llm_result = result_text
                
                # Отрисовка кнопок и информации
                _render_result_download(result_text, task_type)
                _render_analysis_info(extracted_text, result_text)
                
                return result_text
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # 🔹 Если 429 (rate limit) — ротируем токен и пробуем снова
                if "429" in error_msg or "rate limit" in error_msg or "too many requests" in error_msg:
                    if attempt < max_retries - 1:
                        token_manager.rotate_token(reason="Rate limit 429")
                        # Не показываем пользователю, просто пробуем следующий токен
                        continue
                    else:
                        st.error("❌ Все токены исчерпали лимит. Попробуйте через 1-2 минуты.")
                        return None
                else:
                    # Другие ошибки — не ротируем, просто показываем
                    return _handle_ai_error(e, model_name)
        
        st.error("❌ Не удалось выполнить запрос после всех попыток")
        return None


def _handle_ai_error(error: Exception, model_name: str) -> None:
    """Обрабатывает и отображает ошибки обращения к ИИ"""
    error_msg = str(error).lower()
    
    if "auto-router" in error_msg:
        st.error(
            "❌ Ошибка маршрутизации запроса.\n"
            "💡 Попробуйте:\n"
            "1. Проверить, что ключ начинается с `hf_`\n"
            "2. Выбрать другую модель из списка (не все модели доступны через API)\n"
            "3. Убедиться, что у токена есть права `read`"
        )
    elif "401" in error_msg or "unauthorized" in error_msg or "invalid token" in error_msg:
        st.error("❌ Неверный токен. Проверьте ключ доступа в настройках аккаунта Hugging Face.")
    elif "429" in error_msg or "rate limit" in error_msg or "too many requests" in error_msg:
        st.warning("⚠️ Превышен лимит запросов. Попробуйте через минуту или используйте другую модель.")
    # 🔹 Исправлено: проверяем точную фразу "model_not_supported", а не просто "model"
    elif "model_not_supported" in error_msg or ("404" in error_msg and "not found" in error_msg):
        st.error(f"❌ Модель `{model_name}` недоступна через API.\n💡 Выберите другую модель в настройках.")
    elif "503" in error_msg or "loading" in error_msg:
        st.warning(f"⚠️ Модель `{model_name}` загружается. Попробуйте через 30-60 секунд.")
    elif "context" in error_msg and "length" in error_msg:
        st.error("❌ Текст слишком длинный для этой модели.\n💡 Попробуйте модель с большим контекстным окном.")
    else:
        st.error(f"❌ Ошибка при обращении к ИИ: {error}")


def _render_result_download(result_text: str, task_type: str):
    """Отрисовывает кнопку скачивания результата"""
    st.download_button(
        label="📥 Скачать результат",
        data=result_text,
        file_name=f"summary_{task_type.replace(' ', '_')}.md",
        mime="text/markdown",
        key="download_result_new"
    )


def _render_analysis_info(original_text: str, result_text: str):
    """Отрисовывает блок с информацией об анализе"""
    with st.expander("📊 Информация", key="info_expander_new"):
        st.write(f"**Исходный текст:** {len(original_text):,} символов")
        st.write(f"**Результат:** {len(result_text):,} символов")
        if len(original_text) > 0:
            compression = round((1 - len(result_text) / len(original_text)) * 100, 1)
            st.write(f"**Сокращение:** {compression}%")


def render_saved_result(task_type: str, user_id: str = None, db_connected: bool = False):
    """
    Отображает сохранённый результат анализа, если он есть в session_state.
    (Версия из кода 1: с колонками для кнопок)
    """
    if not st.session_state.llm_result:
        return

    st.write("---")
    st.success("✅ Результат готов!")
    st.write(st.session_state.llm_result)

    # 🔹 Оригинальная логика из кода 1: кнопки в две колонки
    col1, col2 = st.columns([3, 1])
    with col1:
        st.download_button(
            label="📥 Скачать результат",
            data=st.session_state.llm_result,
            file_name=f"summary_{task_type.replace(' ', '_')}.md",
            mime="text/markdown",
            key="download_result_saved"
        )
    
    if db_connected and user_id:
        with col2:
            if st.button("Сохранить конспект", key="save_note_btn"):
                from db.user_manager import save_note
                note_name = f"{task_type} — {st.session_state.file_info.get('name', 'без имени')[:30]}"
                try:
                    saved = save_note(user_id, note_name, st.session_state.llm_result)
                    if saved:
                        st.success(f"✅ Конспект '{note_name}' сохранён!")
                    else:
                        st.error("❌ Не удалось сохранить конспект.")
                except Exception as e:
                    st.error(f"❌ Ошибка сохранения: {e}")