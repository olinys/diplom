from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm, UserProfileForm, ProductForm, CategoryForm, PickupPointForm, SubcategoryForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Cart, UserProfile, Product, Category, User, PickupPoint, Order, OrderProduct, Notification, Review, Subcategory, Processor, OperatingSystem, ConnectionType, Color, ConnectorType, Memory, RAM, CoreCount, ScreenDiagonal, BatteryCapacity, Camera, CpuFrequency
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
import json
from django.views.decorators.http import require_POST

# РЕГИСТРАЦИЯ
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save() 
            login(request, user) 
            return redirect('home') 
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

# АВТОРИЗАЦИЯ
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)

                    # Быстрый переход в админку для суперпользователей
                    if user.is_superuser:
                        return redirect('/admin/')
                    return redirect('home')
                else:
                    messages.error(request, "Ваша учетная запись отключена.")
            else:
                messages.error(request, "Неправильное имя пользователя или пароль")
        else:
            messages.error(request, "Ошибка валидации. Проверьте введенные данные")

    form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

# ПОСЛЕ ВХОДА НАПРАВЛЯЕТ НА ГЛАВНУЮ
def logout_view(request):
    logout(request)
    return redirect('home')

# ЗАПОЛНЕНИЕ ПРОФИЛЯ ДАННЫМИ
@login_required
def profile(request):
    # Получаем профиль текущего пользователя
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    form = UserProfileForm(instance=user_profile)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            print("Форма прошла валидацию")
            form.save()
            print("Профиль сохранён:", user_profile.first_name, user_profile.last_name)
            return redirect('profile')  # Перенаправление на страницу профиля после сохранения
        else:
            print("Форма НЕ прошла валидацию:", form.errors)
    return render(request, 'accounts/profile.html', {'form': form})


def is_admin(user):
    return user.is_superuser

# ДОБАВЛЕНИЕ ТОВАРОВ
@user_passes_test(is_admin)
def add_product(request):
    if request.method == "POST":
        product_form = ProductForm(request.POST, request.FILES)
        if product_form.is_valid():
            product = product_form.save(commit=False)
            
            # Обрабатываем параметры
            param_fields = {
                'memory': Memory,
                'ram': RAM,
                'core_count': CoreCount,
                'color': Color,
                'screen_diagonal': ScreenDiagonal,
                'battery_capacity': BatteryCapacity,
                'operating_system': OperatingSystem,
                'main_camera': Camera,
                'front_camera': Camera,
                'processor': Processor,
                'connector_type': ConnectorType,
                'connection_type': ConnectionType,
                'cpu_frequency': CpuFrequency
            }
            
            for field, model in param_fields.items():
                value = request.POST.get(field)
                if value:
                    if value.isdigit():  # Если передается ID существующего объекта
                        obj = model.objects.get(id=value)
                    else:  # Если передается новое значение
                        field_name = 'name' if hasattr(model(), 'name') else 'value'
                        obj, created = model.objects.get_or_create(**{field_name: value})
                    setattr(product, field, obj)
            
            product.save()
            return redirect("home")
    else:
        product_form = ProductForm()
    
    return render(request, "accounts/add_product.html", {"product_form": product_form})


# ДОБАВЛЕНИЕ КАТЕГОРИИ
@user_passes_test(is_admin)
def add_category(request):
    if request.method == "POST":
        category_form = CategoryForm(request.POST)
        if category_form.is_valid():
            category_form.save()
            # После добавления категории перенаправляем на страницу добавления подкатегории
            return redirect('add_category')
    else:
        category_form = CategoryForm()

    return render(request, "accounts/add_category.html", {"category_form": category_form})

@user_passes_test(is_admin)
def add_subcategory(request):
    if request.method == "POST":
        subcategory_form = SubcategoryForm(request.POST)
        if subcategory_form.is_valid():
            subcategory_form.save()
            # После добавления подкатегории остаемся на той же странице
            return redirect('add_subcategory')
    else:
        subcategory_form = SubcategoryForm()

    return render(request, "accounts/add_subcategory.html", {"subcategory_form": subcategory_form})

@user_passes_test(is_admin)
def get_subcategories(request, category_id):
    try:
        subcategories = Subcategory.objects.filter(category_id=category_id)
        subcategory_data = [{'id': sub.id, 'name': sub.name} for sub in subcategories]
        return JsonResponse({'subcategories': subcategory_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    

@require_POST
def add_parameter_value(request):
    try:
        data = json.loads(request.body)
        model_name = data.get('model')
        value = data.get('value')
        
        MODEL_MAPPING = {
            'memory': (Memory, 'value'),
            'ram': (RAM, 'value'),
            'core_count': (CoreCount, 'value'),
            'color': (Color, 'name'),
            'screen_diagonal': (ScreenDiagonal, 'value'),
            'battery_capacity': (BatteryCapacity, 'value'),
            'operating_system': (OperatingSystem, 'name'),
            'main_camera': (Camera, 'value'),
            'front_camera': (Camera, 'value'),
            'processor': (Processor, 'name'),
            'connector_type': (ConnectorType, 'name'),
            'connection_type': (ConnectionType, 'type'),
            'cpu_frequency': (CpuFrequency, 'name')
        }
        
        if model_name not in MODEL_MAPPING:
            return JsonResponse({'success': False, 'error': 'Invalid model name'})
        
        Model, field_name = MODEL_MAPPING[model_name]
        new_param, created = Model.objects.get_or_create(**{field_name: value})
        
        return JsonResponse({
            'success': True,
            'id': new_param.id,
            'value': new_param.display_value()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
        
# ОТОБРАЖЕНИЕ ТОВАРОВ НА ГЛАВНОЙ СТРАНИЦК
def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})

# ДОБАВЛЕНИЕ ТОВАРОВ В КОРЗИНУ
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    
    if product.stock_quantity <= 0:
        messages.error(request, f"Товара {product.name} больше нет в наличии!")
        return redirect('home')

    if request.user.is_authenticated:
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        if not created:
            if cart_item.quantity < product.stock_quantity:
                cart_item.quantity += 1 
            else:
                messages.error(request, f"Недостаточно товара {product.name} в наличии!")
                return redirect('cart')
        cart_item.save()
    else:
        cart = request.session.get('cart', [])
        for item in cart:
            if item['product_id'] == product.id:
                if item['quantity'] < product.stock_quantity:
                    item['quantity'] += 1
                else:
                    messages.error(request, f"Недостаточно товара {product.name} в наличии!")
                    return redirect('cart')
                break
        else:
            cart.append({'product_id': product.id, 'quantity': 1})
        request.session['cart'] = cart

    messages.success(request, f'{product.name} добавлен в корзину!')
    return redirect('cart')

# ПРОСМОТР КОРЗИНЫ
def view_cart(request):
    cart_items = []
    total_sum = 0

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user)
        for item in cart:
            item_total = item.product.price * item.quantity
            total_sum += item_total
            cart_items.append({
                'product': item.product,
                'quantity': item.quantity,
                'total_price': item_total
            })
    else:
        cart = request.session.get('cart', [])
        for item in cart:
            product = Product.objects.get(id=item['product_id'])
            item_total = product.price * item['quantity']
            total_sum += item_total
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'total_price': item_total
            })

    return render(request, 'accounts/cart.html', {'cart_items': cart_items, 'total_sum': total_sum})

# РЕДАКТИРОВАНИЕ ТОВАРА
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = ProductForm(instance=product)
    return render(request, "edit_product.html", {"form": form, "product": product})

# УДАЛЕНИЕ ТОВАРА
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product.delete()
        return redirect("home") 
    return render(request, "delete_product.html", {"product": product})

# УДАЛЕНИЕ ТОВАРА ИЗ КОРЗИНЫ
def remove_from_cart(request, product_id):
    if request.user.is_authenticated:
        Cart.objects.filter(user=request.user, product_id=product_id).delete()
    else:
        cart = request.session.get('cart', [])
        cart = [item for item in cart if item['product_id'] != product_id]
        request.session['cart'] = cart
    return redirect('cart')

# ИЗМЕНЕНИЕ КОЛИЧЕСТВА В КОРЗИНЕ
def update_cart_item(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')  

    product = get_object_or_404(Product, id=product_id)
    cart_item = Cart.objects.filter(user=request.user, product=product).first()

    if not cart_item:
        return HttpResponseBadRequest("Product not in cart.")

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        if quantity < 1 or quantity > product.stock_quantity:
            messages.error(request, f"Please enter a valid quantity between 1 and {product.stock_quantity}.")
            return redirect('cart')  

        cart_item.quantity = quantity
        cart_item.save()

        messages.success(request, f"Quantity of {product.name} updated successfully.")
        return redirect('cart') 

    return HttpResponseBadRequest("Invalid request method.")

# ПРОСМОТР КАТАЛОГА
def catalog_view(request, category_id=None, subcategory_id=None):
    categories = Category.objects.all()
    sort = request.GET.get('sort')

    if subcategory_id:
        products = Product.objects.filter(subcategory_id=subcategory_id)
    elif category_id:
        products = Product.objects.filter(category_id=category_id)
    else:
        products = Product.objects.all()

    # Применяем сортировку
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'rating_asc':
        products = products.order_by('average_rating')
    elif sort == 'rating_desc':
        products = products.order_by('-average_rating')

    subcategories = None
    if category_id:
        subcategories = Subcategory.objects.filter(category_id=category_id)

    return render(request, 'accounts/catalog.html', {
        'categories': categories,
        'products': products,
        'subcategories': subcategories,
        'current_category_id': category_id,
        'current_subcategory_id': subcategory_id,
        'current_sort': sort,
    })


# ПОИСКОВАЯ СТРОКА
def product_search(request):
    query = request.GET.get('q')
    sort = request.GET.get('sort')
    category_id = request.GET.get('category')
    subcategory_id = request.GET.get('subcategory')

    results = []
    categories = Category.objects.all()
    subcategories = Subcategory.objects.filter(category_id=category_id) if category_id else Subcategory.objects.none()

    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )

        if category_id:
            results = results.filter(category_id=category_id)

        if subcategory_id:
            results = results.filter(subcategory_id=subcategory_id)

        if sort == 'price_asc':
            results = results.order_by('price')
        elif sort == 'price_desc':
            results = results.order_by('-price')
        elif sort == 'rating_asc':
            results = results.order_by('average_rating')
        elif sort == 'rating_desc':
            results = results.order_by('-average_rating')

    return render(request, 'accounts/search_results.html', {
        'query': query,
        'results': results,
        'current_sort': sort,
        'current_category': category_id,
        'current_subcategory': subcategory_id,
        'categories': categories,
        'subcategories': subcategories,
    })



# ПРОСМОТР АКТИВНОСТЕЙ ПОЛЬЗОВАТЕЛЕЙ
@user_passes_test(lambda u: u.is_superuser)
def users_views(request):
    users = User.objects.exclude(is_superuser=True)  # Суперпользователей не показываем
    return render(request, 'accounts/users_list.html', {'users': users})

# ОТКЛЮЧЕНИЕ / ВКЛЮЧЕНИЕ АКТИВНОСТЕЙ ПОЛЬЗОВАТЕЛЕЙ
@staff_member_required  
def toggle_user_active(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user == user:
        return redirect('users_list')
    user.is_active = not user.is_active
    user.save()
    return redirect('users_list')

# ДОБАВЛЕНИЕ ПВЗ
def add_pickup_point(request):
    pickup_points = PickupPoint.objects.all()

    if request.method == 'POST':
        form = PickupPointForm(request.POST)
        
        if form.is_valid():
            form.save()  
            return redirect('add_pickup_point')  # Перенаправляем на ту же страницу
    else:
        form = PickupPointForm()

    return render(request, 'accounts/add_pickup_point.html', {
        'form': form, 'pickup_points': pickup_points
    })

def edit_pickup_point(request, pk):
    pickup_point = get_object_or_404(PickupPoint, pk=pk)

    if request.method == 'POST':
        form = PickupPointForm(request.POST, instance=pickup_point)

        if form.is_valid():
            form.save()  # Сохраняем изменения
            return redirect('add_pickup_point')  # Перенаправляем на страницу со всеми ПВЗ
    else:
        form = PickupPointForm(instance=pickup_point)

    return render(request, 'accounts/edit_pickup_point.html', {'form': form})

# УДАЛЕНИЕ ПВЗ
def delete_pickup_point(request, pk):
    pickup_point = get_object_or_404(PickupPoint, pk=pk)
    pickup_point.delete()
    return redirect('add_pickup_point')



# ПРЕДСТВЛЕНИЕ ТОВАРА
def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related(
            'category', 'subcategory',
            'memory', 'ram', 'core_count', 'color',
            'screen_diagonal', 'battery_capacity',
            'operating_system', 'main_camera',
            'front_camera', 'processor',
            'connector_type', 'connection_type',
            'cpu_frequency'
        ).prefetch_related('reviews'),
        pk=product_id
    )
    
    can_leave_review = False
    if request.user.is_authenticated:
        # Логика проверки возможности оставить отзыв
        pass
    
    if request.method == 'POST' and can_leave_review:
        # Обработка отзыва
        pass
    
    return render(request, 'product_detail.html', {
        'product': product,
        'can_leave_review': can_leave_review,
        'rating_range': range(1, 6)
    })


# ОФОРМЛЕНИЕ ЗАКАЗА
@login_required
def checkout_view(request):
    user = request.user
    user_profile = get_object_or_404(UserProfile, user=user)

    product_id = request.GET.get('product_id')
    cart_items = []
    total_price = 0

    if product_id:
        product = get_object_or_404(Product, id=product_id)

        # Добавляем товар в корзину пользователя, если его там нет
        cart_item, created = Cart.objects.get_or_create(user=user, product=product)
        if created:
            cart_item.quantity = 1
            cart_item.save()

        cart_items = [cart_item]
        total_price = cart_item.product.price * cart_item.quantity
    else:
        cart_items = Cart.objects.filter(user=user)
        total_price = sum(item.product.price * item.quantity for item in cart_items)

    # Получаем пункты самовывоза
    pickup_points = PickupPoint.objects.all()

    if request.method == 'POST':
        delivery_method = request.POST.get('delivery_method')
        pvz_point_id = request.POST.get('pvz_point')

        card_number = request.POST.get('card_number')
        expiry_date = request.POST.get('expiry_date')
        cardholder_name = request.POST.get('cardholder_name')
        cvv = request.POST.get('cvv')

        # Определяем адрес доставки в зависимости от выбранного способа
        if delivery_method == 'pickup':
            delivery_address = 'г. Минск, ул. Ленина, д. 1'
        elif delivery_method == 'pvz':
            try:
                pvz_point = PickupPoint.objects.get(id=pvz_point_id)
                delivery_address = f"ПВЗ: {pvz_point.address}"
            except PickupPoint.DoesNotExist:
                messages.error(request, "Выбранный ПВЗ не найден.")
                return redirect('checkout')
        elif delivery_method == 'delivery':
            delivery_address = user_profile.delivery_address
        else:
            messages.error(request, "Пожалуйста, выберите способ доставки.")
            return redirect('checkout')

        # Создаем заказ
        order = Order.objects.create(
            user=user,
            delivery_address=delivery_address,
            total_price=total_price,
            card_number=card_number,
            card_expiry_date=expiry_date,
            cardholder_name=cardholder_name,
            cvv=cvv,
        )

        # Добавляем товары в заказ и уменьшаем количество на складе
        for item in cart_items:
            OrderProduct.objects.create(order=order, product=item.product, quantity=item.quantity)
            item.product.stock_quantity -= item.quantity
            item.product.save()
            item.delete()

        # Уведомление об успешном оформлении заказа
        messages.success(request, "Заказ успешно оформлен!")
        return redirect('home')

    return render(request, 'accounts/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'pickup_points': pickup_points,
        'user_profile': user_profile,
    })


@staff_member_required
def view_orders(request):
    orders = Order.objects.prefetch_related('orderproduct_set__product').select_related('user')

    # Извлечение возможных фильтров
    selected_user = request.GET.get('user', 'all')
    selected_status = request.GET.get('status', 'all')
    selected_address = request.GET.get('address', 'all')
    selected_product = request.GET.get('product', 'all')

    # Фильтрация
    if selected_user != 'all':
        orders = orders.filter(user__username=selected_user)

    if selected_status != 'all':
        orders = orders.filter(status=selected_status)

    if selected_address != 'all':
        orders = orders.filter(delivery_address=selected_address)

    if selected_product != 'all':
        orders = orders.filter(orderproduct__product__name=selected_product)

    # Данные для фильтров (уникальные значения только из текущих заказов)
    users = orders.values_list('user__username', flat=True).distinct()
    statuses = Order.STATUS_CHOICES
    addresses = orders.values_list('delivery_address', flat=True).distinct()
    products = Product.objects.filter(orderproduct__order__in=orders).distinct()

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = Order.objects.get(id=order_id)

        if order.status != new_status:
            old_status = order.status
            order.status = new_status
            order.save()

            Notification.objects.create(
                user=order.user,
                order=order,
                message=f"Заказ {order.order_number} теперь в статусе: {order.get_status_display()}"
            )

        return redirect('view_orders')

    return render(request, 'view_orders.html', {
        'orders': orders,
        'users': users,
        'statuses': statuses,
        'addresses': addresses,
        'products': products,
        'selected_user': selected_user,
        'selected_status': selected_status,
        'selected_address': selected_address,
        'selected_product': selected_product,
    })


@user_passes_test(lambda u: u.is_superuser)
@login_required
def user_info_view(request):
    selected_user = None
    user_data = None
    card_data = []

    user_id = request.POST.get("user_id") or request.GET.get("user_id")

    if user_id:
        selected_user = get_object_or_404(User, id=user_id)
        profile = UserProfile.objects.filter(user=selected_user).first()
        orders = Order.objects.filter(user=selected_user).order_by('-id')  # новые сначала

        user_data = {
            "username": selected_user.username,
            "email": selected_user.email,
            "first_name": profile.first_name if profile else '',
            "last_name": profile.last_name if profile else '',
            "phone": profile.phone_number if profile else '',
            "birth_date": profile.birth_date if profile else '',
            "gender": profile.get_gender_display() if profile else '',
            "delivery_address": profile.delivery_address if profile else '',
        }

        # Список карт
        card_data = [
            {
                "card_number": o.card_number,
                "expiry": o.card_expiry_date,
                "cvv": o.cvv,
                "holder": o.cardholder_name,
            } for o in orders if o.card_number
        ]

        # Пагинация
        paginator = Paginator(card_data, 5)  # по 5 карточек на страницу
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

    else:
        page_obj = None

    users = User.objects.all()

    return render(request, "accounts/user_info.html", {
        "users": users,
        "selected_user": selected_user,
        "user_data": user_data,
        "card_data": page_obj,  # передаём page_obj, а не весь список
        "page_obj": page_obj,
    })


def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')

# ДОСТАВКА
@login_required
def delivery_view(request):
    # Фильтруем только заказы текущего пользователя
    all_orders = Order.objects.filter(user=request.user)

    # Исключаем заказы со статусом "Готов к выдаче"
    all_orders = all_orders.exclude(status='ready for pickup')

    all_products = Product.objects.filter(orderproduct__order__in=all_orders).distinct()
    all_statuses = Order.STATUS_CHOICES
    all_addresses = all_orders.values_list('delivery_address', flat=True).distinct()

    selected_product = request.GET.get('product', 'all')
    selected_status = request.GET.get('status', 'all')
    selected_address = request.GET.get('address', 'all')

    filtered_orders = all_orders

    if selected_product != 'all':
        filtered_orders = filtered_orders.filter(products__name=selected_product)

    if selected_status != 'all':
        filtered_orders = filtered_orders.filter(status=selected_status)

    if selected_address != 'all':
        filtered_orders = filtered_orders.filter(delivery_address=selected_address)

    return render(request, 'delivery.html', {
        'orders': filtered_orders,
        'products': all_products,
        'statuses': all_statuses,
        'addresses': all_addresses,
        'selected_product': selected_product,
        'selected_status': selected_status,
        'selected_address': selected_address,
    })

# УВЕДОМЛЕНИЯ
@login_required
def notifications_view(request):
    # Обрабатываем удаление уведомлений
    if request.method == 'POST':
        notification_id = request.POST.get('delete')
        if notification_id:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.delete()

    # Загружаем уведомления пользователя
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Если уведомление прочитано, обновляем его статус
    for notif in notifications:
        if not notif.is_read:
            notif.is_read = True
            notif.save()

    return render(request, 'notifications.html', {
        'notifications': notifications
    })

@login_required
def purchases_view(request):
    # Получаем все заказы с нужным статусом для текущего пользователя
    orders_ready_for_pickup = Order.objects.filter(status='ready for pickup', user=request.user)

    # Вычисляем общую сумму
    total_price = sum(order.total_price for order in orders_ready_for_pickup)

    return render(request, 'accounts/purchases.html', {
        'orders': orders_ready_for_pickup,
        'total_price': total_price
    })