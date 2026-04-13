"""
API Gateway - точка входа для всех запросов
"""

from flask import jsonify, request
import requests
from services.base_service import BaseMicroservice


class GatewayService(BaseMicroservice):
    def __init__(self):
        super().__init__(name="gateway-service", port=8000, failure_mode="none")

    def setup_custom_routes(self):
        @self.app.route('/api/info')
        def get_info():
            """Получение информации от всех сервисов"""
            result = {}

            # Запрос к user-service
            try:
                r = requests.get('http://127.0.0.1:8001/info', timeout=2)
                result['user_service'] = r.json()
            except Exception as e:
                result['user_service'] = {'error': str(e)}

            # Запрос к payment-service
            try:
                r = requests.get('http://127.0.0.1:8002/info', timeout=2)
                result['payment_service'] = r.json()
            except Exception as e:
                result['payment_service'] = {'error': str(e)}

            return jsonify(result)

        @self.app.route('/api/payment', methods=['POST'])
        def proxy_payment():
            """Проксирование запроса к payment-service"""
            try:
                response = requests.post(
                    'http://127.0.0.1:8002/api/payment',
                    json=request.json,
                    timeout=5
                )
                return jsonify(response.json()), response.status_code
            except Exception as e:
                return jsonify({'error': str(e)}), 503

    def health_check(self):
        # Проверяем зависимые сервисы
        services_status = {}

        try:
            r = requests.get('http://127.0.0.1:8001/health', timeout=2)
            services_status['user-service'] = 'ok' if r.status_code == 200 else 'fail'
        except:
            services_status['user-service'] = 'unreachable'

        try:
            r = requests.get('http://127.0.0.1:8002/health', timeout=2)
            services_status['payment-service'] = 'ok' if r.status_code == 200 else 'fail'
        except:
            services_status['payment-service'] = 'unreachable'

        all_healthy = all(s == 'ok' for s in services_status.values())

        return jsonify({
            'status': 'healthy' if all_healthy else 'degraded',
            'service': self.name,
            'dependencies': services_status
        })