"""
Сервис пользователей (стабильный)
"""

from flask import jsonify
from services.base_service import BaseMicroservice


class UserService(BaseMicroservice):
    def __init__(self):
        super().__init__(name="user-service", port=8001, failure_mode="none")

    def setup_custom_routes(self):
        @self.app.route('/api/users')
        def get_users():
            return jsonify({
                'users': [
                    {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
                    {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'},
                    {'id': 3, 'name': 'Charlie', 'email': 'charlie@example.com'}
                ],
                'count': 3
            })

    def health_check(self):
        return jsonify({
            'status': 'healthy',
            'service': self.name,
            'timestamp': __import__('time').time()
        })