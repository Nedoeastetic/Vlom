import os
import shutil
import tempfile
import yt_dlp
from services.transcription import transcribe_media


def _ensure_ffmpeg_for_ytdlp() -> str | None:
    """Находит ffmpeg/ffprobe и принудительно добавляет их в PATH для yt-dlp"""
    # 1. Приоритет: системный PATH (Homebrew ставит правильные имена)
    ffmpeg_exe = shutil.which('ffmpeg')
    ffprobe_exe = shutil.which('ffprobe')

    if ffmpeg_exe and ffprobe_exe and os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe):
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        current_path = os.environ.get('PATH', '')
        if ffmpeg_dir not in current_path.split(os.pathsep):
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + current_path
        return ffmpeg_dir

    # 2. Fallback: imageio_ffmpeg
    try:
        import imageio_ffmpeg
        exe_path = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(exe_path):
            ffmpeg_dir = os.path.dirname(exe_path)
            current_path = os.environ.get('PATH', '')
            if ffmpeg_dir not in current_path.split(os.pathsep):
                os.environ['PATH'] = ffmpeg_dir + os.pathsep + current_path
            return ffmpeg_dir
    except Exception:
        pass

    return None


def get_transcript_from_vk_rutube(video_url: str, whisper_model: str = "base") -> str:
    ffmpeg_dir = _ensure_ffmpeg_for_ytdlp()
    if not ffmpeg_dir:
        return "❌ FFmpeg не найден. Установите: `brew install ffmpeg` и перезапустите Streamlit."

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(tmpdir, 'audio'),
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'retries': 3,
                'socket_timeout': 30,
                'ffmpeg_location': ffmpeg_dir,  # Явная передача директории
                'nocheckcertificate': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            audio_files = [
                f for f in os.listdir(tmpdir)
                if f.startswith("audio") and f.endswith(('.mp3', '.m4a', '.opus', '.wav', '.webm'))
            ]
            if not audio_files:
                return "❌ Не удалось извлечь аудио. Возможно, видео защищено от загрузки."

            audio_path = os.path.join(tmpdir, audio_files[0])
            return transcribe_media(audio_path, model_size=whisper_model)

    except yt_dlp.utils.DownloadError as e:
        err = str(e).lower()
        if any(k in err for k in ["private", "unavailable", "region", "blocked"]):
            return "❌ Видео приватное, удалено или заблокировано по регионам."
        return f"❌ Ошибка загрузки: {e}"
    except Exception as e:
        return f"❌ Ошибка обработки VK/Rutube: {e}"