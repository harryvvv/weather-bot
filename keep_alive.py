# keep_alive.py (версия 1.0)
import requests
import time
import logging
import sys
import platform

# Настройка логирования для Windows
if platform.system() == "Windows":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

WEBHOOK_URL = "https://твой_логин.pythonanywhere.com/твой_бот_токен"

def keep_alive():
    """Отправлять запрос каждые 5 минут для предотвращения засыпания"""
    while True:
        try:
            response = requests.get(WEBHOOK_URL, timeout=10)
            logger.info(f"✅ Keep-alive request sent. Status: {response.status_code}")
            time.sleep(300)  # 5 минут
        except Exception as e:
            logger.error(f"❌ Keep-alive error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    logger.info("🚀 Keep-alive script started")
    keep_alive()