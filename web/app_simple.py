"""
Упрощенный веб-интерфейс системы мониторинга
"""

from flask import Flask, jsonify, render_template_string
import requests

simple_app = Flask(__name__)

# HTML шаблон прямо в коде
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Мониторинг микросервисов</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
        }
        .status-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px;
            display: inline-block;
            width: 250px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .healthy {
            color: green;
            font-weight: bold;
        }
        .unhealthy {
            color: red;
            font-weight: bold;
        }
        .degraded {
            color: orange;
            font-weight: bold;
        }
        .status-list {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px;
        }
        .service-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Система мониторинга микросервисов</h1>

        <div style="text-align: center;">
            <div class="status-card">
                <h3>User Service</h3>
                <p>Порт: 8001</p>
                <p>Статус: <span id="user-status" class="unknown">Загрузка...</span></p>
                <button onclick="checkService(8001)">Проверить</button>
            </div>

            <div class="status-card">
                <h3>Payment Service</h3>
                <p>Порт: 8002</p>
                <p>Статус: <span id="payment-status" class="unknown">Загрузка...</span></p>
                <button onclick="checkService(8002)">Проверить</button>
            </div>

            <div class="status-card">
                <h3>Gateway Service</h3>
                <p>Порт: 8000</p>
                <p>Статус: <span id="gateway-status" class="unknown">Загрузка...</span></p>
                <button onclick="checkService(8000)">Проверить</button>
            </div>
        </div>

        <div class="status-list">
            <h3>📢 Последние алерты</h3>
            <div id="alerts"></div>
        </div>
    </div>

    <script>
        async function updateStatus() {
            const response = await fetch('/api/status');
            const data = await response.json();

            for (const [service, info] of Object.entries(data)) {
                const prefix = service.split('-')[0];
                const el = document.getElementById(`${prefix}-status`);
                if (el) {
                    el.textContent = info.status;
                    el.className = info.status;
                }
            }
        }

        async function loadAlerts() {
            const response = await fetch('/api/alerts');
            const alerts = await response.json();
            const alertsDiv = document.getElementById('alerts');

            if (alerts.length === 0) {
                alertsDiv.innerHTML = '<p>Нет алертов</p>';
                return;
            }

            alertsDiv.innerHTML = alerts.slice(0, 10).map(alert => `
                <div class="service-item">
                    <strong>${alert.service_name}</strong> - ${alert.message}
                    <br><small>${new Date(alert.timestamp * 1000).toLocaleString()}</small>
                </div>
            `).join('');
        }

        async function checkService(port) {
            const names = {8001: 'User', 8002: 'Payment', 8000: 'Gateway'};
            try {
                const response = await fetch(`http://localhost:${port}/health`);
                const data = await response.json();
                alert(`${names[port]} Service: ${data.status}`);
            } catch(e) {
                alert(`${names[port]} Service: НЕДОСТУПЕН!`);
            }
        }

        updateStatus();
        loadAlerts();
        setInterval(updateStatus, 3000);
        setInterval(loadAlerts, 5000);
    </script>
</body>
</html>
'''


@simple_app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@simple_app.route('/api/status')
def api_status():
    try:
        services = {}

        # Проверка user-service
        try:
            r = requests.get('http://127.0.0.1:8001/health', timeout=2)
            user_status = 'healthy' if r.status_code == 200 and r.json().get('status') == 'healthy' else 'degraded'
        except:
            user_status = 'critical'

        # Проверка payment-service
        try:
            r = requests.get('http://127.0.0.1:8002/health', timeout=2)
            payment_status = 'healthy' if r.status_code == 200 and r.json().get('status') == 'healthy' else 'degraded'
        except:
            payment_status = 'critical'

        # Проверка gateway-service
        try:
            r = requests.get('http://127.0.0.1:8000/health', timeout=2)
            gateway_status = 'healthy' if r.status_code == 200 and r.json().get('status') == 'healthy' else 'degraded'
        except:
            gateway_status = 'critical'

        return jsonify({
            'user-service': {'status': user_status, 'failures': 0, 'threshold': 3},
            'payment-service': {'status': payment_status, 'failures': 0, 'threshold': 3},
            'gateway-service': {'status': gateway_status, 'failures': 0, 'threshold': 3}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@simple_app.route('/api/alerts')
def api_alerts():
    # Простые тестовые алерты
    import time
    return jsonify([
        {
            'service_name': 'payment-service',
            'timestamp': time.time(),
            'message': 'Сервис временно недоступен',
            'severity': 'warning'
        }
    ])


def run_simple_web():
    simple_app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    run_simple_web()