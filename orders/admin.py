
from django.contrib import admin
from .models import Address, UploadedDesign, PrintOrder
admin.site.register(Address)
admin.site.register(UploadedDesign)
from .models import Distributor
from .models import  Order, OrderItem, Return

@admin.register(Distributor)
class DistributorAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "city")


@admin.register(PrintOrder)
class PrintOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "delivery_status", "distributor")
    list_filter = ("delivery_status",)



class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','distributor','price','stock','created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','user','distributor','payment_status','delivery_status','created_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order','product','quantity','price')


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'user', 'return_status', 'created_at', 'updated_at')
    list_filter = ('return_status', 'created_at')
    search_fields = ('order__id', 'user__username', 'issue_description')
    readonly_fields = ('created_at', 'updated_at')