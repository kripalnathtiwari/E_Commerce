from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account

class AccountAdmin(UserAdmin):

    list_display = ('email','first_name','last_name','username','role','last_login','is_active','date_joined')
    list_display_links = ('email','first_name','last_name')
    readonly_fields = ('last_login','date_joined')
    ordering = ('-date_joined',)

    filter_horizontal = ()
    list_filter = ('role',)   # optional but useful
    fieldsets = ()

    # 🔥 THIS IS THE FIX
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(role='customer')   # hide distributors

admin.site.register(Account, AccountAdmin)