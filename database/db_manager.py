"""
Менеджер базы данных
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional


class DatabaseManager:
    def __init__(self, db_path: str = "database/monitoring.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with open("database/schema.sql", "r", encoding="utf-8") as f:
            schema = f.read()

        conn = self.get_connection()
        conn.executescript(schema)
        conn.commit()
        conn.close()

    def get_connection(self):
        """Получение соединения с БД"""
        return sqlite3.connect(self.db_path)

    def save_metric(self, service_name: str, status: str, response_time_ms: float = None,
                    error_message: str = None, is_healthy: bool = None):
        """Сохранение метрики"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO metrics (service_name, timestamp, status, response_time_ms, error_message, is_healthy)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (service_name, datetime.now().timestamp(), status, response_time_ms, error_message, is_healthy))

        conn.commit()
        conn.close()

    def save_recovery_event(self, service_name: str, success: bool, method: str = None, details: str = None):
        """Сохранение события восстановления"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO recovery_events (service_name, timestamp, success, recovery_method, details)
            VALUES (?, ?, ?, ?, ?)
        """, (service_name, datetime.now().timestamp(), success, method, details))

        conn.commit()
        conn.close()

    def save_alert(self, service_name: str, severity: str, message: str):
        """Сохранение алерта"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alerts (service_name, timestamp, severity, message)
            VALUES (?, ?, ?, ?)
        """, (service_name, datetime.now().timestamp(), severity, message))

        conn.commit()
        conn.close()

    def get_recent_metrics(self, service_name: str = None, limit: int = 100) -> List[Dict]:
        """Получение последних метрик"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if service_name:
            cursor.execute("""
                SELECT * FROM metrics 
                WHERE service_name = ? 
                ORDER BY timestamp DESC LIMIT ?
            """, (service_name, limit))
        else:
            cursor.execute("""
                SELECT * FROM metrics 
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_recovery_stats(self) -> Dict:
        """Получение статистики восстановлений"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
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

    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Получение последних алертов"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM alerts 
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def acknowledge_alert(self, alert_id: int):
        """Подтверждение алерта"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()