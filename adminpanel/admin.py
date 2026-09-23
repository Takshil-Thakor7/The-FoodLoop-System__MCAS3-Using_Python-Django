from django.contrib import admin
from .models import (
    Admin, User, FoodBusiness, NGO, Customer, Volunteer,
    FoodItem, FoodEligibility, FoodRequest, Match, Pickup,
    Delivery, Notification, Analytics,
)


@admin.register(Admin)
class AdminAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'contact', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'contact')


@admin.register(User)
class FoodLoopUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'contact', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'contact')


for model in [FoodBusiness, NGO, Customer, Volunteer, FoodItem, FoodEligibility, FoodRequest, Match, Pickup, Delivery, Notification, Analytics]:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
