import streamlit as st
from huggingface_hub import InferenceClient
from config.constants import PROMPTS, CHARTS_PROMPT, CHAR_LIMIT, MEDIA_EXTENSIONS


def render_ai_analysis_section(task_type: str, file_info: dict, extracted_text: str) -> str:
    st.subheader("✨ Анализ с помощью ИИ")
    st.info(f"📌 Задача: **{task_type}**")
    render_source_caption(file_info)
    st.session_state.generate_charts = st.checkbox(
        "📊 Строить графики по данным из конспекта",
        value=st.session_state.get("generate_charts", True),
        key="charts_checkbox",
    )
    text_for_llm = extracted_text
    if len(text_for_llm) > CHAR_LIMIT:
        st.warning("⚠️ Текст очень большой. Для анализа будет использована только первая часть.")
        text_for_llm = text_for_llm[:CHAR_LIMIT]
    return text_for_llm


def render_source_caption(file_info: dict):
    if file_info.get("ext") in MEDIA_EXTENSIONS:
        st.caption("🎵 Источник: аудио или видеофайл")
    elif file_info.get("ext") == ".youtube":
        st.caption("🌐 Источник: видео с YouTube")


def handle_ai_analysis(
    hf_token: str,
    model_name: str,
    task_type: str,
    text_for_llm: str,
    extracted_text: str,
    button_key: str = "analyze_ai_btn",
) -> str | None:
    if not st.button("🚀 Проанализировать с ИИ", key=button_key):
        return None

    hf_token = hf_token.strip() if hf_token else ""
    if not hf_token:
        st.warning("⚠️ Введите ключ доступа в меню слева.")
        return None
    if not hf_token.startswith("hf_"):
        st.error(
            "❌ Неверный формат ключа API.\n"
            "💡 Убедитесь, что вы используете токен Hugging Face:\n"
            "1. Зайдите на [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)\n"
            "2. Создайте новый токен с правами `read`\n"
            "3. Скопируйте ключ (начинается с `hf_...`)\n"
            "4. Вставьте его в поле 'Ключ доступа' слева"
        )
        return None

    with st.spinner("🤖 Идёт анализ..."):
        try:
            client = InferenceClient(model=model_name, token=hf_token)
            system_prompt = (
                f"Ты ИИ помощник. Думай внимательно, тщательно проверяй свои ответы. "
                f"{PROMPTS[task_type]} Отвечай на русском языке."
            )
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Текст для обработки:\n{text_for_llm}"},
                ],
                max_tokens=10000,
                temperature=0.3,
            )
            result_text = response.choices[0].message.content.strip()
            st.session_state.llm_result = result_text
            _render_result_download(result_text, task_type)
            _render_analysis_info(extracted_text, result_text)
        except Exception as e:
            return _handle_ai_error(e, model_name)

    # Второй запрос — ищем данные для графиков
    with st.spinner("📊 Ищем данные для графиков..."):
        chart_data = _extract_chart_data(hf_token, model_name, result_text)
        st.session_state.chart_data = chart_data

    return st.session_state.llm_result


# =============================================================================
# Извлечение данных для графиков
# =============================================================================

def _extract_chart_data(hf_token: str, model_name: str, result_text: str) -> list:
    """Запрашивает у LLM данные для графиков в компактном pipe-формате."""
    try:
        client = InferenceClient(model=model_name, token=hf_token)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": CHARTS_PROMPT},
                {"role": "user", "content": f"Текст:\n{result_text[:8000]}"},
            ],
            max_tokens=1500,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        return _parse_compact_charts(raw)
    except Exception:
        return []


def _parse_compact_charts(text: str) -> list:
    """Парсит компактный pipe-формат: тип|заголовок|ось_x|ось_y|x-данные|y-данные"""
    charts = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.upper() == "NONE":
            continue
        parts = line.split("|")
        if len(parts) < 6:
            continue
        chart_type = parts[0].strip().lower()
        title = parts[1].strip()
        xlabel = parts[2].strip()
        ylabel = parts[3].strip()
        x_raw = [v.strip() for v in parts[4].split(",") if v.strip()]
        y_raw = [v.strip() for v in parts[5].split(",") if v.strip()]
        if not x_raw or not y_raw or len(x_raw) != len(y_raw):
            continue

        # Пытаемся привести y к числам
        try:
            y_vals = [float(v) for v in y_raw]
        except ValueError:
            y_vals = y_raw

        if chart_type in ("scatter", "line"):
            # Для scatter/line x тоже может быть числами
            try:
                x_vals = [float(v) for v in x_raw]
            except ValueError:
                x_vals = x_raw
            charts.append({"type": chart_type, "title": title,
                           "x": x_vals, "y": y_vals,
                           "xlabel": xlabel, "ylabel": ylabel})

        elif chart_type == "bar":
            charts.append({"type": "bar", "title": title,
                           "x": x_raw, "y": y_vals,
                           "xlabel": xlabel, "ylabel": ylabel})

        elif chart_type == "pie":
            charts.append({"type": "pie", "title": title,
                           "labels": x_raw, "values": y_vals})

        elif chart_type == "timeline":
            events = [{"date": d, "label": l} for d, l in zip(x_raw, y_raw)]
            charts.append({"type": "timeline", "title": title, "events": events})

    return charts


# =============================================================================
# Рендеринг графиков
# =============================================================================

def _render_single_chart(chart: dict, idx: int):
    """Строит один Plotly-график по описанию из LLM."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.warning("Установите plotly: `pip install plotly`")
        return

    chart_type = chart.get("type", "")
    title = chart.get("title", f"График {idx + 1}")

    fig = None

    if chart_type == "bar":
        x = chart.get("x", [])
        y = chart.get("y", [])
        if not x or not y or len(x) != len(y):
            return
        fig = go.Figure(
            go.Bar(x=x, y=y, marker_color="#4C9BE8"),
            layout=go.Layout(
                title=title,
                xaxis_title=chart.get("xlabel", ""),
                yaxis_title=chart.get("ylabel", ""),
            ),
        )

    elif chart_type == "pie":
        labels = chart.get("labels", [])
        values = chart.get("values", [])
        if not labels or not values or len(labels) != len(values):
            return
        fig = go.Figure(
            go.Pie(labels=labels, values=values, hole=0.3),
            layout=go.Layout(title=title),
        )

    elif chart_type == "scatter":
        x = chart.get("x", [])
        y = chart.get("y", [])
        if not x or not y or len(x) != len(y):
            return
        fig = go.Figure(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                marker=dict(size=10, color="#4C9BE8", line=dict(width=1, color="#1a5fa8")),
            ),
            layout=go.Layout(
                title=title,
                xaxis_title=chart.get("xlabel", ""),
                yaxis_title=chart.get("ylabel", ""),
            ),
        )

    elif chart_type == "line":
        x = chart.get("x", [])
        y = chart.get("y", [])
        if not x or not y or len(x) != len(y):
            return
        fig = go.Figure(
            go.Scatter(x=x, y=y, mode="lines+markers", line=dict(color="#4C9BE8", width=2)),
            layout=go.Layout(
                title=title,
                xaxis_title=chart.get("xlabel", ""),
                yaxis_title=chart.get("ylabel", ""),
            ),
        )

    elif chart_type == "timeline":
        events = chart.get("events", [])
        if not events:
            return
        dates = [e.get("date", "") for e in events]
        labels = [e.get("label", "") for e in events]
        fig = go.Figure(
            go.Scatter(
                x=list(range(len(dates))),
                y=[0] * len(dates),
                mode="markers+text",
                text=labels,
                textposition="top center",
                marker=dict(size=14, color="#4C9BE8"),
                customdata=dates,
                hovertemplate="%{customdata}<br>%{text}<extra></extra>",
            ),
            layout=go.Layout(
                title=title,
                xaxis=dict(
                    tickvals=list(range(len(dates))),
                    ticktext=dates,
                    tickangle=-30,
                ),
                yaxis=dict(visible=False),
                height=280,
            ),
        )

    if fig:
        fig.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="#fff"),
            margin=dict(l=20, r=20, t=50, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)


def render_charts(charts: list):
    """Отображает все найденные графики."""
    if not charts:
        return

    st.write("---")
    st.subheader("📊 Графики по данным из текста")

    for idx, chart in enumerate(charts):
        _render_single_chart(chart, idx)


# =============================================================================
# Вспомогательные функции
# =============================================================================

def _handle_ai_error(error: Exception, model_name: str) -> None:
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
    elif "404" in error_msg or "not found" in error_msg or "model" in error_msg:
        st.error(f"❌ Модель `{model_name}` недоступна через API.\n💡 Выберите другую модель в настройках.")
    elif "503" in error_msg or "loading" in error_msg:
        st.warning(f"⚠️ Модель `{model_name}` загружается. Попробуйте через 30-60 секунд.")
    elif "context" in error_msg and "length" in error_msg:
        st.error("❌ Текст слишком длинный для этой модели.\n💡 Попробуйте модель с большим контекстным окном.")
    else:
        st.error(f"❌ Ошибка при обращении к ИИ: {error}")


def _render_result_download(result_text: str, task_type: str):
    st.download_button(
        label="📥 Скачать результат",
        data=result_text,
        file_name=f"summary_{task_type.replace(' ', '_')}.md",
        mime="text/markdown",
        key="download_result_new",
    )


def _render_analysis_info(original_text: str, result_text: str):
    with st.expander("📊 Информация", key="info_expander_new"):
        st.write(f"**Исходный текст:** {len(original_text):,} символов")
        st.write(f"**Результат:** {len(result_text):,} символов")
        if len(original_text) > 0:
            compression = round((1 - len(result_text) / len(original_text)) * 100, 1)
            st.write(f"**Сокращение:** {compression}%")


def _build_download_content(result_text: str, charts: list) -> str:
    """Собирает markdown с текстом конспекта и таблицами данных из графиков."""
    parts = [result_text]
    if charts:
        parts.append("\n\n---\n\n## 📊 Данные графиков\n")
        for chart in charts:
            title = chart.get("title", "График")
            chart_type = chart.get("type", "")
            parts.append(f"\n### {title}\n")

            if chart_type in ("bar", "line", "scatter"):
                x = chart.get("x", [])
                y = chart.get("y", [])
                xlabel = chart.get("xlabel", "X")
                ylabel = chart.get("ylabel", "Y")
                if x and y:
                    parts.append(f"| {xlabel} | {ylabel} |\n|---|---|\n")
                    for xi, yi in zip(x, y):
                        parts.append(f"| {xi} | {yi} |\n")

            elif chart_type == "pie":
                labels = chart.get("labels", [])
                values = chart.get("values", [])
                if labels and values:
                    parts.append("| Категория | Значение |\n|---|---|\n")
                    for label, value in zip(labels, values):
                        parts.append(f"| {label} | {value} |\n")

            elif chart_type == "timeline":
                events = chart.get("events", [])
                if events:
                    parts.append("| Дата | Событие |\n|---|---|\n")
                    for event in events:
                        parts.append(f"| {event.get('date', '')} | {event.get('label', '')} |\n")

    return "".join(parts)


def render_saved_result(task_type: str, user_id: str = None, db_connected: bool = False):
    """Отображает сохранённый результат анализа и графики, если они есть."""
    if not st.session_state.llm_result:
        return

    st.write("---")
    st.success("✅ Результат готов!")
    st.write(st.session_state.llm_result)

    # Графики встроены в конспект — сразу после текста
    charts = st.session_state.get("chart_data") or []
    render_charts(charts)

    # Кнопки скачивания и сохранения
    full_content = _build_download_content(st.session_state.llm_result, charts)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.download_button(
            label="📥 Скачать конспект с данными",
            data=full_content,
            file_name=f"summary_{task_type.replace(' ', '_')}.md",
            mime="text/markdown",
            key="download_result_saved",
        )
    if db_connected and user_id:
        with col2:
            if st.button("Сохранить конспект", key="save_note_btn"):
                from db.user_manager import save_note
                note_name = f"{task_type} — {st.session_state.file_info.get('name', 'без имени')[:30]}"
                try:
                    saved = save_note(user_id, note_name, full_content)
                    if saved:
                        st.success(f"✅ Конспект '{note_name}' сохранён!")
                    else:
                        st.error("❌ Не удалось сохранить конспект.")
                except Exception as e:
                    st.error(f"❌ Ошибка сохранения: {e}")
