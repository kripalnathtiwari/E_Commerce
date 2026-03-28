from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('product/<int:product_id>/', views.product_detail, name="product_detail"),
    path('get_image_for_color/<int:product_id>/<str:color>/', views.get_image_for_color, name="get_image_for_color"),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path("cart/", views.cart, name="cart"),
    path('cart/increase/<int:item_id>/', views.increase_cart, name='increase_cart'),
    path('cart/decrease/<int:item_id>/', views.decrease_cart, name='decrease_cart'),
    path('cart/remove/<int:item_id>/', views.remove_cart, name='remove_cart'),
    path('contact/', views.contact, name='contact'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path("payment/", views.payment, name="payment"),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('search/', views.search, name='search'),
    path('distributor/dashboard/', views.distributor_dashboard, name='distributor_dashboard'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('write_review/<int:product_id>/', views.write_review, name='write_review'),
    path('support/', views.support, name='support'),
]