# Vlom

<div align="center">

**Интеллектуальный сервис для создания, редактирования и хранения конспектов**

Загружайте документы, аудио, видео или ссылки на видеоплатформы, получайте структурированный конспект с помощью ИИ, редактируйте его и сохраняйте в пользовательские папки.

</div>

---

## О проекте

**Vlom** — веб-приложение на Streamlit для автоматического создания конспектов из разных источников.

Приложение умеет:

- извлекать текст из документов;
- расшифровывать аудио и видео;
- получать субтитры и текст из видеоссылок;
- создавать краткий пересказ, подробный конспект, тезисы или план статьи;
- редактировать результат во встроенном rich-text редакторе;
- формировать таблицы и графики по содержанию конспекта;
- сохранять конспекты в профиле пользователя;
- создавать собственные папки;
- переносить сохранённые конспекты между папками;
- скачивать результаты в TXT и HTML.

---

## Основные возможности

### Работа с документами

Поддерживаются основные форматы:

- PDF;
- DOCX;
- PPTX;
- XLSX и XLS;
- MSG.

Текст извлекается через библиотеку `MarkItDown`.

### Работа с аудио и видео

Для локальных медиафайлов используется `faster-whisper`.

Поддерживаются распространённые форматы:

- MP3;
- WAV;
- M4A;
- MP4;
- MOV;
- AVI;
- MKV.

Для обработки медиа используется FFmpeg.

### Работа с видеоплатформами

Приложение может получать текст из:

- YouTube;
- VK Видео;
- Rutube.

Для загрузки метаданных, субтитров и аудиодорожек используется `yt-dlp`.

### ИИ-анализ

Конспекты создаются через Hugging Face Inference API.

Доступные сценарии анализа:

- краткий пересказ;
- подробный конспект;
- основные тезисы;
- план статьи.

Приложение поддерживает несколько Hugging Face-токенов и может переключаться между ними при достижении лимита.

### Редактор конспектов

Встроенный редактор поддерживает:

- жирный текст;
- курсив;
- подчёркивание;
- зачёркивание;
- заголовки;
- списки;
- выравнивание;
- изменение размера текста;
- изменение цвета;
- классические шрифты;
- ссылки и цитаты.

Редактор построен на `streamlit-quill`.

### Таблицы и графики

ИИ может создавать таблицы и графики на основе информации из исходного материала.

Поддерживаются:

- таблицы;
- столбчатые графики;
- линейные графики;
- графики площади;
- диаграммы рассеяния.

Графики создаются только при наличии числовых данных в исходном тексте.

### Профили и папки

Через Supabase реализованы:

- регистрация;
- авторизация;
- сохранение конспектов;
- редактирование сохранённых конспектов;
- удаление конспектов;
- создание пользовательских папок;
- переименование папок;
- перенос конспектов между папками;
- раздел «Без папки».

Названия папок пользователь задаёт самостоятельно.

---

## Архитектура проекта

```text
Vlom/
├── app.py
├── check_token.py
├── requirements.txt
├── .env
│
├── config/
│   ├── constants.py
│   └── token_manager.py
│
├── db/
│   ├── supabase_client.py
│   └── user_manager.py
│
├── services/
│   ├── document_extractor.py
│   ├── transcription.py
│   ├── youtube_service.py
│   ├── vk_rutube_service.py
│   └── visualization_service.py
│
├── ui/
│   ├── __init__.py
│   ├── ai_analysis.py
│   ├── cleanup.py
│   ├── display.py
│   ├── file_upload.py
│   ├── help_section.py
│   ├── notes_view.py
│   ├── page_config.py
│   ├── results.py
│   ├── sidebar.py
│   ├── status.py
│   ├── text_editor.py
│   ├── vk_rutube_form.py
│   └── youtube_form.py
│
├── utils/
│   ├── ffmpeg_setup.py
│   └── text_cleaner.py
│
└── sql/
    └── add_user_folders.sql
```

---

## Схема работы приложения

```text
Документ, аудио, видео или ссылка
                │
                ▼
        Извлечение текста
                │
                ▼
         Очистка текста
                │
                ▼
        Hugging Face Inference
                │
                ▼
     Конспект, таблицы и графики
                │
                ▼
       Rich-text редактор
                │
                ▼
     Скачивание или Supabase
                │
                ▼
       Пользовательские папки
```

---

# Установка и запуск

## Требования

- Python 3.10 или 3.11;
- Git;
- доступ к интернету;
- Hugging Face Token;
- Supabase — для аккаунтов и сохранения конспектов.

Проверьте Python:

```bash
python --version
```

Проверьте Git:

```bash
git --version
```

---

## 1. Клонирование репозитория

```bash
git clone https://github.com/Nedoeastetic/Vlom.git
cd Vlom
```

Если проект уже скачан:

```bash
git pull origin main
```

---

## 2. Создание виртуального окружения

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

Если запуск скриптов запрещён:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Windows CMD

```cmd
.venv\Scripts\activate
```

### Linux и macOS

```bash
source .venv/bin/activate
```

---

## 3. Установка зависимостей

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Если зависимости редактора отсутствуют:

```bash
pip install streamlit-quill pandas
```

Если отдельно не устанавливается MarkItDown:

```bash
pip install "markitdown[all]"
```

---

## 4. Создание Hugging Face Token

Создайте токен типа:

```text
Fine-grained
```

Включите разрешение:

```text
Inference → Make calls to Inference Providers
```

---

## 5. Настройка `.env`

Создайте в корне проекта файл `.env` рядом с `app.py`.

Минимальная конфигурация:

```env
HF_TOKEN_1=hf_ваш_токен
```

Для Supabase добавьте:

```env
SUPABASE_URL=https://ваш-проект.supabase.co
SUPABASE_KEY=ваш_anon_public_key
```

---

## 6. Настройка Supabase

Supabase необходим для:

- регистрации;
- входа;
- сохранения конспектов;
- пользовательских папок;
- редактирования сохранённых записей.

Выполните SQL из файла:

```text
sql/add_user_folders.sql
```

В SQL Editor нужно вставлять содержимое файла, а не его путь.

После выполнения SQL обновите schema cache:

```sql
notify pgrst, 'reload schema';
```

---

## 7. Запуск приложения

```bash
streamlit run app.py
```

Если команда не найдена:

```bash
python -m streamlit run app.py
```

Приложение откроется по адресу:

```text
http://localhost:8501
```

---

## Переменные окружения

| Переменная | Обязательность | Назначение |
|---|---:|---|
| `HF_TOKEN_1` | Да | Основной токен Hugging Face |
| `HF_TOKEN_2` | Нет | Резервный токен |
| `HF_TOKEN_3` | Нет | Резервный токен |
| `SUPABASE_URL` | Для профиля | URL проекта Supabase |
| `SUPABASE_KEY` | Для профиля | Anon public key Supabase |

---

## Типичные ошибки

### Таблица `note_folders` не найдена

Выполните SQL создания таблицы и затем:

```sql
notify pgrst, 'reload schema';
```

### Hugging Face возвращает 401

Проверьте правильность токена и расположение `.env`.

### Hugging Face возвращает 403

У токена должно быть разрешение:

```text
Make calls to Inference Providers
```

### Streamlit не найден

```bash
python -m streamlit run app.py
```

### После изменения кода ничего не изменилось

```text
Ctrl+C
```

Затем:

```bash
python -m streamlit run app.py
```

И обновите браузер через `Ctrl+F5`.

---

## Безопасность

Не добавляйте в Git:

```text
.env
.venv/
__pycache__/
*.pyc
```

Рекомендуемый `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
.streamlit/
```

---

## Используемые технологии

- Python;
- Streamlit;
- Hugging Face Inference API;
- Faster Whisper;
- FFmpeg;
- yt-dlp;
- MarkItDown;
- Supabase;
- Pandas;
- Streamlit Quill.

---

## Автор

Репозиторий:

```text
https://github.com/Nedoeastetic/Vlom
```
