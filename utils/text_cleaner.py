import re


def clean_markdown_text(text: str) -> str:
    """
    Очищает текст от Markdown-разметки:
    - Убирает жирное выделение (**текст**)
    - Убирает заголовки (#, ##, ### и т.д.)
    - Убирает маркеры списков (-, *, +)
    - Убирает лишние пробелы и пустые строки
    """
    if not text:
        return ""

    # 1. Убираем заголовки
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

    # 2. Убираем жирное выделение и курсив
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)

    # 3. Убираем маркеры списков
    text = re.sub(r'^[\-\*\+]\s+', '', text, flags=re.MULTILINE)

    # 4. Убираем лишние пробелы и пустые строки
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    text = '\n'.join(cleaned_lines)

    # 5. Убираем множественные переносы строк
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text