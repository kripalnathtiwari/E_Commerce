
from django.urls import path
from . import views

urlpatterns = [
    path("checkout/<int:product_id>/", views.checkout, name="checkout"),
    path("distributor/", views.distributor_dashboard, name="distributor_dashboard"),
    path('place-order/<int:product_id>/', views.place_order, name="place_order"),
    path('distributor/orders/', views.distributor_orders, name="distributor_orders"),
    path('my-orders/', views.user_orders, name="user_orders"),
    path('dashboard/', views.distributor_dashboard, name='distributor_dashboard'),
    path('add-product/', views.add_product, name='add_product'),
    path('orders/', views.distributor_orders, name='distributor_orders'),
    path('update-status/<int:order_id>/', views.update_delivery_status, name='update_status'),
    path('update-payment-status/<int:order_id>/', views.update_payment_status, name='update_payment_status'),
    path('shop/', views.shop, name="shop"),
    path('buy/<int:product_id>/', views.buy_product, name="buy_product"),
    path('my-orders/', views.user_orders, name="user_orders"),
    path('my-products/', views.distributor_products, name='distributor_products'),
    path('store/', views.shop, name="shop"),
    path('update-stock/<int:product_id>/', views.update_stock, name='update_stock'),
]
