"""
ffmpeg_setup.py — единая точка для настройки ffmpeg.
app.py вызывает _setup_ffmpeg_early() до импортов,
эти утилиты используются после.
"""
from __future__ import annotations

import os
import shutil


def get_ffmpeg_path() -> str | None:
    """Возвращает путь к исполняемому файлу ffmpeg или None."""
    # 1. Системный PATH
    path = shutil.which("ffmpeg")
    if path:
        return path

    # 2. imageio_ffmpeg как запасной вариант
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def setup_ffmpeg_env() -> bool:
    """
    Гарантирует что ffmpeg доступен в PATH.
    Безопасно вызывать несколько раз (идемпотентно).
    """
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return False

    ffmpeg_dir = os.path.dirname(ffmpeg)
    current = os.environ.get("PATH", "")
    if ffmpeg_dir and ffmpeg_dir not in current:
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + current

    return True