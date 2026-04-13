"""
Cart Service - Сервис корзины покупок
Независимый сервис для демонстрации мониторинга
"""

from flask import jsonify, request
import random
import time
from services.base_service import BaseMicroservice


class CartService(BaseMicroservice):
    def __init__(self, failure_mode: str = "none"):
        super().__init__(name="cart-service", port=8003, failure_mode=failure_mode)
        self.carts = {}  # {user_id: [{"product_id": 1, "name": "...", "price": 100, "quantity": 1}]}
        self.failure_countdown = 0

    def setup_custom_routes(self):
        @self.app.route('/api/cart/<int:user_id>', methods=['GET'])
        def get_cart(user_id):
            """Получить корзину пользователя"""
            self.request_count += 1

            if self.should_fail():
                return jsonify({'error': 'Service unavailable'}), 500

            cart = self.carts.get(user_id, [])
            total = sum(item['price'] * item['quantity'] for item in cart)

            return jsonify({
                'user_id': user_id,
                'items': cart,
                'total': round(total, 2),
                'items_count': len(cart)
            })

        @self.app.route('/api/cart/add', methods=['POST'])
        def add_to_cart():
            """Добавить товар в корзину"""
            self.request_count += 1

            if self.should_fail():
                return jsonify({'error': 'Service unavailable'}), 500

            data = request.json
            user_id = data.get('user_id')
            product = {
                'product_id': data.get('product_id'),
                'name': data.get('name', 'Product'),
                'price': data.get('price', 0),
                'quantity': data.get('quantity', 1)
            }

            if not user_id:
                return jsonify({'error': 'user_id required'}), 400

            if user_id not in self.carts:
                self.carts[user_id] = []

            # Проверяем, есть ли уже такой товар
            for item in self.carts[user_id]:
                if item['product_id'] == product['product_id']:
                    item['quantity'] += product['quantity']
                    break
            else:
                self.carts[user_id].append(product)

            return jsonify({
                'status': 'success',
                'message': f"Added {product['quantity']} x {product['name']} to cart",
                'cart': self.carts[user_id]
            })

        @self.app.route('/api/cart/remove', methods=['DELETE'])
        def remove_from_cart():
            """Удалить товар из корзины"""
            self.request_count += 1

            if self.should_fail():
                return jsonify({'error': 'Service unavailable'}), 500

            data = request.json
            user_id = data.get('user_id')
            product_id = data.get('product_id')

            if user_id and user_id in self.carts:
                self.carts[user_id] = [item for item in self.carts[user_id] if item['product_id'] != product_id]

            return jsonify({
                'status': 'success',
                'message': 'Item removed from cart',
                'cart': self.carts.get(user_id, [])
            })

        @self.app.route('/api/cart/clear/<int:user_id>', methods=['DELETE'])
        def clear_cart(user_id):
            """Очистить корзину"""
            self.request_count += 1

            if self.should_fail():
                return jsonify({'error': 'Service unavailable'}), 500

            if user_id in self.carts:
                self.carts[user_id] = []

            return jsonify({
                'status': 'success',
                'message': 'Cart cleared'
            })

    def health_check(self):
        """Проверка здоровья сервиса"""
        current_time = time.time()

        # ПЛАНОВЫЕ ОТКАЗЫ - 3 ошибки подряд
        if self.failure_mode == 'scheduled':
            if self.failure_countdown > 0:
                self.failure_countdown -= 1
                remaining = self.failure_countdown + 1
                print(f"⏰ [SCHEDULED FAILURE] Cart Service падает ({remaining}/3)", flush=True)
                return jsonify({
                    'status': 'unhealthy',
                    'service': self.name,
                    'error': f'Scheduled failure ({remaining}/3)',
                    'mode': self.failure_mode
                }), 503
            else:
                return jsonify({
                    'status': 'healthy',
                    'service': self.name,
                    'total_carts': len(self.carts),
                    'total_items': sum(len(items) for items in self.carts.values()),
                    'mode': self.failure_mode,
                    'timestamp': current_time
                })

        # СЛУЧАЙНЫЕ ОТКАЗЫ
        elif self.failure_mode == 'random':
            if random.random() < 0.3:
                print(f"🎲 [RANDOM FAILURE] Cart Service падает случайно", flush=True)
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
                    'total_carts': len(self.carts),
                    'total_items': sum(len(items) for items in self.carts.values()),
                    'mode': self.failure_mode,
                    'timestamp': current_time
                })

        # БЕЗ ОТКАЗОВ (none)
        else:
            return jsonify({
                'status': 'healthy',
                'service': self.name,
                'total_carts': len(self.carts),
                'total_items': sum(len(items) for items in self.carts.values()),
                'mode': self.failure_mode,
                'timestamp': current_time
            })

    def should_fail(self) -> bool:
        """Определяет, должен ли сервис ответить ошибкой"""
        self.request_count += 1

        if self.failure_mode == 'random':
            return random.random() < 0.3

        elif self.failure_mode == 'scheduled':
            if self.failure_countdown > 0:
                self.failure_countdown -= 1
                return True
            return False

        return False

    def set_failure_mode(self, mode: str):
        """Установка режима отказа"""
        self.failure_mode = mode
        self.failure_countdown = 0
        if mode == 'scheduled':
            self.failure_countdown = 3
            print(f"🔄 Cart Service: режим '{mode}', запущено 3 последовательных отказа", flush=True)
        else:
            print(f"🔄 Cart Service: режим изменен на '{mode}'", flush=True)

    def run(self):
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        print(f"🛒 Cart Service запущен на порту {self.port} (режим: {self.failure_mode})", flush=True)
        self.app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)