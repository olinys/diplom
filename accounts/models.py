from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Связь с моделью User
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], blank=True)
    delivery_address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
    

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название категории")

    def __str__(self):
        return self.name
    

class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories", verbose_name="Категория")
    name = models.CharField(max_length=255, verbose_name="Название подкатегории")

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    parameter_1 = models.CharField(max_length=255, blank=True, verbose_name="Параметр 1")
    parameter_2 = models.CharField(max_length=255, blank=True, verbose_name="Параметр 2")
    parameter_3 = models.CharField(max_length=255, blank=True, verbose_name="Параметр 3")
    parameter_4 = models.CharField(max_length=255, blank=True, verbose_name="Параметр 4")
    parameter_5 = models.CharField(max_length=255, blank=True, verbose_name="Параметр 5")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    subcategory = models.ForeignKey(Subcategory, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Подкатегория")  # <-- Добавили
    sku = models.CharField(max_length=50, unique=True, verbose_name="Артикул", blank=True)
    image = models.ImageField(upload_to="product_images/", blank=True, null=True, verbose_name="Изображение")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Количество в наличии")
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.sku:
            last_product = Product.objects.order_by('-id').first()
            base_sku = 10000000
            if last_product and last_product.sku.isdigit():
                self.sku = str(int(last_product.sku) + 1)
            else:
                self.sku = str(base_sku)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=1)  # Рейтинг от 1 до 5
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review for {self.product.name} by {self.user.username}'

    
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Проверьте, что здесь правильно указана модель и внешний ключ
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    

class PickupPoint(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    # Время открытия и закрытия для каждого дня
    monday_open = models.TimeField(default="09:00:00")
    monday_close = models.TimeField(default="12:00:00")

    tuesday_open = models.TimeField(default="09:00:00")
    tuesday_close = models.TimeField(default="21:00:00")

    wednesday_open = models.TimeField(default="09:00:00")
    wednesday_close = models.TimeField(default="21:00:00")

    thursday_open = models.TimeField(default="09:00:00")
    thursday_close = models.TimeField(default="21:00:00")

    friday_open = models.TimeField(default="09:00:00")
    friday_close = models.TimeField(default="21:00:00")

    saturday_open = models.TimeField(default="09:00:00")
    saturday_close = models.TimeField(default="21:00:00")

    sunday_open = models.TimeField(default="09:00:00")
    sunday_close = models.TimeField(default="21:00:00")

    def __str__(self):
        return self.name
    

class Order(models.Model):
    STATUS_CHOICES = [
        ('placed', 'Оформлен'),
        ('on assembly', 'На сборке'),
        ('on the way', 'В пути'),
        ('ready for pickup', 'Готов к выдаче'),
        ('handed over to the courier', 'Передан курьеру'),
    ]

    order_number = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Новый номер заказа

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_address = models.TextField()
    products = models.ManyToManyField(Product, through='OrderProduct')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(default=timezone.now)
    card_number = models.CharField(max_length=19)
    card_expiry_date = models.CharField(max_length=5)
    cardholder_name = models.CharField(max_length=100)
    cvv = models.CharField(max_length=3, verbose_name="CVV")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='placed')

    def __str__(self):
        return f"Заказ {self.order_number or self.id} от {self.user.username}"

    def save(self, *args, **kwargs):
        # Шифрование
        self.card_number = self.encrypt_card(self.card_number)
        self.cvv = self.encrypt_cvv(self.cvv)

        # Генерация номера заказа при первом сохранении
        if not self.order_number:
            last_order = Order.objects.order_by('-id').first()
            next_number = last_order.id + 1 if last_order else 1
            self.order_number = f"№{next_number:06d}"

        super().save(*args, **kwargs)

    def encrypt_card(self, card_data):
        return "**** **** **** " + card_data[-4:]

    def encrypt_cvv(self, cvv_data):
        return "****"

    

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()  # Количество товара

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.message}"
