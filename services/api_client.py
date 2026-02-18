import requests
import json
from flask import session, current_app
from config import Config
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self):
        self.base_url = Config.API_BASE_URL
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def _add_auth_token(self, headers):
        """Добавляем токен авторизации из сессии если есть"""
        if 'auth_token' in session:
            headers['Authorization'] = f'Bearer {session.get("auth_token")}'
        return headers

    def _get_headers(self):
        """Получаем заголовки с авторизацией"""
        headers = self.default_headers.copy()
        return self._add_auth_token(headers)

    def _handle_response(self, response):
        """Обработка ответа от API"""
        try:
            if response.status_code == 204:  # No Content
                return {}

            response_data = response.json()

            if response.status_code >= 400:
                logger.error(f"API Error {response.status_code}: {response_data}")

            return response_data

        except ValueError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                'error': 'Invalid JSON response',
                'status_code': response.status_code,
                'text': response.text[:200] if response.text else ''
            }

    def get(self, endpoint, params=None):
        """GET запрос к вашему API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            logger.info(f"GET {url}")
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=10
            )
            return self._handle_response(response)

        except requests.exceptions.Timeout:
            logger.error(f"Timeout error for GET {url}")
            return {'error': 'Request timeout', 'detail': 'Сервер не отвечает'}

        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for GET {url}")
            return {'error': 'Connection error', 'detail': 'Не удалось подключиться к серверу'}

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for GET {url}: {e}")
            return {'error': 'Request failed', 'detail': str(e)}

    def post(self, endpoint, data=None):
        """POST запрос к вашему API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            logger.info(f"POST {url} - Data: {json.dumps(data)[:200]}...")
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=10
            )
            return self._handle_response(response)

        except requests.exceptions.Timeout:
            logger.error(f"Timeout error for POST {url}")
            return {'error': 'Request timeout', 'detail': 'Сервер не отвечает'}

        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for POST {url}")
            return {'error': 'Connection error', 'detail': 'Не удалось подключиться к серверу'}

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for POST {url}: {e}")
            return {'error': 'Request failed', 'detail': str(e)}

    def put(self, endpoint, data=None):
        """PUT запрос к вашему API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            logger.info(f"PUT {url}")
            response = requests.put(
                url,
                headers=headers,
                json=data,
                timeout=10
            )
            return self._handle_response(response)

        except requests.exceptions.Timeout:
            logger.error(f"Timeout error for PUT {url}")
            return {'error': 'Request timeout'}

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for PUT {url}: {e}")
            return {'error': 'Request failed', 'detail': str(e)}

    def delete(self, endpoint):
        """DELETE запрос к вашему API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            logger.info(f"DELETE {url}")
            response = requests.delete(
                url,
                headers=headers,
                timeout=10
            )
            return self._handle_response(response)

        except requests.exceptions.Timeout:
            logger.error(f"Timeout error for DELETE {url}")
            return {'error': 'Request timeout'}

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for DELETE {url}: {e}")
            return {'error': 'Request failed', 'detail': str(e)}

    def patch(self, endpoint, data=None):
        """PATCH запрос к вашему API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            logger.info(f"PATCH {url}")
            response = requests.patch(
                url,
                headers=headers,
                json=data,
                timeout=10
            )
            return self._handle_response(response)

        except requests.exceptions.Timeout:
            logger.error(f"Timeout error for PATCH {url}")
            return {'error': 'Request timeout'}

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for PATCH {url}: {e}")
            return {'error': 'Request failed', 'detail': str(e)}
