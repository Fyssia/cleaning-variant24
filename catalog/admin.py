from django.contrib import admin

from .models import Material, RoomType, Service, ServiceMaterial


class ServiceMaterialInline(admin.TabularInline):
    model = ServiceMaterial
    extra = 0


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'kind', 'unit', 'price', 'minutes_per_unit', 'series_discount', 'is_active']
    list_filter = ['kind', 'room_types', 'is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}
    inlines = [ServiceMaterialInline]


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price_factor', 'duration_factor', 'sort']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'stock', 'min_stock']
    search_fields = ['name']


@admin.register(ServiceMaterial)
class ServiceMaterialAdmin(admin.ModelAdmin):
    list_display = ['service', 'material', 'norm']
    list_filter = ['material']
