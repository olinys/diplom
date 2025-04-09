from django.contrib import admin
from .models import Product, Category, Order, User, UserProfile, Cart, PickupPoint, OrderProduct

admin.site.register(Product)
admin.site.register(Category)

