import logging
import os
import tempfile
import yt_dlp
from typing import Tuple, Dict, Any

from ..config.settings import settings

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    """Сервис для скачивания видео с YouTube"""
    
    def __init__(self):
        self.max_duration = settings.MAX_DURATION
        self.max_file_size = settings.MAX_FILE_SIZE
    
    def get_ydl_options(self, output_path: str) -> Dict[str, Any]:
        """Получить настройки для yt-dlp"""
        return {
            'format': f'best[height<=720][filesize<{self.max_file_size}]/best[filesize<{self.max_file_size}]/mp4[filesize<{self.max_file_size}]/best',
            'outtmpl': output_path,
            'no_warnings': True,
            'extractaudio': False,
            'embed_subs': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            'no_cache_dir': True,
            'force_overwrites': True,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_client': ['android', 'web'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        }
    
    def extract_info(self, url: str) -> Tuple[bool, Dict[str, Any]]:
        """Извлечь информацию о видео без скачивания"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return True, {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0)
                }
        except Exception as e:
            logger.error(f"Ошибка извлечения информации: {e}")
            return False, {'error': str(e)}
    
    def download(self, url: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Скачать видео с YouTube
    
        Returns:
            Tuple[bool, str, Dict]: (success, file_path_or_error, info)
        """
        temp_filename = None
        
        def safe_remove(file_path):
            """Безопасное удаление файла"""
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Не удалось удалить файл {file_path}: {e}")
        
        try:
            # Сначала проверяем информацию о видео
            success, info = self.extract_info(url)
            if not success:
                return False, info.get('error', 'Unknown error'), {}
            
            # Проверяем длительность
            if info['duration'] and info['duration'] > self.max_duration:
                return False, f"❌ Видео слишком длинное (максимум {self.max_duration//60} минут)", info
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # Получаем настройки yt-dlp
            ydl_opts = self.get_ydl_options(temp_filename)
            
            # Принудительно удаляем файл если существует
            safe_remove(temp_filename)
            
            # Скачиваем видео
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                except Exception as e:
                    # Пробуем с альтернативными настройками
                    logger.warning(f"Первая попытка не удалась: {e}, пробуем альтернативные настройки")
                    
                    alt_opts = {
                        'format': 'worst[ext=mp4]/worst',
                        'outtmpl': temp_filename,
                        'no_warnings': True,
                        'no_cache_dir': True,
                        'force_overwrites': True,
                    }
                    
                    safe_remove(temp_filename)
                    
                    with yt_dlp.YoutubeDL(alt_opts) as ydl_alt:
                        ydl_alt.download([url])
            
            # Проверяем результат скачивания
            if not os.path.exists(temp_filename):
                return False, "❌ Файл не был создан", info
            
            file_size = os.path.getsize(temp_filename)
            if file_size == 0:
                safe_remove(temp_filename)
                return False, "❌ Скачанный файл пустой", info
            
            if file_size > self.max_file_size:
                safe_remove(temp_filename)
                return False, f"❌ Файл слишком большой (максимум {self.max_file_size//1024//1024} MB)", info
            
            info['file_size'] = file_size
            return True, temp_filename, info
            
        except Exception as e:
            logger.error(f"Ошибка скачивания YouTube: {e}")
            safe_remove(temp_filename)
            return False, str(e), {}
