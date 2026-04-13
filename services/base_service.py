"""
Базовый класс для всех микросервисов
"""

from flask import Flask, jsonify
from flask_cors import CORS
import time
import threading
from abc import ABC, abstractmethod


class BaseMicroservice(ABC):
    """Абстрактный базовый класс микросервиса"""

    def __init__(self, name: str, port: int, failure_mode: str = "none"):
        self.name = name
        self.port = port
        self.failure_mode = failure_mode
        self.app = Flask(__name__)
        CORS(self.app)  # Разрешает запросы с любых источников
        self.request_count = 0
        self.start_time = time.time()
        self.is_running = True

        self._setup_routes()

    def _setup_routes(self):
        """Настройка маршрутов"""

        @self.app.route('/health')
        def health():
            return self.health_check()

        @self.app.route('/info')
        def info():
            return jsonify({
                'service': self.name,
                'port': self.port,
                'uptime': round(time.time() - self.start_time, 2),
                'requests_handled': self.request_count,
                'failure_mode': self.failure_mode
            })

        @self.app.route('/metrics')
        def metrics():
            return jsonify(self.get_metrics())

        # Дополнительные маршруты
        self.setup_custom_routes()

    @abstractmethod
    def setup_custom_routes(self):
        """Настройка специфичных маршрутов (переопределяется в наследниках)"""
        pass

    @abstractmethod
    def health_check(self):
        """Проверка здоровья (переопределяется в наследниках)"""
        pass

    def get_metrics(self):
        """Получение метрик сервиса"""
        return {
            'name': self.name,
            'uptime': round(time.time() - self.start_time, 2),
            'request_count': self.request_count,
            'failure_mode': self.failure_mode
        }

    def should_fail(self) -> bool:
        """Определяет, должен ли сервис ответить ошибкой"""
        self.request_count += 1

        if self.failure_mode == 'random':
            import random
            return random.random() < 0.3

        elif self.failure_mode == 'scheduled':
            return int(time.time()) % 20 < 5

        return False

    def run(self):
        """Запуск сервиса"""
        # Подавляем лишние логи
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

        self.app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)