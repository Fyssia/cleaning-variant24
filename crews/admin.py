from django.contrib import admin

from .models import Crew, Employee, ScheduleSlot


class EmployeeInline(admin.TabularInline):
    model = Employee
    extra = 0
    fields = ['full_name', 'phone', 'hired_on', 'is_active']


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ['name', 'leader', 'is_active']
    inlines = [EmployeeInline]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'crew', 'phone', 'hired_on', 'is_active']
    list_filter = ['crew', 'is_active']
    search_fields = ['full_name']


@admin.register(ScheduleSlot)
class ScheduleSlotAdmin(admin.ModelAdmin):
    list_display = ['crew', 'kind', 'start', 'end', 'order']
    list_filter = ['crew', 'kind']
    date_hierarchy = 'start'
