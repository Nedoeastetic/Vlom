import streamlit as st

def render_saved_result(task_type):
    """Отображает результат с возможностью редактирования и скачивания"""

    if not st.session_state.get("llm_result"):
        return

    st.write("---")
    st.success("✅ Результат готов!")

    # режим просмотра
    if not st.session_state.edit_mode:
        st.markdown(f"""
        <style>
        .formatted-text {{
            font-size: {st.session_state.font_size}px;
            font-family: {st.session_state.font_family};
            color: {st.session_state.font_color};  # ← Добавлен #
            line-height: 1.6;
            padding: 20px;
        }}
        </style>
        <div class="formatted-text">
            {st.session_state.llm_result.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Редактировать конспект", key="btn_show_edit_panel", use_container_width=True):
                st.session_state.edit_mode = True
                st.rerun()
        with col2:
            st.download_button(
                label="📥 Скачать результат (TXT)",
                data=st.session_state.llm_result,
                file_name=f"summary_{task_type.replace(' ', '_')}.txt",
                mime="text/plain",
                key="download_result_txt_view"
            )

    # Режим редактирования
    else:
        with st.container(border=True):
            st.markdown("#### 🎨 Настройки форматирования")
            col_f1, col_f2, col_f3 = st.columns(3)

            with col_f1:
                font_options = ["Arial", "Times New Roman", "Calibri", "Courier New", "Georgia"]
                current_idx = font_options.index(
                    st.session_state.font_family) if st.session_state.font_family in font_options else 0
                selected_font = st.selectbox("Шрифт:", options=font_options, index=current_idx,
                                             key="edit_font_selector")
                if selected_font != st.session_state.font_family:
                    st.session_state.font_family = selected_font

            with col_f2:
                preset_sizes = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
                default_idx = preset_sizes.index(
                    st.session_state.font_size) if st.session_state.font_size in preset_sizes else len(preset_sizes)

                size_option = st.selectbox(
                    "Размер шрифта (px):",
                    options=[str(s) for s in preset_sizes] + ["Другое..."],
                    index=default_idx,
                    key="edit_size_selector"
                )

                if size_option == "Другое...":
                    new_font_size = st.number_input("Введите размер (от 8 до 40):", min_value=8, max_value=40,
                                                    value=st.session_state.font_size, step=1, key="edit_custom_size")
                else:
                    new_font_size = int(size_option)

                if new_font_size != st.session_state.font_size:
                    st.session_state.font_size = new_font_size

            with col_f3:
                new_color = st.color_picker("Цвет текста:", value=st.session_state.font_color, key="edit_color_picker")
                if new_color != st.session_state.font_color:
                    st.session_state.font_color = new_color

            st.markdown("---")
            st.markdown("#### 📝 Редактор конспекта")
            edited_text = st.text_area("Внесите правки в текст ниже:", value=st.session_state.llm_result, height=450,
                                       key="editor_text_area")

            st.markdown("---")
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Сохранить изменения", key="btn_save_edit", type="primary", use_container_width=True):
                    st.session_state.llm_result = edited_text.strip()
                    st.session_state.edit_mode = False
                    st.rerun()
            with col_cancel:
                if st.button("❌ Отменить", key="btn_cancel_edit", use_container_width=True):
                    st.session_state.edit_mode = False
                    st.rerun()

        # ===== Кнопки скачивания в режиме редактирования =====
        st.markdown("---")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="📥 Скачать результат в TXT",
                data=st.session_state.llm_result,
                file_name=f"summary_{task_type.replace(' ', '_')}.txt",
                mime="text/plain",
                key="download_result_txt_edit"
            )
        with col_d2:
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Конспект - {task_type}</title>
    <style>
        body {{
            font-size: {st.session_state.font_size}px;
            font-family: {st.session_state.font_family};
            color: {st.session_state.font_color};
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
        }}
    </style>
</head>
<body>
    {st.session_state.llm_result.replace(chr(10), '<br>')}
</body>
</html>"""
            st.download_button(
                label="📥 Скачать результат в HTML",
                data=html_content,
                file_name=f"summary_{task_type.replace(' ', '_')}.html",
                mime="text/html",
                key="download_result_html_edit"
            )