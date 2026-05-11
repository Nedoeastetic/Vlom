import streamlit as st
from huggingface_hub import InferenceClient
from config.constants import PROMPTS, CHAR_LIMIT, MEDIA_EXTENSIONS
from config.token_manager import token_manager  # 🔹 ИМПОРТ МЕНЕДЖЕРА







def render_ai_analysis_section(task_type: str, file_info: dict, extracted_text: str) -> str:
    """
    Отрисовывает секцию анализа с помощью ИИ.
    
    Возвращает:
        str: Текст, подготовленный для отправки в ИИ (возможно, обрезанный)
    """
    st.subheader("✨ Анализ с помощью ИИ")
    st.info(f"📌 Задача: **{task_type}**")
    
    # 🔹 Показываем статус токенов (только для отладки, можно убрать)
    # if token_manager.is_configured():
    #     stats = token_manager.get_stats()
    #     st.caption(f"🔑 Токенов в пуле: {stats['total']}")
    
    render_source_caption(file_info)
    
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
    hf_tokenР: str,  # 🔹 Теперь этот параметр игнорируется (всегда None)
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
    
    

    # 🔹 Проверяем наличие токенов в системе
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
            if current_token:
                current_token = current_token.strip()  # 🔹 Убираем случайные пробелы
            
            if not current_token:
                st.error("❌ Не удалось получить токен")
                return None
            
            try:
                client = InferenceClient(
                    model=model_name,
                    token=current_token
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
    error_msg = str(error)
    error_lower = error_msg.lower()
    
    # 🔹 ПОКАЗЫВАЕМ ПОЛНУЮ ОШИБКУ ДЛЯ ОТЛАДКИ
    st.error(f"🔍 Полная ошибка: {error_msg[:300]}...")
    
    if "model_not_supported" in error_lower:
        st.error(f"❌ Модель `{model_name}` НЕ ПОДДЕРЖИВАЕТСЯ через Inference API")
        st.info("💡 Попробуйте: `mistralai/Mistral-7B-Instruct-v0.2`")
        
    elif "404" in error_lower and "not found" in error_lower:
        st.error(f"❌ Модель `{model_name}` не найдена (404)")
        st.info("💡 Проверьте название модели на huggingface.co")
        
    elif "403" in error_lower or "forbidden" in error_lower:
        st.error("❌ Ошибка 403: недостаточно прав у токена")
        st.info("💡 Убедитесь, что токен имеет права 'read' и вы запросили доступ к модели")
        
    elif "401" in error_lower or "unauthorized" in error_lower:
        st.error("❌ Ошибка 401: неверный токен")
        st.info("💡 Проверьте токены в .env")
        
    elif "429" in error_lower or "rate limit" in error_lower:
        st.warning("⚠️ Превышен лимит запросов. Система попробует другой токен...")
        
    elif "503" in error_lower or "loading" in error_lower:
        st.warning(f"⚠️ Модель загружается. Попробуйте через 30-60 секунд.")
        
    elif "connection" in error_lower or "timeout" in error_lower or "network" in error_lower:
        st.error("❌ Ошибка сети. Проверьте интернет-соединение.")
        
    else:
        # 🔹 Для неизвестных ошибок — показываем больше деталей
        st.error(f"❌ Неизвестная ошибка: {type(error).__name__}")
        with st.expander("🔧 Детали ошибки (для разработчика)"):
            st.code(error_msg)

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
    """
    if not st.session_state.llm_result:
        return

    st.write("---")
    st.success("✅ Результат готов!")
    st.write(st.session_state.llm_result)

    st.download_button(
        label="📥 Скачать результат",
        data=st.session_state.llm_result,
        file_name=f"summary_{task_type.replace(' ', '_')}.md",
        mime="text/markdown",
        key="download_result_saved",
    )
    if db_connected and user_id:
        st.write("")
        default_name = f"{task_type} — {st.session_state.file_info.get('name', 'без имени')[:40]}"
        note_name = st.text_input(
            "Название конспекта",
            value=default_name,
            max_chars=80,
            key="note_name_input",
        )
        if st.button("Сохранить конспект", key="save_note_btn"):
            from db.user_manager import save_note
            name = note_name.strip() or default_name
            try:
                saved = save_note(user_id, name, st.session_state.llm_result)
                if saved:
                    st.success(f"✅ Конспект «{name}» сохранён!")
                else:
                    st.error("❌ Не удалось сохранить конспект.")
            except Exception as e:
                st.error(f"❌ Ошибка сохранения: {e}")