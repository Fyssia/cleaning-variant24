from django.contrib import admin

from .models import Order, OrderItem, RecurrenceRule


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'start', 'customer', 'room_type', 'area', 'price', 'status', 'crew', 'rule']
    list_filter = ['status', 'room_type', 'crew']
    search_fields = ['customer__user__last_name', 'address__street']
    date_hierarchy = 'start'
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'service', 'quantity', 'unit_price']
    list_filter = ['service__kind', 'service']


@admin.register(RecurrenceRule)
class RecurrenceRuleAdmin(admin.ModelAdmin):
    list_display = ['customer', 'period', 'start_date', 'end_date']
    list_filter = ['period']
