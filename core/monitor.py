"""
Модуль мониторинга микросервисов
"""

import time
import threading
import requests
from typing import Dict
from config.settings import MONITORING_INTERVAL, HEALTH_TIMEOUT, FAILURE_THRESHOLD

def log_print(*args, **kwargs):
    print(*args, **kwargs, flush=True)

class ServiceMonitor:
    def __init__(self, db_manager, alert_manager, recovery_manager):
        self.db_manager = db_manager
        self.alert_manager = alert_manager
        self.recovery_manager = recovery_manager
        self.services: Dict[str, dict] = {}
        self.is_running = False
        self.monitor_thread = None

    def register_service(self, name: str, url: str, threshold: int = FAILURE_THRESHOLD, auto_recovery: bool = True):
        """Регистрация сервиса для мониторинга"""
        self.services[name] = {
            'name': name,
            'url': url,
            'threshold': threshold,
            'failures': 0,
            'status': 'unknown',
            'last_check': 0,
            'auto_recovery': auto_recovery  # Добавляем флаг
        }
        log_print(f"📝 Зарегистрирован сервис: {name} (порог: {threshold} ошибок, авто-восст: {auto_recovery})")

    def check_service(self, service: dict) -> dict:
        start_time = time.time()
        result = {
            'name': service['name'],
            'is_healthy': False,
            'response_time_ms': 0,
            'error': None
        }

        try:
            response = requests.get(service['url'], timeout=HEALTH_TIMEOUT)
            response_time = (time.time() - start_time) * 1000
            result['response_time_ms'] = round(response_time, 2)

            if response.status_code == 200:
                data = response.json()
                is_healthy = data.get('status') == 'healthy'
                result['is_healthy'] = is_healthy
                if not is_healthy:
                    result['error'] = data.get('error', 'Service unhealthy')
            else:
                result['error'] = f'HTTP {response.status_code}'

        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            result['response_time_ms'] = round(response_time, 2)
            result['error'] = 'Timeout'
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            result['response_time_ms'] = round(response_time, 2)
            result['error'] = 'Connection refused'
        except Exception as e:
            result['error'] = str(e)

        return result

    def update_service_status(self, service_name: str, check_result: dict):
        service = self.services[service_name]
        is_healthy = check_result['is_healthy']

        self.db_manager.save_metric(
            service_name=service_name,
            status='healthy' if is_healthy else 'unhealthy',
            response_time_ms=check_result['response_time_ms'],
            error_message=check_result['error'],
            is_healthy=is_healthy
        )

        if is_healthy:
            if service['failures'] > 0:
                log_print(f"✅ {service_name} - вернул здоровый ответ (было {service['failures']} ошибок)")
            service['failures'] = 0
            service['status'] = 'healthy'
        else:
            service['failures'] += 1
            service['status'] = 'degraded'

            log_print(f"⚠️ {service_name} - ошибка ({service['failures']}/{service['threshold']}): {check_result['error']}")

            # Восстанавливаем ТОЛЬКО если auto_recovery = True
            if service['failures'] >= service['threshold'] and service.get('auto_recovery', True):
                log_print(f"🔴 ДОСТИГНУТ ПОРОГ! {service_name}: {service['failures']} >= {service['threshold']}")
                self.initiate_recovery(service_name)
            elif service['failures'] >= service['threshold']:
                log_print(f"⚠️ {service_name} - достигнут порог, но авто-восстановление отключено")

    def initiate_recovery(self, service_name: str):
        log_print(f"🔴 КРИТИЧЕСКИЙ АЛЕРТ: {service_name} НЕДОСТУПЕН!")

        self.db_manager.save_alert(
            service_name=service_name,
            severity='critical',
            message=f'Сервис {service_name} недоступен после {self.services[service_name]["failures"]} проверок'
        )

        self.alert_manager.send_telegram(
            f"🔴 КРИТИЧЕСКИЙ АЛЕРТ!\nСервис {service_name} недоступен!\nЗапускаю автоматическое восстановление..."
        )

        success = self.recovery_manager.recover_service(service_name)

        if success:
            log_print(f"✅ {service_name} - успешно восстановлен!")
            self.services[service_name]['failures'] = 0
            self.services[service_name]['status'] = 'healthy'
        else:
            log_print(f"❌ {service_name} - восстановление НЕ УДАЛОСЬ!")
            self.services[service_name]['status'] = 'critical'

    def monitor_loop(self):
        log_print("🔄 Запуск цикла мониторинга...")
        log_print(f"📊 Интервал проверки: {MONITORING_INTERVAL} сек")
        log_print(f"📊 Порог ошибок: {FAILURE_THRESHOLD}")
        log_print("=" * 60)

        while self.is_running:
            for service_name, service in self.services.items():
                check_result = self.check_service(service)
                self.update_service_status(service_name, check_result)

            time.sleep(MONITORING_INTERVAL)

    def start(self):
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        log_print("✅ Мониторинг запущен")

    def stop(self):
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        log_print("⏹️ Мониторинг остановлен")

    def get_status(self) -> Dict:
        return {
            name: {
                'status': service['status'],
                'failures': service['failures'],
                'threshold': service['threshold']
            }
            for name, service in self.services.items()
        }