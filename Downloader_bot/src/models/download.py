from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Download:
    """Модель записи о скачивании"""
    user_id: int
    platform: str
    video_url: str
    status: str = 'completed'
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

