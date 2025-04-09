from django.contrib import admin
from django.urls import path, include
from accounts.views import home  # Импортируем home из accounts
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  # Главная страница
    path('accounts/', include('accounts.urls')),  # Используем include для путей аккаунтов
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
