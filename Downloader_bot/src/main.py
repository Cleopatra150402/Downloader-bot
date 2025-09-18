#!/usr/bin/env python3

import logging
import sys
from pathlib import Path

# Добавляем корневую папку в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bot.bot import YouTubeBotApp

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

def main():
    """Главная функция запуска бота"""
    try:
        app = YouTubeBotApp()
        app.setup()
        app.run()
    except KeyboardInterrupt:
        logging.info("Получен сигнал остановки")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

