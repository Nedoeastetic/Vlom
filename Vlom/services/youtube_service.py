import re
import json
import urllib.request
import urllib.error
import time
import random
import os


def extract_video_id(url: str) -> str:
    """Извлекает ID видео из YouTube URL"""
    patterns = [
        r'(?:v=|/)([a-zA-Z0-9_-]{11})(?:\?|&|/|$)',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'embed/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def parse_json_subtitles(json_text: str) -> str:
    """Парсит JSON-субтитры YouTube"""
    try:
        data = json.loads(json_text)
        text_lines = []
        
        events = data.get('events', [])
        for event in events:
            segs = event.get('segs', [])
            for seg in segs:
                utf8_text = seg.get('utf8', '')
                if utf8_text and utf8_text.strip():
                    cleaned = utf8_text.strip()
                    if cleaned != '\n':
                        text_lines.append(cleaned)
        
        result = ' '.join(text_lines)
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
        
    except json.JSONDecodeError:
        return "❌ Не удалось распарсить данные субтитров"
    except Exception as e:
        return f"❌ Ошибка обработки данных: {e}"


def clean_vtt(vtt_text: str) -> str:
    """Очищает VTT-субтитры от таймкодов и тегов"""
    lines = vtt_text.split('\n')
    clean_lines = []
    in_header = True
    
    for line in lines:
        if line.strip() == 'WEBVTT' or line.strip().startswith('Kind:') or line.strip().startswith('Language:'):
            continue
        if in_header and line.strip() == '':
            in_header = False
            continue
        if in_header:
            continue
        
        if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3}', line.strip()):
            continue
        if re.match(r'^\d+$', line.strip()):
            continue
        
        line = re.sub(r'<[^>]+>', '', line)
        line = re.sub(r'NOTE.*', '', line)
        line = re.sub(r'STYLE.*', '', line)
        
        if line.strip():
            clean_lines.append(line.strip())
    
    return ' '.join(clean_lines)


def get_youtube_transcript_ytdlp(
    video_url: str, 
    language: str = "ru",
    cookies_path: str = None,
    browser_name: str = None
) -> str:
    """
    Получает субтитры с YouTube.
    
    Параметры:
    - video_url: ссылка на видео
    - language: предпочтительный язык субтитров
    - cookies_path: путь к файлу cookies.txt (опционально)
    - browser_name: имя браузера для извлечения cookies (опционально): 
      'chrome', 'firefox', 'edge', 'safari', 'opera', 'brave', 'vivaldi'
    """
    try:
        import yt_dlp
        
        video_id = extract_video_id(video_url)
        if not video_id:
            return "❌ Не удалось извлечь ID видео из ссылки"
        
        # Формируем опции yt-dlp
        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'retries': 3,
        }
        
        # 🔹 Добавляем cookies, если указаны
        if cookies_path and os.path.exists(cookies_path):
            ydl_opts['cookiefile'] = cookies_path
        elif browser_name:
            ydl_opts['cookies_from_browser'] = browser_name
        
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    
                    if not info:
                        return "❌ Не удалось получить информацию о видео"
                    
                    subtitles = info.get('subtitles', {})
                    automatic_captions = info.get('automatic_captions', {})
                    
                    if not subtitles and not automatic_captions:
                        return "❌ Для этого видео нет доступных субтитров\n\n💡 Попробуйте скачать аудио и обработать его как файл"
                    
                    caption_url = None
                    subs_lang = language if language != 'auto' else 'ru'
                    
                    # Приоритет поиска субтитров
                    for lang in [subs_lang, 'en', 'en-US', 'ru-RU']:
                        if lang in subtitles:
                            for sub in subtitles[lang]:
                                if sub.get('ext') == 'vtt':
                                    caption_url = sub.get('url')
                                    break
                            if caption_url:
                                break
                    
                    if not caption_url:
                        for lang in [subs_lang, 'en', 'en-US']:
                            if lang in automatic_captions:
                                for sub in automatic_captions[lang]:
                                    if sub.get('ext') in ['vtt', 'json3', 'srv3']:
                                        caption_url = sub.get('url')
                                        break
                                if caption_url:
                                    break
                    
                    if not caption_url:
                        available_langs = list(subtitles.keys()) + list(automatic_captions.keys())
                        return f"❌ Субтитры на языке '{subs_lang}' не найдены\n\n💡 Доступные языки: {', '.join(available_langs[:5])}"
                    
                    # Скачиваем субтитры
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/vtt,application/json,*/*',
                        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
                    }
                    
                    request = urllib.request.Request(caption_url, headers=headers)
                    
                    with urllib.request.urlopen(request, timeout=30) as response:
                        raw_content = response.read().decode('utf-8')
                    
                    if raw_content.strip().startswith('{'):
                        text = parse_json_subtitles(raw_content)
                    else:
                        text = clean_vtt(raw_content)
                    
                    return text if text.strip() else "⚠️ Субтитры пустые"
                    
            except urllib.error.HTTPError as e:
                last_error = e
                if e.code == 429:
                    if attempt < max_retries:
                        wait_time = (2 ** attempt) + random.uniform(0.5, 2.0)
                        time.sleep(wait_time)
                        continue
                    else:
                        return f"❌ YouTube ограничивает запросы (429). Попробуйте позже или используйте cookies.\n\n💡 Альтернатива: скачайте аудио с видео и загрузите как файл"
                elif e.code == 403 and "bot" in str(e).lower():
                    return "❌ YouTube требует подтверждения, что вы не бот.\n\n💡 Решение:\n1. Экспортируйте cookies из браузера (инструкция ниже)\n2. Укажите путь к файлу в настройках приложения"
                else:
                    raise
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                if "sign in" in error_str or "confirm you're not a bot" in error_str:
                    return "❌ YouTube требует входа для подтверждения, что вы не бот.\n\n💡 Решение:\n1. Экспортируйте cookies из браузера\n2. Укажите путь к файлу cookies.txt в настройках"
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise
        
        return f"❌ Не удалось получить субтитры после {max_retries} попыток: {last_error}"
            
    except ImportError:
        return "❌ Функция работы с YouTube временно недоступна"
    except Exception as e:
        return f"❌ Не удалось получить данные с YouTube: {e}"