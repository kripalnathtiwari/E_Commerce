from django.contrib import admin
from .models import Product, ProductImage

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','product_name','price','stock','category','modified_date','is_available')
    prepopulated_fields = {'slug': ('product_name',)}

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation', 'is_main')
    list_filter = ('product', 'variation')