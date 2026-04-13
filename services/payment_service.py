"""
Сервис платежей (нестабильный - для демонстрации)
"""

from flask import jsonify, request
import random
import time
from services.base_service import BaseMicroservice


class PaymentService(BaseMicroservice):
    def __init__(self, failure_mode: str = "random"):
        super().__init__(name="payment-service", port=8002, failure_mode=failure_mode)
        self.failure_countdown = 0  # Счетчик оставшихся отказов

    def setup_custom_routes(self):
        @self.app.route('/api/payment', methods=['POST'])
        def process_payment():
            if self.should_fail():
                return jsonify({'error': 'Payment processing failed'}), 500

            amount = request.json.get('amount', 100) if request.json else 100

            return jsonify({
                'status': 'success',
                'transaction_id': random.randint(10000, 99999),
                'amount': amount,
                'message': 'Payment processed successfully'
            })

    def health_check(self):
        current_time = time.time()

        # ПЛАНОВЫЕ ОТКАЗЫ (scheduled) - 3 ошибки подряд, потом восстановление
        if self.failure_mode == 'scheduled':
            if self.failure_countdown > 0:
                # Все еще в режиме падения
                self.failure_countdown -= 1
                print(f"⏰ [SCHEDULED FAILURE] Payment Service падает (осталось отказов: {self.failure_countdown + 1}/3)", flush=True)
                return jsonify({
                    'status': 'unhealthy',
                    'service': self.name,
                    'error': f'Scheduled failure ({self.failure_countdown + 1}/3)',
                    'mode': self.failure_mode
                }), 503
            else:
                # Режим падения закончился, сервис здоров
                return jsonify({
                    'status': 'healthy',
                    'service': self.name,
                    'requests_handled': self.request_count,
                    'mode': self.failure_mode,
                    'timestamp': current_time
                })

        # СЛУЧАЙНЫЕ ОТКАЗЫ (random)
        elif self.failure_mode == 'random':
            if random.random() < 0.3:
                print(f"🎲 [RANDOM FAILURE] Payment Service падает случайно", flush=True)
                return jsonify({
                    'status': 'unhealthy',
                    'service': self.name,
                    'error': 'Random failure',
                    'mode': self.failure_mode
                }), 503
            else:
                return jsonify({
                    'status': 'healthy',
                    'service': self.name,
                    'requests_handled': self.request_count,
                    'mode': self.failure_mode,
                    'timestamp': current_time
                })

        # БЕЗ ОТКАЗОВ (none)
        else:
            return jsonify({
                'status': 'healthy',
                'service': self.name,
                'requests_handled': self.request_count,
                'mode': self.failure_mode,
                'timestamp': current_time
            })

    def should_fail(self) -> bool:
        self.request_count += 1

        if self.failure_mode == 'random':
            return random.random() < 0.3

        elif self.failure_mode == 'scheduled':
            # Если счетчик отказов > 0 - падаем
            if self.failure_countdown > 0:
                self.failure_countdown -= 1
                return True
            return False

        return False

    def set_failure_mode(self, mode: str):
        """Установка режима отказа с сбросом счетчика"""
        self.failure_mode = mode
        self.failure_countdown = 0  # Сбрасываем счетчик при смене режима
        print(f"🔄 Режим Payment Service изменен на: {mode}", flush=True)

        # Если включили плановые отказы - запускаем 3 ошибки подряд
        if mode == 'scheduled':
            self.failure_countdown = 3
            print(f"⏰ Запущено 3 последовательных отказа", flush=True)

    def run(self):
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        print(f"💳 Payment Service запущен на порту {self.port} (режим: {self.failure_mode})", flush=True)
        self.app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)