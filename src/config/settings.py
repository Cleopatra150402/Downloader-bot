import os
from typing import Dict, Any
from dotenv import load_dotenv

# Загружаем .env только если он существует (для локальной разработки)
if os.path.exists('.env'):
    load_dotenv()

class Settings:
    """Настройки приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Database - используем переменные окружения Docker
    DB_CONFIG: Dict[str, Any] = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'telegram_bot'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': int(os.getenv('DB_PORT', 5432))
    }
    
    # YouTube Download
    MAX_DURATION: int = 600  # 10 minutes
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    @classmethod
    def validate(cls) -> None:
        """Проверка обязательных настроек"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        if not cls.DB_CONFIG['password']:
            raise ValueError("Database password is required")

settings = Settings()

