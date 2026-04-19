import os


def get_ffmpeg_path():
    """Возвращает полный путь к ffmpeg бинарнику"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:
        print(f"⚠️ ffmpeg not found: {e}")
        return None


def setup_ffmpeg_env():
    """Добавляет ffmpeg в PATH для subprocess-вызовов"""
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path:
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        current_path = os.environ.get("PATH", "")
        if ffmpeg_dir not in current_path:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path
            print(f"✅ FFmpeg added to PATH: {ffmpeg_dir}")
            return True
    return False