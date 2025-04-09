from django.contrib import admin
from .models import Product, Category, Order, UserProfile, Cart, PickupPoint, OrderProduct

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Order)
admin.site.register(UserProfile)
admin.site.register(Cart)
admin.site.register(PickupPoint)


