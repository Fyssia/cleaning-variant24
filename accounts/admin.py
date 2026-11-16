from django.contrib import admin

from .models import Address, Customer


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'phone', 'user', 'created_at']
    search_fields = ['user__last_name', 'user__first_name', 'phone', 'user__email']
    inlines = [AddressInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'customer', 'floor', 'comment']
    list_filter = ['city']
    search_fields = ['street', 'customer__user__last_name']
