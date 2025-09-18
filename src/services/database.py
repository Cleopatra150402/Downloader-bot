import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from ..config.settings import settings
from ..models.download import Download

logger = logging.getLogger(__name__)

class DatabaseService:
    """Сервис для работы с базой данных"""
    
    def __init__(self, db_config: Dict[str, Any] = None):
        self.db_config = db_config or settings.DB_CONFIG
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для подключения к БД"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def save_download(self, download: Download) -> bool:
        """Сохранение информации о скачивании"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO downloads (user_id, platform, video_url, status) 
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, created_at
                """, (download.user_id, download.platform, download.video_url, download.status))
                
                result = cursor.fetchone()
                if result:
                    download.id, download.created_at = result
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка сохранения в БД: {e}")
            return False
    
    def get_user_stats(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение статистики пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT platform, COUNT(*) as count 
                    FROM downloads 
                    WHERE user_id = %s AND status = 'completed'
                    GROUP BY platform
                """, (user_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return []
    
    def init_database(self) -> None:
        """Инициализация базы данных"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS downloads (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        platform VARCHAR(50) NOT NULL,
                        video_url TEXT NOT NULL,
                        status VARCHAR(20) DEFAULT 'completed',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_downloads_user_id 
                    ON downloads(user_id);
                    
                    CREATE INDEX IF NOT EXISTS idx_downloads_created_at 
                    ON downloads(created_at);
                """)
                conn.commit()
                logger.info("База данных инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise

