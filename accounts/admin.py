from django.contrib import admin
from .models import Product, Category, Order, UserProfile, Cart, PickupPoint, Notification, Review, Subcategory, CpuFrequency, Camera, Color, ConnectionType, ConnectorType, CoreCount, BatteryCapacity, Memory, RAM, Processor, OperatingSystem, ScreenDiagonal
import logging

# Регистрируем модели в админке
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(UserProfile)
admin.site.register(Cart)
admin.site.register(PickupPoint)
admin.site.register(Notification)
admin.site.register(Review)
admin.site.register(Subcategory)
admin.site.register(CoreCount)
admin.site.register(CpuFrequency)
admin.site.register(Camera)
admin.site.register(Color)
admin.site.register(ConnectionType)
admin.site.register(ConnectorType)
admin.site.register(BatteryCapacity)
admin.site.register(Memory)
admin.site.register(RAM)
admin.site.register(Processor)
admin.site.register(OperatingSystem)
admin.site.register(ScreenDiagonal)









# Логгер для отслеживания создания уведомлений
logger = logging.getLogger(__name__)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'status', 'user')
    list_editable = ('status',)

    def save_model(self, request, obj, form, change):
        if change:
            # Получаем старый объект заказа для сравнения статусов
            old_obj = Order.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                # Создаем уведомление, если статус изменился
                notification = Notification.objects.create(
                    user=obj.user,
                    order=obj,
                    message=f"Заказ {obj.order_number} теперь в статусе: {obj.get_status_display()}"
                )
                # Логируем информацию о созданном уведомлении
                logger.info(f"Создано уведомление для пользователя {obj.user.username} о статусе заказа {obj.order_number}: {obj.get_status_display()}")

        # Продолжаем сохранение модели
        super().save_model(request, obj, form, change)

# Регистрируем модель Order с кастомным админом
admin.site.register(Order, OrderAdmin)
