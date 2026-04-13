"""
Конфигурационные параметры системы мониторинга
"""

# Настройки мониторинга
MONITORING_INTERVAL = 5  # секунд
FAILURE_THRESHOLD = 3    # количество ошибок для восстановления
HEALTH_TIMEOUT = 3       # таймаут health check в секундах

# Порты микросервисов
USER_SERVICE_PORT = 8001
PAYMENT_SERVICE_PORT = 8002
GATEWAY_SERVICE_PORT = 8000
MONITORING_API_PORT = 5000

# Режимы отказа (для демонстрации)
FAILURE_MODES = {
    'none': 'Без отказов',
    'random': 'Случайные отказы (30%)',
    'scheduled': 'Плановые отказы (5 сек каждые 20 сек)',
    'memory_leak': 'Эмуляция утечки памяти'
}

# Настройки алертов
TELEGRAM_ENABLED = False  # Включить если есть токен
TELEGRAM_BOT_TOKEN = ''   # Заполните при наличии
TELEGRAM_CHAT_ID = ''     # Заполните при наличии

# База данных
DATABASE_PATH = 'database/monitoring.db'

# Логирование
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/monitoring.log'