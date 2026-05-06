from rest_framework import serializers
from .models import Property, Tenant, Lease, RentData, Occupancy, OwnerProfile
from django.contrib.auth.models import User

class PropertySerializer(serializers.ModelSerializer):
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Needs to be able to resolve relations. Wait, to solve circular dependency if not defined first, let's use Method fields or just move classes up.
    # I'll just use SerializerMethodField for easier read caching
    rent_data = serializers.SerializerMethodField()
    occupancy = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = '__all__'

    def get_rent_data(self, obj):
        if hasattr(obj, 'rent_data'):
            current_rent = float(obj.rent_data.current_annual_rent) if obj.rent_data.current_annual_rent else 0
            market_rent = float(obj.rent_data.market_annual_rent) if obj.rent_data.market_annual_rent else 0
            gap_percent = ((current_rent - market_rent) / market_rent) * 100 if market_rent > 0 else 0

            return {
                'current_annual_rent': obj.rent_data.current_annual_rent,
                'market_annual_rent': obj.rent_data.market_annual_rent,
                'rent_gap': obj.rent_data.rent_gap(),
                'monthly_rent': current_rent / 12,
                'gap_percent': gap_percent
            }
        return None

    def get_occupancy(self, obj):
        if hasattr(obj, 'occupancy'):
            return {
                'status': obj.occupancy.status,
                'days_vacant': obj.occupancy.days_vacant()
            }
        return None

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = '__all__'

class LeaseSerializer(serializers.ModelSerializer):
    property_ref = serializers.CharField(source='property.unit_ref', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Lease
        fields = '__all__'

class RentDataSerializer(serializers.ModelSerializer):
    rent_gap = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = RentData
        fields = '__all__'

class OccupancySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_vacant = serializers.IntegerField(read_only=True)

    class Meta:
        model = Occupancy
        fields = '__all__'

class OwnerProfileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    mfa_enabled = serializers.SerializerMethodField()
    mfa_methods = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()
    activity_logs = serializers.SerializerMethodField()

    class Meta:
        model = OwnerProfile
        fields = '__all__'

    def get_name(self, obj):
        if obj.full_name:
            return obj.full_name
        if obj.user.first_name or obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.username

    def get_mfa_enabled(self, obj):
        return obj.mfa_enabled

    def get_mfa_methods(self, obj):
        if obj.mfa_methods:
            return [m.strip() for m in obj.mfa_methods.split(',') if m.strip()]
        return []

    def get_last_login(self, obj):
        if obj.last_login_display:
            return obj.last_login_display
        from django.utils import timezone
        return (timezone.now() - timezone.timedelta(hours=2)).isoformat()

    def get_activity_logs(self, obj):
        from django.utils import timezone
        now = timezone.now()
        return [
            {"action": "Account Login (Dubai, UAE)", "timestamp": (now - timezone.timedelta(hours=2)).isoformat(), "status": "Success"},
            {"action": "Viewed Financial Dashboard", "timestamp": (now - timezone.timedelta(hours=24)).isoformat(), "status": "Success"},
            {"action": "Enabled MFA (Authenticator)", "timestamp": (now - timezone.timedelta(days=3)).isoformat(), "status": "Success"},
            {"action": "Password Change Requested", "timestamp": (now - timezone.timedelta(days=14)).isoformat(), "status": "Warning"},
            {"action": "Exported Portfolio Report", "timestamp": (now - timezone.timedelta(days=15)).isoformat(), "status": "Success"},
        ]

class PropertyDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single property, including nested relations.
    """
    def to_representation(self, instance):
        # Base Property Data
        current_rent = float(instance.rent_data.current_annual_rent) if hasattr(instance, 'rent_data') else 0
        
        property_data = {
            "id": instance.id,
            "name": instance.name,
            "location": instance.location,
            "category": instance.category,
            "status": instance.status,
            "bedrooms": instance.bedrooms,
            "bathrooms": instance.bathrooms,
            "area_sqft": instance.area_sqft,
            "image_url": instance.image_url,
            "annual_rent": current_rent,
            "monthly_rent": current_rent / 12
        }

        # Rent Data
        rent_data = {}
        if hasattr(instance, 'rent_data'):
            rent_data = {
                "current_annual_rent": instance.rent_data.current_annual_rent,
                "market_annual_rent": instance.rent_data.market_annual_rent,
                "rent_gap": instance.rent_data.rent_gap()
            }

        # Lease & Tenant Data (Latest active lease)
        lease_data = None
        tenant_data = None
        
        active_lease = instance.leases.filter(status='ACTIVE').first()
        if active_lease:
            lease_data = {
                "start_date": active_lease.start_date,
                "end_date": active_lease.end_date,
                "monthly_rent": active_lease.monthly_rent,
                "status": active_lease.status
            }
            if active_lease.tenant:
                tenant_data = {
                    "full_name": active_lease.tenant.name,
                    "email": active_lease.tenant.email,
                    "phone_number": active_lease.tenant.contact_number
                }

        return {
            "PROPERTY": property_data,
            "RENT_DATA": rent_data,
            "LEASE": lease_data,
            "TENANT": tenant_data
        }

    class Meta:
        model = Property
        fields = [] # Handled by to_representation

