# config/constants.py

# ✅ Только модели, доступные через бесплатный HF Inference API
AVAILABLE_MODELS = [
    "mistralai/Mistral-7B-Instruct-v0.3",
    "meta-llama/Llama-3.2-3B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
    "microsoft/Phi-3-mini-4k-instruct",
    "google/gemma-2-2b-it",
    "openchat/openchat-3.5-0106",

]
DEFAULT_MODEL = AVAILABLE_MODELS[0]

# Остальные константы без изменений
DOC_EXTENSIONS = ["pdf", "docx", "pptx", "xlsx", "xls", "msg"]
MEDIA_EXTENSIONS = ["wav", "mp3", "m4a", "mp4", "mkv", "avi", "mov", "flv"]
ALL_EXTENSIONS = DOC_EXTENSIONS + MEDIA_EXTENSIONS

PROMPTS = {
    "Краткий пересказ": "Сделай краткий пересказ текста на русском. Выдели 3-5 главных мыслей.",
    "Подробный конспект": "Сделай подробный конспект текста с разделами и подпунктами. Сохрани важную информацию.",
    "Тезисы": "Выдели основные тезисы текста в виде маркированного списка. Только ключевые утверждения.",
    "План статьи": "Составь структурированный план статьи с разделами и подразделами."
}

CHAR_LIMIT = 40000