from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm, UserProfileForm, ProductForm, CategoryForm, PickupPointForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Cart, UserProfile, Product, Category, User, PickupPoint, Order, OrderProduct
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator

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
            product_form.save()
            return redirect("home")  # Перенаправление на главную страницу
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
            return redirect("add_product") 
    else:
        category_form = CategoryForm()

    return render(request, "accounts/add_category.html", {"category_form": category_form})

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
def catalog_view(request, category_id=None):
    categories = Category.objects.all()

    if category_id:
        products = Product.objects.filter(category_id=category_id)
    else:
        products = Product.objects.all()
        
    return render(request, 'accounts/catalog.html', {
        'categories': categories,
        'products': products
    })

# ПОИСКОВАЯ СТРОКА
def product_search(request):
    query = request.GET.get('q')
    results = []
    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )
    return render(request, 'accounts/search_results.html', {
        'query': query,
        'results': results
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
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product_detail.html', {'product': product})

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

    if request.method == 'POST':
        delivery_method = request.POST.get('delivery_method')
        pvz_point_id = request.POST.get('pvz_point')

        card_number = request.POST.get('card_number')
        expiry_date = request.POST.get('expiry_date')
        cardholder_name = request.POST.get('cardholder_name')
        cvv = request.POST.get('cvv')

        # Создаем заказ
        order = Order.objects.create(
            user=user,
            delivery_address=user_profile.delivery_address,
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

            # Удаляем товар из корзины
            item.delete()

        # Уведомление об успешном оформлении заказа
        messages.success(request, "Заказ успешно оформлен!")
        return redirect('home')

    # Получаем пункты самовывоза
    pickup_points = PickupPoint.objects.all()

    return render(request, 'accounts/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'pickup_points': pickup_points,
        'user_profile': user_profile,
    })


@staff_member_required
def view_orders(request):
    orders = Order.objects.prefetch_related('products').select_related('user')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save()
        return redirect('view_orders')

    return render(request, 'view_orders.html', {'orders': orders})


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
def delivery_view(request):
    all_orders = Order.objects.all()

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

    # Пагинация
    paginator = Paginator(filtered_orders.order_by('-id'), 5)  # 5 заказов на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'delivery.html', {
        'orders': page_obj,
        'page_obj': page_obj,
        'products': all_products,
        'statuses': all_statuses,
        'addresses': all_addresses,
        'selected_product': selected_product,
        'selected_status': selected_status,
        'selected_address': selected_address,
    })

# УВЕДОМЛЕНИЯ
def notifications_view(request):
    return render(request, 'notifications.html')