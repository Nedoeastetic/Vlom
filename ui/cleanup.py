import streamlit as st


def render_cleanup_button():
    """Отрисовывает кнопку очистки данных"""
    # Показываем кнопку если есть данные ИЛИ загружен файл ИЛИ введена ссылка
    has_data = (
        st.session_state.extracted_text or 
        st.session_state.youtube_url or
        st.session_state.get('youtube_input_value', '')
    )
    
    if has_data:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🗑️ Очистить всё", key="clear_all_btn"):
                # 🔹 Очищаем ВСЕ данные
                keys_to_clear = [
                    'extracted_text',
                    'file_info', 
                    'processing_status',
                    'llm_result',
                    'youtube_url',
                    'youtube_input_value',
                ]
                
                for key in keys_to_clear:
                    if key in st.session_state:
                        st.session_state[key] = None if key != 'youtube_url' and key != 'youtube_input_value' else ""
                
                # 🔹 Увеличиваем счётчики для сброса виджетов
                st.session_state.file_uploader_counter = st.session_state.get('file_uploader_counter', 0) + 1
                st.session_state.youtube_field_key = st.session_state.get('youtube_field_key', 0) + 1
                
                # 🔹 Принудительная перезагрузка
                st.rerun()
        st.write("")