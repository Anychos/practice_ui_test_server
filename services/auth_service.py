from services.api_client import APIClient, logger
from flask import session


class AuthService:
    def __init__(self):
        self.api_client = APIClient()

    def register(self, email, name, phone, password):
        """
        Регистрация пользователя через API
        Возвращает (success, message, data)
        """
        data = {
            "email": email,
            "name": name,
            "phone": phone,
            "password": password
        }

        response = self.api_client.post('register', data)

        if response and 'access_token' in response:
            # Сохраняем данные в сессии
            self._save_session(response)
            return True, "Регистрация успешна!", response['user']
        else:
            error_msg = self._get_error_message(response)
            return False, error_msg, None

    def login(self, email, password):
        """
        Авторизация пользователя через API
        Возвращает (success, message, data)
        """
        data = {
            "email": email,
            "password": password
        }

        response = self.api_client.post('login', data)

        if response and 'access_token' in response:
            # Сохраняем данные в сессии
            self._save_session(response)
            return True, "Вход выполнен успешно!", response['user']
        else:
            error_msg = self._get_error_message(response)
            return False, error_msg, None

    def _save_session(self, response):
        """Сохранение данных пользователя в сессии"""
        session['auth_token'] = response['access_token']
        session['user_id'] = response['user']['id']
        session['user_email'] = response['user']['email']
        session['user_name'] = response['user']['name']
        session['user_phone'] = response['user']['phone']
        session['is_admin'] = response['user']['is_admin']
        session.permanent = True

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

    def logout(self):
        """Выход из системы"""
        session.clear()
        return True, "Вы вышли из системы", None

    def is_authenticated(self):
        """Проверка авторизации"""
        return 'auth_token' in session

    def get_current_user(self):
        """Получение данных текущего пользователя"""
        if self.is_authenticated():
            return {
                'id': session.get('user_id'),
                'email': session.get('user_email'),
                'name': session.get('user_name'),
                'phone': session.get('user_phone'),
                'is_admin': session.get('is_admin', False)
            }
        return None

    def get_user_profile(self):
        """
        Получение профиля текущего пользователя через API
        Возвращает (success, message, user_data)
        """
        if not self.is_authenticated():
            return False, "Пользователь не авторизован", None

        response = self.api_client.get('user/me')

        if response and 'id' in response:
            # Обновляем данные в сессии
            session['user_id'] = response['id']
            session['user_email'] = response['email']
            session['user_name'] = response['name']
            session['user_phone'] = response.get('phone', '')
            session['is_admin'] = response.get('is_admin', False)

            return True, "Данные профиля получены", response
        else:
            error_msg = self._get_error_message(response)
            logger.error(f"Failed to get user profile: {error_msg}")
            return False, error_msg, None
