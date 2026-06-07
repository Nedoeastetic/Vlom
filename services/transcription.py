"""
Транскрипция аудио/видео через faster-whisper.
Возвращает dict {"text": str, "segments": list[dict]} для поддержки таймкодов.
"""
from __future__ import annotations

import os


def transcribe_media(
    file_path: str,
    model_size: str = "medium",
    language: str | None = None,
) -> dict:
    """
    Транскрибирует медиафайл.

    Возвращает:
        {
            "text": "полный текст",
            "segments": [
                {"start": 0.0, "end": 5.2, "text": "Привет, это начало..."},
                ...
            ]
        }
    При ошибке возвращает {"text": "❌ ...", "segments": []}.
    """
    if not os.path.exists(file_path):
        return {"text": f"❌ Файл не найден: {file_path}", "segments": []}

    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments_iter, info = model.transcribe(
            file_path,
            language=language,
            beam_size=5,
            vad_filter=True,  # убирает тишину → меньше галлюцинаций
        )

        segments = []
        full_text_parts = []
        for seg in segments_iter:
            segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
            })
            full_text_parts.append(seg.text.strip())

        return {
            "text": " ".join(full_text_parts),
            "segments": segments,
            "language": info.language,
        }

    except ImportError:
        return {"text": "❌ faster-whisper не установлен. Запустите: pip install faster-whisper", "segments": []}
    except Exception as e:
        return {"text": f"❌ Ошибка транскрипции: {e}", "segments": []}