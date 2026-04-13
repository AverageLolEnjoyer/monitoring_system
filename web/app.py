"""
Веб-интерфейс системы мониторинга
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import requests
import time
import sqlite3

web_app = Flask(__name__)
web_app.config['SECRET_KEY'] = 'monitoring-secret-key'
socketio = SocketIO(web_app, cors_allowed_origins="*")

# Глобальные переменные
monitor_instance = None
db_instance = None
payment_service_instance = None

monitor_instance = None
db_instance = None
payment_service_instance = None
cart_service_instance = None  # Добавляем

def set_payment_service(service):
    global payment_service_instance
    payment_service_instance = service

def set_cart_service(service):
    global cart_service_instance
    cart_service_instance = service


def set_monitor(monitor):
    global monitor_instance
    monitor_instance = monitor

def set_db(db):
    global db_instance
    db_instance = db

def set_payment_service(service):
    global payment_service_instance
    payment_service_instance = service

# ============= HTML СТРАНИЦЫ =============

@web_app.route('/')
def dashboard():
    return render_template('dashboard.html')

@web_app.route('/services')
def services_page():
    return render_template('services.html')

@web_app.route('/recovery')
def recovery_page():
    return render_template('recovery_log.html')

# ============= API ENDPOINTS =============

@web_app.route('/api/status')
def api_status():
    if monitor_instance:
        return jsonify(monitor_instance.get_status())

    status = {}
    services = ['user-service', 'payment-service', 'gateway-service']
    ports = {'user-service': 8001, 'payment-service': 8002, 'gateway-service': 8000}

    for service in services:
        port = ports[service]
        try:
            r = requests.get(f'http://127.0.0.1:{port}/health', timeout=2)
            if r.status_code == 200 and r.json().get('status') == 'healthy':
                status[service] = {'status': 'healthy', 'failures': 0, 'threshold': 3}
            else:
                status[service] = {'status': 'degraded', 'failures': 1, 'threshold': 3}
        except:
            status[service] = {'status': 'critical', 'failures': 3, 'threshold': 3}

    return jsonify(status)

@web_app.route('/api/metrics')
def api_metrics():
    if db_instance:
        limit = request.args.get('limit', 100, type=int)
        metrics = db_instance.get_recent_metrics(limit=limit)
        return jsonify(metrics)
    return jsonify([])

@web_app.route('/api/alerts')
def api_alerts():
    if db_instance:
        limit = request.args.get('limit', 50, type=int)
        alerts = db_instance.get_alerts(limit=limit)
        return jsonify(alerts)

    return jsonify([
        {
            'id': 1,
            'service_name': 'payment-service',
            'timestamp': time.time(),
            'severity': 'warning',
            'message': 'Сервис временно недоступен',
            'acknowledged': 0
        }
    ])

@web_app.route('/api/recovery-stats')
def api_recovery_stats():
    if db_instance:
        stats = db_instance.get_recovery_stats()
        return jsonify(stats)

    return jsonify({
        'total_recoveries': 0,
        'successful_recoveries': 0,
        'success_rate': 0
    })

@web_app.route('/api/recovery-events')
def api_recovery_events():
    try:
        conn = sqlite3.connect('database/monitoring.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, service_name, timestamp, success, recovery_method, details
            FROM recovery_events 
            ORDER BY timestamp DESC 
            LIMIT 100
        """)

        rows = cursor.fetchall()
        conn.close()

        events = []
        for row in rows:
            events.append({
                'id': row['id'],
                'service_name': row['service_name'],
                'timestamp': row['timestamp'],
                'success': bool(row['success']),
                'recovery_method': row['recovery_method'],
                'details': row['details']
            })

        return jsonify(events)
    except Exception as e:
        return jsonify({'error': str(e), 'events': []})


@web_app.route('/api/set-failure-mode', methods=['POST'])
def set_failure_mode():
    """API: установка режима отказа для сервиса"""
    data = request.json
    service = data.get('service')
    mode = data.get('mode')

    if service == 'payment':
        if payment_service_instance:
            payment_service_instance.set_failure_mode(mode)
            return jsonify({
                'status': 'success',
                'message': f'Payment Service: режим изменен на {mode}',
                'mode': mode
            })
    elif service == 'cart':
        if cart_service_instance:
            cart_service_instance.set_failure_mode(mode)
            return jsonify({
                'status': 'success',
                'message': f'Cart Service: режим изменен на {mode}',
                'mode': mode
            })

    return jsonify({'status': 'error', 'message': 'Service not found'}), 404

@web_app.route('/api/check-service')
def api_check_service():
    port = request.args.get('port', type=int)
    name = request.args.get('name')

    if not port:
        return jsonify({'error': 'Port required'}), 400

    try:
        response = requests.get(f'http://127.0.0.1:{port}/health', timeout=3)
        data = response.json()
        return jsonify({
            'success': True,
            'status': data.get('status', 'unknown'),
            'response_time': f'{response.elapsed.total_seconds()*1000:.0f}ms'
        })
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Timeout'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 503

@socketio.on('request_update')
def handle_update_request():
    if monitor_instance and db_instance:
        emit('status_update', monitor_instance.get_status())
        emit('metrics_update', db_instance.get_recent_metrics(limit=50))

def start_web_interface(port=5000, monitor=None, db=None):
    set_monitor(monitor)
    set_db(db)
    socketio.run(web_app, host='0.0.0.0', port=port, debug=False)