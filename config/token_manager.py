import os
from typing import List, Optional
from dotenv import load_dotenv

# Загружаем переменные из .env при импорте модуля
load_dotenv()


class TokenManager:
    """
    Управляет пулом токенов Hugging Face с автоматической ротацией.
    При ошибке 429 (rate limit) автоматически переключается на следующий токен.
    """
    
    def __init__(self):
        self.tokens = self._load_tokens()
        self.current_index = 0
        self.failed_tokens: set[int] = set()
        
    def _load_tokens(self) -> List[str]:
        """
        Загружает токены из переменных окружения.
        Поддерживает:
        - HF_TOKEN_1, HF_TOKEN_2, ... (несколько токенов)
        - HF_TOKEN (один токен, для обратной совместимости)
        """
        tokens = []
        
        # Пробуем загрузить HF_TOKEN_1, HF_TOKEN_2 и т.д.
        i = 1
        while True:
            token = os.getenv(f"HF_TOKEN_{i}")
            if not token:
                break
            tokens.append(token.strip())
            i += 1
        
        # Если не найдено токенов с суффиксом, пробуем просто HF_TOKEN
        if not tokens:
            single_token = os.getenv("HF_TOKEN")
            if single_token:
                tokens.append(single_token.strip())
        
        return tokens
    
    def get_token(self) -> Optional[str]:
        """Возвращает текущий активный токен"""
        if not self.tokens:
            return None
        return self.tokens[self.current_index]
    
    def rotate_token(self, reason: str = "") -> bool:
        """
        Переключается на следующий токен.
        Возвращает True, если удалось переключиться.
        """
        if len(self.tokens) <= 1:
            return False  # Нечем ротировать
        
        # Помечаем текущий индекс как проблемный
        self.failed_tokens.add(self.current_index)
        
        # Ищем следующий рабочий токен
        for offset in range(1, len(self.tokens)):
            next_index = (self.current_index + offset) % len(self.tokens)
            if next_index not in self.failed_tokens:
                self.current_index = next_index
                return True
        
        # Если все помечены как failed — сбрасываем и берём следующий по кругу
        self.failed_tokens.clear()
        self.current_index = (self.current_index + 1) % len(self.tokens)
        return True
    
    def get_stats(self) -> dict:
        """Статистика использования токенов"""
        return {
            "total": len(self.tokens),
            "active_index": self.current_index,
            "failed_count": len(self.failed_tokens),
            "available": len(self.tokens) - len(self.failed_tokens)
        }
    
    def is_configured(self) -> bool:
        """Проверяет, настроены ли токены"""
        return len(self.tokens) > 0


# Глобальный экземпляр для всего приложения
token_manager = TokenManager()