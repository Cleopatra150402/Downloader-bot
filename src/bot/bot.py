import logging
from typing import Optional

from telegram.ext import Application

from .handlers import BotHandlers
from ..services.database import DatabaseService
from ..services.youtube_downloader import YouTubeDownloader
from ..config.settings import settings

logger = logging.getLogger(__name__)

class YouTubeBotApp:
    """Основное приложение Telegram бота"""
    
    def __init__(self, token: str = None):
        self.token = token or settings.BOT_TOKEN
        self.application: Optional[Application] = None
        self.db_service = DatabaseService()
        self.youtube_service = YouTubeDownloader()
        self.handlers = BotHandlers(self.db_service, self.youtube_service)
    
    def setup(self):
        """Настройка приложения"""
        # Проверяем настройки
        settings.validate()
        
        # Инициализируем базу данных
        self.db_service.init_database()
        
        # Создаем приложение
        self.application = Application.builder().token(self.token).build()
        
        # Регистрируем обработчики
        self.handlers.register_handlers(self.application)
        
        logger.info("Приложение настроено успешно")
    
    def run(self):
        """Запуск бота"""
        if not self.application:
            raise RuntimeError("Приложение не настроено. Вызовите setup() сначала")
        
        logger.info("🚀 YouTube Bot запущен!")
        logger.info("📺 Поддерживает только YouTube видео")
        
        self.application.run_polling()
    
    def stop(self):
        """Остановка бота"""
        if self.application:
            self.application.stop()
            logger.info("Бот остановлен")

