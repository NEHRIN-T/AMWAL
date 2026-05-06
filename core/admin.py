from django.contrib import admin
from .models import Property, Tenant, Lease, RentData, Occupancy, Valuation, PropertyImage, OwnerProfile

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('unit_ref', 'property_type', 'category', 'bedrooms', 'updated_at')
    list_filter = ('property_type', 'category', 'bedrooms')
    search_fields = ('unit_ref', 'area')
    readonly_fields = ('unit_ref', 'category')
    inlines = [PropertyImageInline]

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'email', 'nationality', 'created_at')
    search_fields = ('name', 'email', 'contact')

@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ('property', 'tenant', 'start_date', 'end_date', 'status', 'annual_rent')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('property__unit_ref', 'tenant__name')
    autocomplete_fields = ('property', 'tenant')

@admin.register(RentData)
class RentDataAdmin(admin.ModelAdmin):
    list_display = ('property', 'current_annual_rent', 'market_annual_rent', 'last_review_date')
    search_fields = ('property__unit_ref',)

@admin.register(Occupancy)
class OccupancyAdmin(admin.ModelAdmin):
    list_display = ('property', 'status', 'vacancy_start_date')
    list_filter = ('status',)
    search_fields = ('property__unit_ref',)

@admin.register(Valuation)
class ValuationAdmin(admin.ModelAdmin):
    list_display = ('property', 'value', 'valuation_date', 'source')
    list_filter = ('valuation_date', 'source')
    search_fields = ('property__unit_ref',)

@admin.register(OwnerProfile)
class OwnerProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'portfolio_units', 'location')
