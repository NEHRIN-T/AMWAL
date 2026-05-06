from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import re

class Property(models.Model):
    """
    Core model representing a property unit in the portfolio.
    """
    class PropertyType(models.TextChoices):
        LX_VILLA = 'LX_VILLA', _('LX Villa')
        ST_VILLA = 'ST_VILLA', _('Standard Villa')
        APARTMENT = 'APARTMENT', _('2-3BR Apartment')
        FLAT = 'FLAT', _('Studio/1BR Flat')

    class Category(models.TextChoices):
        LUXURY_VILLAS = 'Luxury Villas', _('Luxury Villas')
        STANDARD_VILLAS = 'Standard Villas', _('Standard Villas')
        LARGER_APARTMENTS = 'Larger Apartments', _('Larger Apartments')
        STANDARD_FLATS = 'Standard Flats', _('Standard Flats')

    unit_ref = models.CharField(max_length=50, unique=True, editable=False)
    property_type = models.CharField(max_length=50, choices=PropertyType.choices)
    category = models.CharField(max_length=50, choices=Category.choices, editable=False)
    area = models.CharField(max_length=255, default='TBD')
    bedrooms = models.IntegerField(default=0)
    floor_area = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['unit_ref']

    def save(self, *args, **kwargs):
        # 1. Mandatory Category Mapping
        mapping = {
            self.PropertyType.LX_VILLA: self.Category.LUXURY_VILLAS,
            self.PropertyType.ST_VILLA: self.Category.STANDARD_VILLAS,
            self.PropertyType.APARTMENT: self.Category.LARGER_APARTMENTS,
            self.PropertyType.FLAT: self.Category.STANDARD_FLATS,
        }
        self.category = mapping.get(self.property_type)

        # 2. Unit Reference Generation (Only on creation)
        if not self.unit_ref:
            prefix_map = {
                self.PropertyType.LX_VILLA: 'LV',
                self.PropertyType.ST_VILLA: 'SV',
                self.PropertyType.APARTMENT: 'LA',
                self.PropertyType.FLAT: 'SF',
            }
            prefix = prefix_map.get(self.property_type)
            
            # Find the last unit_ref with this prefix
            last_unit = Property.objects.filter(unit_ref__startswith=prefix).order_by('-unit_ref').first()
            if last_unit:
                match = re.search(r'-(\d+)$', last_unit.unit_ref)
                if match:
                    next_num = int(match.group(1)) + 1
                else:
                    next_num = 1
            else:
                next_num = 1
            
            self.unit_ref = f"{prefix}-{next_num:02d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unit_ref} ({self.category})"


class Tenant(models.Model):
    """
    Model representing a tenant.
    """
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=50, default='N/A')
    email = models.EmailField(unique=True)
    id_passport = models.CharField(max_length=100, default='N/A')
    nationality = models.CharField(max_length=100, default='N/A')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Lease(models.Model):
    """
    Model representing a lease agreement.
    Status: Active -> Occupied, Expired/Terminated -> Vacant.
    """
    class LeaseStatus(models.TextChoices):
        ACTIVE = 'Active', _('Active')
        EXPIRED = 'Expired', _('Expired')
        TERMINATED = 'Terminated', _('Terminated')
        NOTICE = 'Notice', _('Notice')

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='leases')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='leases')
    start_date = models.DateField()
    end_date = models.DateField()
    vacate_date = models.DateField(null=True, blank=True)
    annual_rent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_rent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_frequency = models.CharField(max_length=50, default='Monthly')
    deposit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=15, choices=LeaseStatus.choices, default=LeaseStatus.ACTIVE)
    contract_file = models.FileField(upload_to='contracts/', null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Lease: {self.tenant.name} - {self.property.unit_ref}"


class RentData(models.Model):
    """
    Financial and market rental data for a property.
    """
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='rent_data')
    current_annual_rent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_monthly_rent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    market_annual_rent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    market_monthly_rent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    DLD_evidence = models.CharField(max_length=255, blank=True, null=True)
    last_review_date = models.DateField(default=timezone.now)
    review_notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Rent Data"

    def __str__(self):
        return f"Rent Data for {self.property.unit_ref}"


class Occupancy(models.Model):
    """
    Tracking occupancy status and vacancy details.
    """
    class OccupancyStatus(models.TextChoices):
        OCCUPIED = 'Occupied', _('Occupied')
        VACANT = 'Vacant', _('Vacant')
        UNDER_RENOVATION = 'Under Renovation', _('Under Renovation')
        RESERVED = 'Reserved', _('Reserved')

    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='occupancy')
    status = models.CharField(max_length=30, choices=OccupancyStatus.choices, default=OccupancyStatus.VACANT)
    vacancy_start_date = models.DateField(null=True, blank=True)
    target_occupancy_date = models.DateField(null=True, blank=True)
    vacancy_reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Occupancy Records"

    def __str__(self):
        return f"Occupancy: {self.property.unit_ref} ({self.status})"


class Valuation(models.Model):
    """
    Asset valuation records.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='valuations')
    value = models.DecimalField(max_digits=15, decimal_places=2)
    valuation_date = models.DateField()
    source = models.CharField(max_length=255)

    def __str__(self):
        return f"Valuation: {self.property.unit_ref} - {self.value}"


class PropertyImage(models.Model):
    """
    Gallery images for properties.
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=500)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.property.unit_ref} (Order: {self.order})"


class OwnerProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'Admin', _('Admin')
        ANALYST = 'Analyst', _('Analyst')
        MANAGER = 'Manager', _('Manager')
        VIEWER = 'Viewer', _('Viewer')

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_profile')
    full_name = models.CharField(max_length=255, default='H. Siddiqui')
    portfolio_units = models.IntegerField(default=60)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADMIN)
    location = models.CharField(max_length=100, default='Dubai, UAE')
    currency = models.CharField(max_length=10, default='AED')

    def __str__(self):
        return self.full_name

@receiver(post_save, sender=Property)
def create_occupancy_for_property(sender, instance, created, **kwargs):
    if created:
        Occupancy.objects.get_or_create(property=instance)

@receiver(post_save, sender=User)
def create_owner_profile(sender, instance, created, **kwargs):
    if created:
        OwnerProfile.objects.create(user=instance)

@receiver(post_save, sender=Lease)
def update_occupancy_on_lease_save(sender, instance, **kwargs):
    """
    Automatically update Property Occupancy status based on Lease state.
    """
    occupancy, created = Occupancy.objects.get_or_create(property=instance.property)
    if instance.status == Lease.LeaseStatus.ACTIVE:
        occupancy.status = Occupancy.OccupancyStatus.OCCUPIED
        occupancy.vacancy_start_date = None
    elif instance.status in [Lease.LeaseStatus.EXPIRED, Lease.LeaseStatus.TERMINATED]:
        occupancy.status = Occupancy.OccupancyStatus.VACANT
        if not occupancy.vacancy_start_date:
            occupancy.vacancy_start_date = timezone.now().date()
    occupancy.save()
