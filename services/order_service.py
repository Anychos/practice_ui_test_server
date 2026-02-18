from services.api_client import APIClient
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self):
        self.api_client = APIClient()

    def create_order(self, cart_id):
        """
        Создание заказа из корзины через API
        Возвращает (success, message, order_data)
        """
        data = {
            "cart_id": cart_id
        }

        response = self.api_client.post('orders', data)

        if response and 'id' in response:
            return True, "Заказ успешно создан", response
        else:
            error_msg = self._get_error_message(response)
            logger.error(f"Failed to create order: {error_msg}")
            return False, error_msg, None

    def get_user_orders(self):
        """
        Получение заказов пользователя через API
        Возвращает (success, message, orders)
        """
        response = self.api_client.get('orders')

        if isinstance(response, list):
            return True, "Заказы загружены", response
        elif response and 'detail' in response:
            error_msg = response['detail']
            logger.error(f"Failed to get orders: {error_msg}")
            return False, error_msg, []
        else:
            error_msg = "Не удалось загрузить заказы"
            return False, error_msg, []

    def get_order_by_id(self, order_id):
        """
        Получение деталей заказа через API
        Возвращает (success, message, order)
        """
        response = self.api_client.get(f'orders/{order_id}')

        if response and 'id' in response:
            return True, "Заказ загружен", response
        else:
            error_msg = self._get_error_message(response)
            logger.error(f"Failed to get order {order_id}: {error_msg}")
            return False, error_msg, None

    def _get_error_message(self, response):
        """Извлечение сообщения об ошибке из ответа API"""
        if not response:
            return "Ошибка соединения с сервером"

        if 'detail' in response:
            return response['detail']
        elif 'message' in response:
            return response['message']
        elif 'error' in response:
            return response['error']
        else:
            return "Неизвестная ошибка"

    def format_order_date(self, date_string):
        """Форматирование даты заказа для отображения"""
        try:
            if not date_string:
                return "Дата не указана"

            # Пробуем разные форматы даты
            for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
                try:
                    dt = datetime.strptime(date_string, fmt)
                    return dt.strftime('%d.%m.%Y %H:%M')
                except ValueError:
                    continue

            return date_string
        except Exception as e:
            logger.error(f"Error formatting date {date_string}: {e}")
            return date_string
