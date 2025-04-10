from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import add_product, add_category, checkout_view, view_cart, edit_product, delete_product, add_pickup_point


urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('accounts/add_product/', add_product, name='add_product'),
    path("add_category/", add_category, name="add_category"),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('product/edit/<int:product_id>/', edit_product, name='edit_product'),
    path('product/delete/<int:product_id>/', delete_product, name='delete_product'),
    path('cart/', view_cart, name='cart'),
    path('checkout/', checkout_view, name='checkout'),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart_item, name='update_cart_item'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('catalog/<int:category_id>/', views.catalog_view, name='catalog_by_category'), 
    path('search/', views.product_search, name='search'),
    path('delivery/', views.delivery_view, name='delivery'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('users/', views.users_views, name='users_list'),
    path('toggle_user_active/<int:user_id>/', views.toggle_user_active, name='toggle_user_active'),
    path('add/', views.add_pickup_point, name='add_pickup_point'),
    path('delete/<int:pk>/', views.delete_pickup_point, name='delete_pickup_point'),
    path('edit/<int:pk>/', views.edit_pickup_point, name='edit_pickup_point'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('view_orders/', views.view_orders, name='view_orders'),
    path('user_info/', views.user_info_view, name='user_info'),
    ]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)