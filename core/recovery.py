"""
Модуль автоматического восстановления сервисов
"""

import subprocess
import sys
import time
import threading
from typing import Dict, Optional
from datetime import datetime

class RecoveryManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.service_processes: Dict[str, object] = {}
        self.last_recovery_time: Dict[str, float] = {}
        self.recovery_lock = threading.Lock()

    def register_process(self, service_name: str, process):
        self.service_processes[service_name] = process

    def recover_service(self, service_name: str) -> bool:
        with self.recovery_lock:
            current_time = time.time()
            if service_name in self.last_recovery_time:
                if current_time - self.last_recovery_time[service_name] < 30:
                    print(f"⏸️ Пропуск восстановления {service_name} - слишком часто")
                    self._save_recovery_event(service_name, False, 'throttled', 'Too frequent restart')
                    return False

            self.last_recovery_time[service_name] = current_time

            if service_name == 'payment-service':
                success = self._restart_payment_service()
            elif service_name == 'user-service':
                success = self._restart_user_service()
            elif service_name == 'gateway-service':
                success = self._restart_gateway_service()
            elif service_name == 'cart-service':
                success = self._restart_cart_service()
            else:
                success = False

            self._save_recovery_event(service_name, success, 'auto_restart',
                                     'Service restarted successfully' if success else 'Restart failed')
            return success

    def _save_recovery_event(self, service_name: str, success: bool, method: str, details: str):
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recovery_events (service_name, timestamp, success, recovery_method, details)
                VALUES (?, ?, ?, ?, ?)
            """, (service_name, time.time(), 1 if success else 0, method, details))
            conn.commit()
            conn.close()
            print(f"📝 Событие восстановления сохранено: {service_name} -> {'Успех' if success else 'Ошибка'}")
        except Exception as e:
            print(f"❌ Ошибка сохранения события восстановления: {e}")

    def _restart_payment_service(self) -> bool:
        print("🔄 Перезапуск payment-service...")
        try:
            from services.payment_service import PaymentService
            payment_service = PaymentService(failure_mode="random")
            thread = threading.Thread(target=payment_service.run, daemon=True)
            thread.start()
            self.service_processes['payment-service'] = thread
            print("✅ payment-service успешно перезапущен")
            return True
        except Exception as e:
            print(f"❌ Ошибка перезапуска payment-service: {e}")
            return False

    def _restart_user_service(self) -> bool:
        print("🔄 Перезапуск user-service...")
        try:
            from services.user_service import UserService
            user_service = UserService()
            thread = threading.Thread(target=user_service.run, daemon=True)
            thread.start()
            self.service_processes['user-service'] = thread
            print("✅ user-service успешно перезапущен")
            return True
        except Exception as e:
            print(f"❌ Ошибка перезапуска user-service: {e}")
            return False

    def _restart_gateway_service(self) -> bool:
        print("🔄 Перезапуск gateway-service...")
        try:
            from services.gateway_service import GatewayService
            gateway_service = GatewayService()
            thread = threading.Thread(target=gateway_service.run, daemon=True)
            thread.start()
            self.service_processes['gateway-service'] = thread
            print("✅ gateway-service успешно перезапущен")
            return True
        except Exception as e:
            print(f"❌ Ошибка перезапуска gateway-service: {e}")
            return False

    def _restart_cart_service(self) -> bool:   # ← НОВЫЙ МЕТОД
        print("🔄 Перезапуск cart-service...")
        try:
            from services.cart_service import CartService
            cart_service = CartService(failure_mode="random")  # можно "none" если не хотим отказов
            thread = threading.Thread(target=cart_service.run, daemon=True)
            thread.start()
            self.service_processes['cart-service'] = thread
            print("✅ cart-service успешно перезапущен")
            return True
        except Exception as e:
            print(f"❌ Ошибка перезапуска cart-service: {e}")
            return False

    def get_recovery_stats(self) -> Dict:
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as total, SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                FROM recovery_events
            """)
            row = cursor.fetchone()
            conn.close()
            total = row[0] or 0
            successful = row[1] or 0
            return {
                'total_recoveries': total,
                'successful_recoveries': successful,
                'success_rate': (successful / total * 100) if total > 0 else 0
            }
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {'total_recoveries': 0, 'successful_recoveries': 0, 'success_rate': 0}

    def get_recovery_events(self, limit: int = 50):
        try:
            conn = self.db_manager.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recovery_events ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Ошибка получения событий: {e}")
            return []