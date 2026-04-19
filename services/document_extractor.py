def extract_from_document(file_path: str, file_ext: str) -> str:
    """Извлекает текст из документов: pdf, docx, pptx, xlsx, msg"""
    try:
        from markitdown import MarkItDown
        md = MarkItDown()
        result = md.convert(file_path)
        return result.text_content or "⚠️ Текст не извлечён"
    except Exception as e:
        return f"❌ Не удалось обработать документ: {e}"
    