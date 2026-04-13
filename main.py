#!/usr/bin/env python3
"""
Система мониторинга и автоматического восстановления для Python-микросервисов
"""

import sys
import os
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import MONITORING_API_PORT
from database.db_manager import DatabaseManager
from core.monitor import ServiceMonitor
from core.recovery import RecoveryManager
from core.alerting import AlertManager
from web.app import start_web_interface, set_payment_service, set_cart_service

from services.user_service import UserService
from services.payment_service import PaymentService
from services.cart_service import CartService  # Вместо GatewayService


class MonitoringSystem:
    def __init__(self):
        self.db_manager = None
        self.alert_manager = None
        self.recovery_manager = None
        self.monitor = None
        self.payment_service = None
        self.cart_service = None  # Добавляем Cart Service
        self.service_threads = []

    def init_database(self):
        print("📁 Инициализация базы данных...")
        self.db_manager = DatabaseManager()
        print("✅ База данных готова")

    def init_alerting(self):
        print("📱 Инициализация системы алертинга...")
        self.alert_manager = AlertManager()
        print("✅ Система алертинга готова")

    def init_recovery(self):
        print("🔄 Инициализация системы восстановления...")
        self.recovery_manager = RecoveryManager(self.db_manager)
        print("✅ Система восстановления готова")

    def start_services(self):
        print("\n🚀 Запуск микросервисов...")

        # User Service (стабильный)
        user_service = UserService()
        user_thread = threading.Thread(target=user_service.run, daemon=True)
        user_thread.start()
        self.service_threads.append(user_thread)
        print("  ✅ User Service запущен на порту 8001")

        # Payment Service (нестабильный - для демонстрации)
        self.payment_service = PaymentService(failure_mode="random")
        payment_thread = threading.Thread(target=self.payment_service.run, daemon=True)
        payment_thread.start()
        self.service_threads.append(payment_thread)
        print("  ✅ Payment Service запущен на порту 8002 (режим: random)")

        # Cart Service (новый, независимый)
        self.cart_service = CartService(failure_mode="random")
        cart_thread = threading.Thread(target=self.cart_service.run, daemon=True)
        cart_thread.start()
        self.service_threads.append(cart_thread)
        print("  ✅ Cart Service запущен на порту 8003")

        # Регистрируем процессы в recovery_manager
        self.recovery_manager.register_process('payment-service', payment_thread)

        time.sleep(2)
        print("\n✅ Все микросервисы запущены!")

    def start_monitoring(self):
        print("\n🔍 Инициализация системы мониторинга...")

        self.monitor = ServiceMonitor(self.db_manager, self.alert_manager, self.recovery_manager)

        # Регистрируем сервисы для мониторинга
        self.monitor.register_service("user-service", "http://127.0.0.1:8001/health", auto_recovery=True)
        self.monitor.register_service("payment-service", "http://127.0.0.1:8002/health", auto_recovery=True)
        self.monitor.register_service("cart-service", "http://127.0.0.1:8003/health", auto_recovery=True)

        self.monitor.start()
        print("✅ Мониторинг запущен")

    def start_web_interface(self):
        print(f"\n🌐 Запуск веб-интерфейса на порту {MONITORING_API_PORT}...")

        # Передаем ссылки на сервисы в веб-интерфейс
        set_payment_service(self.payment_service)
        set_cart_service(self.cart_service)

        web_thread = threading.Thread(
            target=start_web_interface,
            args=(MONITORING_API_PORT, self.monitor, self.db_manager),
            daemon=True
        )
        web_thread.start()

        print(f"✅ Веб-интерфейс: http://localhost:{MONITORING_API_PORT}")

    def run(self):
        print("=" * 60)
        print("   СИСТЕМА МОНИТОРИНГА МИКРОСЕРВИСОВ")
        print("   С автоматическим восстановлением")
        print("=" * 60)
        print()

        self.init_database()
        self.init_alerting()
        self.init_recovery()
        self.start_services()
        self.start_monitoring()
        self.start_web_interface()

        print("\n" + "=" * 60)
        print("   СИСТЕМА ЗАПУЩЕНА!")
        print("   📊 Дашборд: http://localhost:5000")
        print("   🔧 Сервисы: http://localhost:5000/services")
        print("   🔄 Лог восстановлений: http://localhost:5000/recovery")
        print("=" * 60)
        print("\n💡 Для демонстрации:")
        print("   - На странице 'Сервисы' можно менять режим отказов Payment Service")
        print("   - В режиме 'Плановые отказы' сервис падает 3 раза подряд")
        print("   - Система обнаружит 3 ошибки и автоматически восстановит сервис")
        print("\n⏹️ Нажмите Ctrl+C для остановки\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️ Остановка системы...")
            self.stop()

    def stop(self):
        if self.monitor:
            self.monitor.stop()
        print("✅ Система остановлена")


def main():
    system = MonitoringSystem()
    system.run()


if __name__ == "__main__":
    main()