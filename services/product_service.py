from services.api_client import APIClient
import logging

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self):
        self.api_client = APIClient()

    def get_all_products(self, page=1, limit=20):
        """
        Получение списка товаров через API
        Возвращает (success, message, products)
        """
        params = {
            'page': page,
            'limit': limit
        }

        response = self.api_client.get('products', params)

        if isinstance(response, list):
            return True, "Товары успешно загружены", response
        elif response and 'detail' in response:
            error_msg = response['detail']
            logger.error(f"Failed to get products: {error_msg}")
            return False, error_msg, []
        else:
            error_msg = "Не удалось загрузить товары"
            logger.error(f"Failed to get products: {response}")
            return False, error_msg, []

    def get_product_by_id(self, product_id):
        """
        Получение товара по ID через API
        Возвращает (success, message, product)
        """
        response = self.api_client.get(f'products/{product_id}')

        if response and 'id' in response:
            return True, "Товар успешно загружен", response
        else:
            error_msg = "Не удалось загрузить товар"
            if response and 'detail' in response:
                error_msg = response['detail']
            logger.error(f"Failed to get product {product_id}: {error_msg}")
            return False, error_msg, None

    def search_products(self, query, category=None, min_price=None, max_price=None):
        """
        Поиск товаров через API
        Пока заглушка - будет реализовано позже
        """
        params = {'search': query}
        if category:
            params['category'] = category
        if min_price is not None:
            params['min_price'] = min_price
        if max_price is not None:
            params['max_price'] = max_price

        response = self.api_client.get('products', params)

        if isinstance(response, list):
            return True, "Результаты поиска загружены", response
        else:
            error_msg = "Не удалось выполнить поиск"
            return False, error_msg, []
