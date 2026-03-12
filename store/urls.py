from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('product/<int:product_id>/', views.product_detail, name="product_detail"),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path("cart/", views.cart, name="cart"),
    path('cart/increase/<int:item_id>/', views.increase_cart, name='increase_cart'),
    path('cart/decrease/<int:item_id>/', views.decrease_cart, name='decrease_cart'),
    path('cart/remove/<int:item_id>/', views.remove_cart, name='remove_cart'),
    path('contact/', views.contact, name='contact'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path("payment/", views.payment, name="payment"),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('search/', views.search, name='search'),
]