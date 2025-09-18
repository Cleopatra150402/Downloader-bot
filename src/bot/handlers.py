import logging
import os
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

if TYPE_CHECKING:
    from ..services.database import DatabaseService
    from ..services.youtube_downloader import YouTubeDownloader

from ..models.download import Download

logger = logging.getLogger(__name__)

class BotHandlers:
    """Обработчики команд и сообщений бота"""
    
    def __init__(self, db_service: 'DatabaseService', youtube_service: 'YouTubeDownloader'):
        self.db_service = db_service
        self.youtube_service = youtube_service
    
    def register_handlers(self, application: Application):
        """Регистрация обработчиков"""
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        welcome_message = """
🎥 Привет! Я бот для скачивания YouTube видео!

📺 Поддерживается только YouTube
⏱️ Максимальная длительность: 10 минут
📊 Максимальный размер: 50MB

Просто отправь ссылку на YouTube видео!

Команды:
/start - начать работу
/help - помощь  
/stats - статистика скачиваний
"""
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
🔧 Как пользоваться ботом:

1. Отправь ссылку на YouTube видео
2. Дождись обработки (обычно 10-30 секунд)
3. Получи видео прямо в чат!

⚠️ Ограничения:
• Только YouTube видео
• Максимум 10 минут длительностью
• Размер файла до 50MB
• Только публичные видео

Примеры ссылок:
• https://www.youtube.com/watch?v=...
• https://youtu.be/...
• https://youtube.com/shorts/...
"""
        await update.message.reply_text(help_text)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats - статистика пользователя"""
        user_id = update.effective_user.id
        stats = self.db_service.get_user_stats(user_id)
        
        if stats:
            total = sum(stat['count'] for stat in stats)
            stats_text = f"📊 Ваша статистика скачиваний:\n\n📺 YouTube: {total} видео"
        else:
            stats_text = "У вас пока нет скачанных видео."
        
        await update.message.reply_text(stats_text)
    
    def is_youtube_url(self, url: str) -> bool:
        """Проверка, является ли ссылка YouTube URL"""
        youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
        return any(domain in url.lower() for domain in youtube_domains)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщений с YouTube ссылками"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Проверяем, что это YouTube ссылка
        if not self.is_youtube_url(text):
            await update.message.reply_text(
                "❌ Неподдерживаемая ссылка!\n\n"
                "Отправьте ссылку на YouTube видео:\n"
                "• https://www.youtube.com/watch?v=...\n"
                "• https://youtu.be/...\n"
                "• https://youtube.com/shorts/..."
            )
            return
        
        # Отправляем сообщение о начале обработки
        status_message = await update.message.reply_text(
            "⏳ Обрабатываю YouTube видео...\n"
            "Это может занять до 30 секунд ⏱️"
        )
        
        try:
            # Скачиваем видео
            success, result, info = self.youtube_service.download(text)
            
            if success:
                # Отправляем видео
                with open(result, 'rb') as video_file:
                    caption = f"🎥 {info['title'][:100]}\n📺 YouTube"
                    if info.get('file_size'):
                        caption += f"\n📊 {info['file_size'] // (1024*1024)} MB"
                    if info.get('view_count'):
                        caption += f"\n👀 {info['view_count']:,} просмотров"
                    
                    await update.message.reply_video(
                        video_file,
                        caption=caption,
                        supports_streaming=True
                    )
                
                # Удаляем временный файл
                os.unlink(result)
                
                # Сохраняем в БД
                download = Download(
                    user_id=user_id,
                    platform='youtube',
                    video_url=text,
                    status='completed'
                )
                self.db_service.save_download(download)
                
                await status_message.edit_text("✅ Видео отправлено!")
            else:
                # Сохраняем ошибку в БД
                download = Download(
                    user_id=user_id,
                    platform='youtube',
                    video_url=text,
                    status='failed'
                )
                self.db_service.save_download(download)
                
                await status_message.edit_text(f"❌ Ошибка: {result}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await status_message.edit_text(
                "❌ Произошла ошибка при обработке видео.\n"
                "Попробуйте еще раз или используйте другую ссылку."
            )

