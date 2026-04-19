def transcribe_media(file_path: str, model_size: str = "base") -> str:
    """
    Транскрибирует аудио/видео файл.
    Поддерживает: .wav, .mp3, .m4a, .mp4, .mkv, .avi, .mov, .flv
    """
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, info = model.transcribe(file_path, beam_size=1, language="ru")
        text = " ".join([segment.text.strip() for segment in segments])
        return text if text else "⚠️ Речь не распознана"
    except ImportError:
        return "❌ Функция распознавания речи временно недоступна"
    except Exception as e:
        return f"❌ Не удалось распознать речь: {e}"
    