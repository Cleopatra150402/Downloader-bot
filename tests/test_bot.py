import pytest
from unittest.mock import Mock, patch

from src.bot.bot import YouTubeBotApp

class TestYouTubeBotApp:
    
    @pytest.fixture
    def mock_token(self):
        return "test_token"
    
    def test_init_with_token(self, mock_token):
        """Тест инициализации с токеном"""
        app = YouTubeBotApp(mock_token)
        assert app.token == mock_token
        assert app.application is None
        assert app.db_service is not None
        assert app.youtube_service is not None
        assert app.handlers is not None
    
    @patch('src.bot.bot.settings')
    def test_init_without_token(self, mock_settings):
        """Тест инициализации без токена"""
        mock_settings.BOT_TOKEN = "settings_token"
        app = YouTubeBotApp()
        assert app.token == "settings_token"
    
    @patch('src.bot.bot.Application')
    @patch('src.bot.bot.settings')
    def test_setup(self, mock_settings, mock_application):
        """Тест настройки приложения"""
        mock_settings.validate.return_value = None
        mock_app_instance = Mock()
        mock_application.builder.return_value.token.return_value.build.return_value = mock_app_instance
        
        app = YouTubeBotApp("test_token")
        app.db_service.init_database = Mock()
        app.handlers.register_handlers = Mock()
        
        app.setup()
        
        assert app.application == mock_app_instance
        app.db_service.init_database.assert_called_once()
        app.handlers.register_handlers.assert_called_once_with(mock_app_instance)
    
    def test_run_without_setup(self):
        """Тест запуска без настройки"""
        app = YouTubeBotApp("test_token")
        
        with pytest.raises(RuntimeError, match="Приложение не настроено"):
            app.run()
    
    @patch('src.bot.bot.Application')
    @patch('src.bot.bot.settings')
    def test_run_with_setup(self, mock_settings, mock_application):
        """Тест запуска после настройки"""
        mock_settings.validate.return_value = None
        mock_app_instance = Mock()
        mock_application.builder.return_value.token.return_value.build.return_value = mock_app_instance
        
        app = YouTubeBotApp("test_token")
        app.db_service.init_database = Mock()
        app.handlers.register_handlers = Mock()
        
        app.setup()
        app.run()
        
        mock_app_instance.run_polling.assert_called_once()
    
    @patch('src.bot.bot.Application')
    @patch('src.bot.bot.settings')
    def test_stop(self, mock_settings, mock_application):
        """Тест остановки бота"""
        mock_settings.validate.return_value = None
        mock_app_instance = Mock()
        mock_application.builder.return_value.token.return_value.build.return_value = mock_app_instance
        
        app = YouTubeBotApp("test_token")
        app.db_service.init_database = Mock()
        app.handlers.register_handlers = Mock()
        
        app.setup()
        app.stop()
        
        mock_app_instance.stop.assert_called_once()

