"""
Модуль отправки уведомлений (алертов)
"""

import requests
import json
import os
from datetime import datetime
from typing import Optional


class AlertManager:
    """Менеджер отправки алертов"""

    def __init__(self, telegram_token: str = None, telegram_chat_id: str = None):
        self.telegram_token = telegram_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = telegram_chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.alert_history = []

    def send_telegram(self, message: str, priority: str = "warning") -> bool:
        """Отправка алерта в Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            print(f"📱 [TELEGRAM] {message}")
            return False

        emoji = {
            'critical': '🔴',
            'warning': '🟡',
            'info': '🔵'
        }.get(priority, '⚪')

        formatted_message = f"{emoji} *АЛЕРТ* {emoji}\n\n{message}\n\n🕐 {datetime.now().strftime('%H:%M:%S')}"

        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            response = requests.post(
                url,
                json={
                    'chat_id': self.telegram_chat_id,
                    'text': formatted_message,
                    'parse_mode': 'Markdown'
                },
                timeout=5
            )

            if response.status_code == 200:
                self.alert_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': message,
                    'priority': priority,
                    'success': True
                })
                return True
            else:
                print(f"❌ Ошибка Telegram: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Ошибка отправки в Telegram: {e}")
            return False

    def send_webhook(self, webhook_url: str, data: dict) -> bool:
        """Отправка алерта на webhook"""
        try:
            response = requests.post(webhook_url, json=data, timeout=3)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            return False

    def get_history(self, limit: int = 20):
        """Получение истории алертов"""
        return self.alert_history[-limit:]