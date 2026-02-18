from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from config import Config
from services import CartService, OrderService
from services.auth_service import AuthService
from services.product_service import ProductService
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Инициализируем сервисы
auth_service = AuthService()
product_service = ProductService()
cart_service = CartService()
order_service = OrderService()


# Главная страница
@app.route('/')
def index():
    user = auth_service.get_current_user()

    # Получаем товары через API
    success, message, products = product_service.get_all_products()

    if not success:
        flash(f'Ошибка загрузки товаров: {message}', 'warning')
        products = []

    return render_template('index.html',
                           title="Главная",
                           user=user,
                           products=products)


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Если пользователь уже авторизован, перенаправляем на главную
    if auth_service.is_authenticated():
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Получаем данные из формы
        email = request.form.get('email', '').strip()
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        # Базовая валидация
        if not all([email, name, phone, password]):
            flash('Все поля обязательны для заполнения', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Пароль должен быть не менее 6 символов', 'danger')
            return render_template('register.html')

        # Регистрация через API
        success, message, user_data = auth_service.register(email, name, phone, password)

        if success:
            flash(message, 'success')
            return redirect(url_for('index'))
        else:
            flash(f'Ошибка: {message}', 'danger')
            return render_template('register.html',
                                   email=email, name=name, phone=phone)

    return render_template('register.html')


# Страница логина
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже авторизован, перенаправляем на главную
    if auth_service.is_authenticated():
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Получаем данные из формы
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember') == 'on'

        # Базовая валидация
        if not email or not password:
            flash('Введите email и пароль', 'danger')
            return render_template('login.html', email=email)

        # Авторизация через API
        success, message, user_data = auth_service.login(email, password)

        if success:
            # Если выбрано "Запомнить меня", устанавливаем длительную сессию
            if remember:
                session.permanent = True
            else:
                session.permanent = False

            flash(message, 'success')

            # Перенаправляем на главную или на страницу, куда хотел попасть пользователь
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash(f'Ошибка входа: {message}', 'danger')
            return render_template('login.html', email=email, demo_credentials=True)

    # Для GET запроса показываем форму
    return render_template('login.html', demo_credentials=True)


# Выход из системы
@app.route('/logout')
def logout():
    success, message, _ = auth_service.logout()
    if success:
        flash(message, 'info')
    return redirect(url_for('index'))


# Защищенные роуты (декоратор для проверки авторизации)
def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth_service.is_authenticated():
            # Для API запросов возвращаем JSON ошибку
            if request.path.startswith('/api/') or request.path.startswith('/cart/'):
                return jsonify({
                    'error': 'Необходимо авторизоваться',
                    'auth_required': True
                }), 401
            # Для обычных страниц - редирект
            else:
                flash('Для доступа к этой странице необходимо авторизоваться', 'warning')
                return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/profile')
@login_required
def profile():
    # Получаем свежие данные профиля через API
    success, message, user_data = auth_service.get_user_profile()

    if not success:
        flash(f'Ошибка загрузки профиля: {message}', 'danger')
        return redirect(url_for('index'))

    # Заглушка для заказов (пока нет API)
    orders = []  # В будущем получим через API

    return render_template('profile.html',
                           title="Мой профиль",
                           user=user_data,
                           orders=orders)


# Страница деталей товара
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # Получаем товар через API
    success, message, product = product_service.get_product_by_id(product_id)

    if not success:
        flash(f'Ошибка загрузки товара: {message}', 'danger')
        return redirect(url_for('index'))

    user = auth_service.get_current_user()

    return render_template('product_detail.html',
                           title=product['name'],
                           user=user,
                           product=product)


# API endpoint для добавления в корзину
@app.route('/cart/items', methods=['POST'])
@login_required
def api_add_to_cart():
    """API endpoint для добавления товара в корзину"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        if not product_id:
            return jsonify({
                'error': 'Не указан ID товара'
            }), 400

        # Добавляем товар в корзину через API
        success, message, cart_item = cart_service.add_to_cart(product_id, quantity)

        if success:
            # Возвращаем в формате, соответствующем вашему curl-запросу
            return jsonify({
                'product_id': product_id,
                'quantity': quantity,
                'cart_id': cart_item.get('cart_id', 1)  # Предполагаем, что cart_item содержит cart_id
            })
        else:
            return jsonify({
                'error': message
            }), 400

    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        return jsonify({
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500


# Страница корзины
@app.route('/cart')
@login_required
def cart():
    """Страница корзины"""
    # Получаем корзину через API
    success, message, cart_data = cart_service.get_cart()

    if not success:
        # Если корзина не найдена (например, пустая), создаем пустую структуру
        if message and "не найден" in message.lower():
            cart_data = {
                'id': None,
                'user_id': session.get('user_id'),
                'total_quantity': 0,
                'total_price': 0,
                'items': []
            }
        else:
            flash(f'Ошибка загрузки корзины: {message}', 'danger')
            cart_data = {
                'id': None,
                'user_id': session.get('user_id'),
                'total_quantity': 0,
                'total_price': 0,
                'items': []
            }

    # Если корзина есть, обрабатываем товары
    cart_items = []
    if cart_data and 'items' in cart_data:
        for item in cart_data['items']:
            # Формируем структуру для шаблона
            cart_item = {
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'product_name': item.get('product_name', f'Товар #{item["product_id"]}'),
                'product_price': item.get('product_price', 0),
                'product_image_url': item.get('product_image_url'),
                'is_available': item.get('is_available', True),
                'has_enough_stock': item.get('has_enough_stock', True),
                'available_quantity': item.get('available_quantity', 0),
                'item_total': item.get('product_price', 0) * item.get('quantity', 1)
            }
            cart_items.append(cart_item)

    user = auth_service.get_current_user()

    return render_template('cart.html',
                           title="Корзина",
                           user=user,
                           cart=cart_data,
                           cart_items=cart_items,
                           total_price=cart_data.get('total_price', 0) if cart_data else 0,
                           total_items=cart_data.get('total_quantity', 0) if cart_data else 0)


# API для обновления количества товара в корзине
@app.route('/cart/items/<int:product_id>', methods=['PUT'])
@login_required
def api_update_cart_item(product_id):
    """API endpoint для обновления количества товара в корзине"""
    try:
        data = request.get_json()
        quantity = data.get('quantity')

        if quantity is None or quantity < 1:
            return jsonify({
                'success': False,
                'message': 'Некорректное количество'
            }), 400

        # Обновляем количество через API
        success, message, updated_item = cart_service.update_cart_item(product_id, quantity)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'updated_item': updated_item
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        logger.error(f"Error updating cart item: {e}")
        return jsonify({
            'success': False,
            'message': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500


# API для удаления товара из корзины
@app.route('/cart/items/<int:product_id>', methods=['DELETE'])
@login_required
def api_remove_from_cart(product_id):
    """API endpoint для удаления товара из корзины"""
    try:
        # Удаляем товар через API
        success, message, _ = cart_service.remove_from_cart(product_id)

        if success:
            return jsonify({
                'message': message or 'Продукт удален из корзины'
            })
        else:
            return jsonify({
                'error': message or 'Ошибка при удалении товара'
            }), 400

    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        return jsonify({
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500


# API для очистки корзины
@app.route('/cart', methods=['DELETE'])
@login_required
def api_clear_cart():
    """API endpoint для очистки корзины"""
    try:
        # Очищаем корзину через API
        success, message, _ = cart_service.clear_cart()

        if success:
            return jsonify({
                'message': message or 'Корзина очищена'
            })
        else:
            return jsonify({
                'error': message or 'Ошибка при очистке корзины'
            }), 400

    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        return jsonify({
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500


# API для создания заказа
@app.route('/api/orders/create', methods=['POST'])
@login_required
def api_create_order():
    """API endpoint для создания заказа из корзины"""
    try:
        data = request.get_json()
        cart_id = data.get('cart_id')

        if not cart_id:
            return jsonify({
                'success': False,
                'message': 'Не указан ID корзины'
            }), 400

        # Создаем заказ через API
        success, message, order_data = order_service.create_order(cart_id)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'order': order_data
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return jsonify({
            'success': False,
            'message': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500


# Страница оформления заказа
@app.route('/checkout')
@login_required
def checkout():
    """Страница оформления заказа"""
    # Получаем корзину через API
    success, message, cart_data = cart_service.get_cart()

    if not success:
        flash(f'Ошибка загрузки корзины: {message}', 'danger')
        return redirect(url_for('cart'))

    # Проверяем, есть ли товары в корзине
    if not cart_data or 'items' not in cart_data or len(cart_data['items']) == 0:
        flash('Ваша корзина пуста. Добавьте товары для оформления заказа.', 'warning')
        return redirect(url_for('index'))

    # Формируем список товаров для шаблона
    cart_items = []
    for item in cart_data['items']:
        cart_item = {
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'product_name': item.get('product_name', f'Товар #{item["product_id"]}'),
            'product_price': item.get('product_price', 0),
            'item_total': item.get('product_price', 0) * item.get('quantity', 1)
        }
        cart_items.append(cart_item)

    user = auth_service.get_current_user()

    return render_template('checkout.html',
                           title="Оформление заказа",
                           user=user,
                           cart=cart_data,
                           cart_items=cart_items)


# Страница успешного оформления заказа
@app.route('/orders/<int:order_id>')
@login_required
def order_success(order_id):
    """Страница успешного оформления заказа"""
    # Получаем информацию о заказе через API
    success, message, order_data = order_service.get_order_by_id(order_id)

    if not success:
        flash(f'Ошибка загрузки заказа: {message}', 'danger')
        return redirect(url_for('index'))

    # Проверяем, принадлежит ли заказ текущему пользователю
    if order_data.get('user_id') != session.get('user_id'):
        flash('У вас нет доступа к этому заказу', 'danger')
        return redirect(url_for('index'))

    user = auth_service.get_current_user()

    # Форматируем дату заказа
    if order_data.get('created_at'):
        order_data['formatted_date'] = order_service.format_order_date(order_data['created_at'])
    else:
        order_data['formatted_date'] = 'Дата не указана'

    return render_template('order_success.html',
                           title=f"Заказ #{order_id}",
                           user=user,
                           order=order_data)


# Страница списка заказов
@app.route('/orders')
@login_required
def orders():
    """Страница списка заказов пользователя"""
    # Получаем заказы пользователя через API
    success, message, orders_data = order_service.get_user_orders()

    if not success:
        # Если заказов нет или ошибка, показываем пустой список
        if message and "не найдены" in message.lower():
            orders_data = []
        else:
            flash(f'Ошибка загрузки заказов: {message}', 'warning')
            orders_data = []

    # Форматируем даты заказов
    for order in orders_data:
        if order.get('created_at'):
            order['formatted_date'] = order_service.format_order_date(order['created_at'])
        else:
            order['formatted_date'] = 'Дата не указана'

    user = auth_service.get_current_user()

    return render_template('orders.html',
                           title="Мои заказы",
                           user=user,
                           orders=orders_data)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
