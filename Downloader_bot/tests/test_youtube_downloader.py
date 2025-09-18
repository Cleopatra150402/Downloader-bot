import pytest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os

from src.services.youtube_downloader import YouTubeDownloader

class TestYouTubeDownloader:
    
    @pytest.fixture
    def downloader(self):
        return YouTubeDownloader()
    
    def test_init(self, downloader):
        """Тест инициализации"""
        assert downloader.max_duration == 600
        assert downloader.max_file_size == 50 * 1024 * 1024
    
    def test_get_ydl_options(self, downloader):
        """Тест получения настроек yt-dlp"""
        output_path = "/tmp/test.mp4"
        options = downloader.get_ydl_options(output_path)
        
        assert options['outtmpl'] == output_path
        assert options['no_cache_dir'] is True
        assert options['force_overwrites'] is True
        assert 'youtube' in options['extractor_args']
    
    @patch('src.services.youtube_downloader.yt_dlp.YoutubeDL')
    def test_extract_info_success(self, mock_ydl, downloader):
        """Тест успешного извлечения информации"""
        mock_instance = Mock()
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 300,
            'view_count': 1000
        }
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        success, info = downloader.extract_info('https://youtube.com/test')
        
        assert success is True
        assert info['title'] == 'Test Video'
        assert info['duration'] == 300
        assert info['view_count'] == 1000
    
    @patch('src.services.youtube_downloader.yt_dlp.YoutubeDL')
    def test_extract_info_failure(self, mock_ydl, downloader):
        """Тест ошибки при извлечении информации"""
        mock_instance = Mock()
        mock_instance.extract_info.side_effect = Exception("Network error")
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        success, info = downloader.extract_info('https://youtube.com/test')
        
        assert success is False
        assert 'error' in info
        assert 'Network error' in info['error']
    
    @patch('src.services.youtube_downloader.yt_dlp.YoutubeDL')
    @patch('src.services.youtube_downloader.tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('os.remove')
    def test_download_success(self, mock_remove, mock_getsize, mock_exists,
                            mock_tempfile, mock_ydl, downloader):
        """Тест успешного скачивания"""
        # Настраиваем моки
        mock_temp = Mock()
        mock_temp.name = '/tmp/test.mp4'
        mock_tempfile.return_value.__enter__.return_value = mock_temp
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.download.return_value = None  # Успешное скачивание
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
        
        # Мокируем extract_info для реального объекта downloader
        with patch.object(downloader, 'extract_info', return_value=(True, {
            'title': 'Test Video',
            'duration': 300,
            'view_count': 1000
        })):
            mock_exists.return_value = True
            mock_getsize.return_value = 1024 * 1024  # 1MB
            
            success, result, info = downloader.download('https://youtube.com/test')
            
            assert success is True
            assert result == '/tmp/test.mp4'
            assert info['title'] == 'Test Video'
            assert info['file_size'] == 1024 * 1024
    
    def test_download_too_long(self, downloader):
        """Тест скачивания слишком длинного видео"""
        with patch.object(downloader, 'extract_info', return_value=(True, {
            'title': 'Long Video',
            'duration': 1200,  # 20 minutes
        })):
            success, result, info = downloader.download('https://youtube.com/test')
            
            assert success is False
            assert 'слишком длинное' in result
    
    @patch('src.services.youtube_downloader.yt_dlp.YoutubeDL')
    @patch('src.services.youtube_downloader.tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('os.remove')
    def test_download_empty_file(self, mock_remove, mock_getsize, mock_exists,
                                mock_tempfile, mock_ydl, downloader):
        """Тест скачивания пустого файла"""
        mock_temp = Mock()
        mock_temp.name = '/tmp/test.mp4'
        mock_tempfile.return_value.__enter__.return_value = mock_temp
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.download.return_value = None
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
        
        # Мокируем extract_info для реального объекта downloader
        with patch.object(downloader, 'extract_info', return_value=(True, {
            'title': 'Test Video',
            'duration': 300
        })):
            mock_exists.return_value = True
            mock_getsize.return_value = 0  # Empty file
            
            success, result, info = downloader.download('https://youtube.com/test')
            
            assert success is False
            assert 'пустой' in result
            mock_remove.assert_called()  # Проверяем что remove был вызван
    
    @patch('src.services.youtube_downloader.yt_dlp.YoutubeDL')
    @patch('src.services.youtube_downloader.tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('os.remove')
    def test_download_file_too_large(self, mock_remove, mock_getsize, mock_exists,
                                    mock_tempfile, mock_ydl, downloader):
        """Тест скачивания слишком большого файла"""
        mock_temp = Mock()
        mock_temp.name = '/tmp/test.mp4'
        mock_tempfile.return_value.__enter__.return_value = mock_temp
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.download.return_value = None
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
        
        # Мокируем extract_info для реального объекта downloader
        with patch.object(downloader, 'extract_info', return_value=(True, {
            'title': 'Large Video',
            'duration': 300
        })):
            mock_exists.return_value = True
            mock_getsize.return_value = 100 * 1024 * 1024  # 100MB (больше лимита 50MB)
            
            success, result, info = downloader.download('https://youtube.com/test')
            
            assert success is False
            assert 'слишком большой' in result
            mock_remove.assert_called()  # Проверяем что remove был вызван
    
    def test_download_extract_info_failure(self, downloader):
        """Тест ошибки при получении информации о видео"""
        with patch.object(downloader, 'extract_info', return_value=(False, {
            'error': 'Network error'
        })):
            success, result, info = downloader.download('https://youtube.com/test')
            
            assert success is False
            assert result == 'Network error'
    
    @patch('src.services.youtube_downloader.yt_dlp.YoutubeDL')
    @patch('src.services.youtube_downloader.tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_download_file_not_created(self, mock_remove, mock_exists,
                                      mock_tempfile, mock_ydl, downloader):
        """Тест когда файл не был создан после скачивания"""
        mock_temp = Mock()
        mock_temp.name = '/tmp/test.mp4'
        mock_tempfile.return_value.__enter__.return_value = mock_temp
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.download.return_value = None
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
        
        # Мокируем extract_info для реального объекта downloader
        with patch.object(downloader, 'extract_info', return_value=(True, {
            'title': 'Test Video',
            'duration': 300
        })):
            mock_exists.return_value = False  # Файл не существует
            
            success, result, info = downloader.download('https://youtube.com/test')
            
            assert success is False
            assert 'не был создан' in result
    
    @patch('src.services.youtube_downloader.yt_dlp.YoutubeDL')
    @patch('src.services.youtube_downloader.tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_download_general_exception(self, mock_remove, mock_exists, mock_tempfile, mock_ydl, downloader):
        """Тест обработки общих исключений"""
        mock_temp = Mock()
        mock_temp.name = '/tmp/test.mp4'
        mock_tempfile.return_value.__enter__.return_value = mock_temp
    
        # Настраиваем YoutubeDL чтобы работал при создании, но падал при download
        mock_ydl_instance = Mock()
        mock_ydl_instance.download.side_effect = Exception("General error")
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
    
        # Мокируем что файл существует для вызова safe_remove
        mock_exists.return_value = True
    
        # Мокируем extract_info для реального объекта downloader
        with patch.object(downloader, 'extract_info', return_value=(True, {
            'title': 'Test Video',
            'duration': 300
        })):
            success, result, info = downloader.download('https://youtube.com/test')
        
            assert success is False
            assert 'General error' in result
            mock_remove.assert_called()  # Теперь remove должен вызваться
