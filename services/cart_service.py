from services.api_client import APIClient
import logging

logger = logging.getLogger(__name__)


class CartService:
    def __init__(self):
        self.api_client = APIClient()

    def add_to_cart(self, product_id, quantity=1):
        """
        Добавление товара в корзину через API
        Возвращает (success, message, cart_item)
        """
        data = {
            "product_id": product_id,
            "quantity": quantity
        }

        response = self.api_client.post('cart/items', data)

        if response and 'cart_id' in response:
            return True, "Товар добавлен в корзину", response
        else:
            error_msg = self._get_error_message(response)
            logger.error(f"Failed to add to cart: {error_msg}")
            return False, error_msg, None

    def get_cart(self):
        """
        Получение корзины через API
        Возвращает (success, message, cart_data)
        """
        response = self.api_client.get('cart')

        if response and 'id' in response:
            return True, "Корзина загружена", response
        elif response and 'detail' in response:
            error_msg = response['detail']
            logger.error(f"Failed to get cart: {error_msg}")
            return False, error_msg, None
        else:
            error_msg = "Не удалось загрузить корзину"
            logger.error(f"Failed to get cart: {response}")
            return False, error_msg, None

    def update_cart_item(self, product_id, quantity):
        """
        Обновление количества товара в корзине
        Возвращает (success, message, updated_item)
        """
        data = {"quantity": quantity}
        response = self.api_client.put(f'cart/items/{product_id}', data)

        if response and 'product_id' in response:
            return True, "Количество обновлено", response
        else:
            error_msg = self._get_error_message(response)
            return False, error_msg, None

    def remove_from_cart(self, product_id):
        """
        Удаление товара из корзины
        Возвращает (success, message)
        """
        response = self.api_client.delete(f'cart/items/{product_id}')

        if response is not None:
            return True, "Товар удален из корзины", response
        else:
            error_msg = "Не удалось удалить товар из корзины"
            return False, error_msg, None

    def clear_cart(self):
        """
        Очистка всей корзины
        Пока заглушка - будет реализовано позже, если есть API метод
        """
        # TODO: Если есть метод для очистки всей корзины, реализовать его
        # Пока просто удаляем все товары по одному
        success, message, cart_data = self.get_cart()
        if success and cart_data and 'items' in cart_data:
            for item in cart_data['items']:
                self.remove_from_cart(item['product_id'])
            return True, "Корзина очищена", None
        return True, "Корзина уже пуста", None

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
