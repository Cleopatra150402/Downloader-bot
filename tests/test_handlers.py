import pytest
from unittest.mock import Mock, AsyncMock, patch
import tempfile

from src.bot.handlers import BotHandlers
from src.models.download import Download

class TestBotHandlers:
    
    @pytest.fixture
    def mock_db_service(self):
        return Mock()
    
    @pytest.fixture
    def mock_youtube_service(self):
        return Mock()
    
    @pytest.fixture
    def handlers(self, mock_db_service, mock_youtube_service):
        return BotHandlers(mock_db_service, mock_youtube_service)
    
    @pytest.mark.asyncio
    async def test_start_command(self, handlers):
        """Тест команды /start"""
        update = Mock()
        context = Mock()
        update.message.reply_text = AsyncMock()
        
        await handlers.start_command(update, context)
        
        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args[0]
        assert "Привет!" in args[0]
        assert "YouTube" in args[0]
    
    @pytest.mark.asyncio
    async def test_help_command(self, handlers):
        """Тест команды /help"""
        update = Mock()
        context = Mock()
        update.message.reply_text = AsyncMock()
        
        await handlers.help_command(update, context)
        
        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args[0]
        assert "пользоваться" in args[0]
    
    @pytest.mark.asyncio
    async def test_stats_command_with_data(self, handlers, mock_db_service):
        """Тест команды /stats с данными"""
        update = Mock()
        context = Mock()
        update.effective_user.id = 123
        update.message.reply_text = AsyncMock()
        
        mock_db_service.get_user_stats.return_value = [
            {'platform': 'youtube', 'count': 5}
        ]
        
        await handlers.stats_command(update, context)
        
        mock_db_service.get_user_stats.assert_called_once_with(123)
        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args[0]
        assert "YouTube: 5" in args[0]
    
    @pytest.mark.asyncio
    async def test_stats_command_no_data(self, handlers, mock_db_service):
        """Тест команды /stats без данных"""
        update = Mock()
        context = Mock()
        update.effective_user.id = 123
        update.message.reply_text = AsyncMock()
        
        mock_db_service.get_user_stats.return_value = []
        
        await handlers.stats_command(update, context)
        
        args = update.message.reply_text.call_args[0]
        assert "пока нет" in args[0]
    
    def test_is_youtube_url(self, handlers):
        """Тест проверки YouTube URL"""
        assert handlers.is_youtube_url("https://www.youtube.com/watch?v=test")
        assert handlers.is_youtube_url("https://youtu.be/test")
        assert handlers.is_youtube_url("https://youtube.com/shorts/test")
        assert not handlers.is_youtube_url("https://vimeo.com/test")
        assert not handlers.is_youtube_url("https://instagram.com/test")
    
    @pytest.mark.asyncio
    async def test_handle_message_invalid_url(self, handlers):
        """Тест обработки невалидного URL"""
        update = Mock()
        context = Mock()
        update.effective_user.id = 123
        update.message.text = "https://vimeo.com/test"
        update.message.reply_text = AsyncMock()
        
        await handlers.handle_message(update, context)
        
        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args[0]
        assert "Неподдерживаемая ссылка" in args[0]
    
    @pytest.mark.asyncio
    @patch('os.unlink')
    @patch('builtins.open')
    async def test_handle_message_success(self, mock_open, mock_unlink, 
                                        handlers, mock_db_service, mock_youtube_service):
        """Тест успешной обработки сообщения"""
        # Настройка моков
        update = Mock()
        context = Mock()
        update.effective_user.id = 123
        update.message.text = "https://youtube.com/watch?v=test"
        update.message.reply_text = AsyncMock(return_value=Mock())
        update.message.reply_video = AsyncMock()
        
        # Мок для status_message
        status_message = Mock()
        status_message.edit_text = AsyncMock()
        update.message.reply_text.return_value = status_message
        
        mock_youtube_service.download.return_value = (
            True, '/tmp/test.mp4', {'title': 'Test Video', 'file_size': 1024}
        )
        
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        await handlers.handle_message(update, context)
        
        # Проверяем вызовы
        mock_youtube_service.download.assert_called_once_with(
            "https://youtube.com/watch?v=test"
        )
        update.message.reply_video.assert_called_once()
        mock_db_service.save_download.assert_called_once()
        status_message.edit_text.assert_called_with("✅ Видео отправлено!")
    
    @pytest.mark.asyncio
    async def test_handle_message_download_failure(self, handlers, mock_db_service, 
                                                 mock_youtube_service):
        """Тест ошибки при скачивании"""
        update = Mock()
        context = Mock()
        update.effective_user.id = 123
        update.message.text = "https://youtube.com/watch?v=test"
        update.message.reply_text = AsyncMock(return_value=Mock())
        
        status_message = Mock()
        status_message.edit_text = AsyncMock()
        update.message.reply_text.return_value = status_message
        
        mock_youtube_service.download.return_value = (
            False, "Ошибка скачивания", {}
        )
        
        await handlers.handle_message(update, context)
        
        mock_db_service.save_download.assert_called_once()
        # Проверяем что сохранили с статусом failed
        call_args = mock_db_service.save_download.call_args[0][0]
        assert call_args.status == 'failed'
        
        status_message.edit_text.assert_called_with("❌ Ошибка: Ошибка скачивания")

