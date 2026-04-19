#!/usr/bin/env python3
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os
load_dotenv()
TOKEN=os.environ.get('TOKEN')


MODEL = "Qwen/Qwen2.5-7B-Instruct"  # ✅ Рабочая альтернатива

def check_token():
    try:
        # 🔹 ИСПРАВЛЕНО: убран base_url, он конфликтует с model
        client = InferenceClient(
            model=MODEL,
            token=TOKEN.strip()  # .strip() на всякий случай убирает случайные пробелы
        )
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Ответь одним словом: готов?"}],
            max_tokens=20
        )
        print(f"✅ Успех! Ответ модели: {response.choices[0].message.content.strip()}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        
        # 🔹 Детальная обработка ошибок
        if "Received both `model` and `base_url`" in error_msg:
            print("❌ Ошибка: Удалите base_url из InferenceClient (конфликт параметров)")
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            print("❌ Ошибка 401: Неверный токен. Проверьте ключ на huggingface.co/settings/tokens")
        elif "404" in error_msg or "not found" in error_msg.lower():
            print(f"❌ Ошибка 404: Модель `{MODEL}` не найдена или недоступна через API")
            print("💡 Попробуйте: 'mistralai/Mistral-7B-Instruct-v0.3' или 'Qwen/Qwen2.5-3B-Instruct'")
        elif "503" in error_msg or "loading" in error_msg.lower():
            print(f"⚠️ Модель `{MODEL}` загружается. Попробуйте через 30-60 секунд.")
        elif "429" in error_msg or "rate limit" in error_msg.lower():
            print("⚠️ Превышен лимит запросов. Попробуйте позже.")
        else:
            print(f"❌ Ошибка: {error_msg}")
        return False

if __name__ == "__main__":
    print(f"🔍 Тестирую токен и модель: {MODEL}")
    print("-" * 50)
    check_token()