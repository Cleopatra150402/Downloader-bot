import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.database import DatabaseService
from src.models.download import Download

class TestDatabaseService:
    
    @pytest.fixture
    def mock_db_config(self):
        return {
            'host': 'test_host',
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass',
            'port': 5432
        }
    
    @pytest.fixture
    def db_service(self, mock_db_config):
        return DatabaseService(mock_db_config)
    
    @patch('src.services.database.psycopg2.connect')
    def test_get_connection_success(self, mock_connect, db_service):
        """Тест успешного подключения к БД"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        with db_service.get_connection() as conn:
            assert conn == mock_conn
        
        mock_connect.assert_called_once_with(**db_service.db_config)
    
    @patch('src.services.database.psycopg2.connect')
    def test_get_connection_failure(self, mock_connect, db_service):
        """Тест ошибки подключения к БД"""
        mock_connect.side_effect = Exception("Connection error")
        
        with pytest.raises(Exception, match="Connection error"):
            with db_service.get_connection():
                pass
    
    @patch('src.services.database.psycopg2.connect')
    def test_save_download_success(self, mock_connect, db_service):
        """Тест успешного сохранения скачивания"""
        # Настраиваем моки
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1, datetime.now())
        mock_connect.return_value = mock_conn
        
        download = Download(
            user_id=123,
            platform='youtube',
            video_url='https://youtube.com/test'
        )
        
        result = db_service.save_download(download)
        
        assert result is True
        assert download.id == 1
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @patch('src.services.database.psycopg2.connect')
    def test_save_download_failure(self, mock_connect, db_service):
        """Тест ошибки при сохранении"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("DB error")
        mock_connect.return_value = mock_conn
        
        download = Download(
            user_id=123,
            platform='youtube',
            video_url='https://youtube.com/test'
        )
        
        result = db_service.save_download(download)
        
        assert result is False
        mock_conn.rollback.assert_called_once()
    
    @patch('src.services.database.psycopg2.connect')
    def test_get_user_stats(self, mock_connect, db_service):
        """Тест получения статистики пользователя"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {'platform': 'youtube', 'count': 5}
        ]
        mock_connect.return_value = mock_conn
        
        stats = db_service.get_user_stats(123)
        
        assert len(stats) == 1
        assert stats[0]['platform'] == 'youtube'
        assert stats[0]['count'] == 5
    
    @patch('src.services.database.psycopg2.connect')
    def test_init_database(self, mock_connect, db_service):
        """Тест инициализации базы данных"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        db_service.init_database()
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

