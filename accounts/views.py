from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm, UserProfileForm, ProductForm, CategoryForm, PickupPointForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Cart, UserProfile, Product, Category, User, PickupPoint
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required

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

# ОФОРМЛЕНИЕ ЗАКАЗА
def checkout_view(request):

    return render(request, 'accounts/checkout.html')

# ДОСТАВКА
def delivery_view(request):
    return render(request, 'delivery.html')

# УВЕДОМЛЕНИЯ
def notifications_view(request):
    return render(request, 'notifications.html')



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