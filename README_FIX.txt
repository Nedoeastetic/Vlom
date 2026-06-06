1. Замените файлы:
   ui/ai_analysis.py
   ui/text_editor.py

2. В Supabase откройте SQL Editor и выполните весь файл:
   sql/add_user_folders.sql

3. Полностью перезапустите Streamlit:
   Ctrl+C
   streamlit run app.py

Причины ошибки:
- таблица public.note_folders ещё не создана в Supabase;
- после новой генерации сохранялся старый edit_mode и пустой editor_draft,
  поэтому новый конспект сразу открывался пустым редактором.
