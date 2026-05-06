import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Property, RentData, Occupancy, OwnerProfile, Tenant, Lease, Valuation, PropertyImage

class Command(BaseCommand):
    help = 'Seed database with 60 properties and analytics data as per FRD'

    def handle(self, *args, **kwargs):
        self.stdout.write("Wiping existing data...")
        Property.objects.all().delete()
        Tenant.objects.all().delete()
        Lease.objects.all().delete()
        # cascades should handle most, but just in case:
        RentData.objects.all().delete()
        Occupancy.objects.all().delete()
        Valuation.objects.all().delete()
        PropertyImage.objects.all().delete()
        # DO NOT delete Users as per request

        self.stdout.write("Wiping complete. Starting seed...")

        # 1. OWNER PROFILE
        user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@amwal.com'}
        )
        if not user.password:
            user.set_password('admin123')
            user.is_superuser = True
            user.is_staff = True
            user.save()
        
        profile, _ = OwnerProfile.objects.get_or_create(user=user)
        profile.full_name = "H. Siddiqui"
        profile.portfolio_units = 60
        profile.save()

        # 2. SEED DATA ARRAYS
        types = [
            Property.PropertyType.LX_VILLA,
            Property.PropertyType.ST_VILLA,
            Property.PropertyType.APARTMENT,
            Property.PropertyType.FLAT
        ]
        
        locs = ["Palm Jumeirah", "Emirates Hills", "Dubai Hills", "Arabian Ranches", "JVC", "Downtown", "Marina", "Business Bay"]
        nationalities = ["Emirati", "British", "Indian", "American", "French", "German", "Canadian", "Australian"]
        
        luxury_urls = [
            "https://images.unsplash.com/photo-1613977257363-707ba9348227",
            "https://images.unsplash.com/photo-1600607687644-c7171b42498b",
            "https://images.unsplash.com/photo-1600585154526-990dced4db0d",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c",
            "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde",
            "https://images.unsplash.com/photo-1600566752355-35792bedcfea",
            "https://images.unsplash.com/photo-1600607688969-a5bfcd646154",
            "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d"
        ]
        standard_urls = [
            "https://images.unsplash.com/photo-1572120360610-d971b9d7767c",
            "https://images.unsplash.com/photo-1605146769289-440113cc3d00",
            "https://images.unsplash.com/photo-1564013799919-ab600027ffc6",
            "https://images.unsplash.com/photo-1598228723793-52759bba239c",
            "https://images.unsplash.com/photo-1576941089067-2de3c901e126",
            "https://images.unsplash.com/photo-1600585152915-d208bec867a1",
            "https://images.unsplash.com/photo-1605276373954-0c4a0dac5b12",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c"
        ]
        apartment_urls = [
            "https://images.unsplash.com/photo-1501183638710-841dd1904471",
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
            "https://images.unsplash.com/photo-1493809842364-78817add7ffb",
            "https://images.unsplash.com/photo-1493666438817-866a91353ca9",
            "https://images.unsplash.com/photo-1507089947368-19c1da9775ae",
            "https://images.unsplash.com/photo-1560185127-6ed189bf02f4",
            "https://images.unsplash.com/photo-1486304873000-235643847519",
            "https://images.unsplash.com/photo-1494526585095-c41746248156"
        ]
        flat_urls = [
            "https://images.unsplash.com/photo-1484154218962-a197022b5858",
            "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85",
            "https://images.unsplash.com/photo-1505691938895-1758d7feb511",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688",
            "https://images.unsplash.com/photo-1505691723518-36a5ac3b2d00"
        ]

        # 3. GENERATE 60 PROPERTIES
        for i in range(60):
            p_type = types[i % 4]
            property = Property(
                property_type=p_type,
                area=random.choice(locs),
                bedrooms=random.randint(1, 6),
                floor_area=Decimal(random.randint(800, 8000))
            )
            property.save() # Triggers unit_ref and category generation

            # Create Rent Data
            market_annual = Decimal(random.randint(60000, 1200000))
            # Create some rent gaps
            gap_rand = random.random()
            if gap_rand < 0.3: # 30% have high gap
                current_annual = market_annual - Decimal(random.randint(70000, 150000))
            elif gap_rand < 0.6: # 30% have small gap
                current_annual = market_annual - Decimal(random.randint(5000, 15000))
            else: # 40% at/near market
                current_annual = market_annual - Decimal(random.randint(0, 2000))

            RentData.objects.create(
                property=property,
                current_annual_rent=current_annual,
                current_monthly_rent=current_annual / 12,
                market_annual_rent=market_annual,
                market_monthly_rent=market_annual / 12,
                last_review_date=date.today() - timedelta(days=random.randint(30, 365))
            )

            # Create Valuation
            Valuation.objects.create(
                property=property,
                value=market_annual * 15, # Rough valuation
                valuation_date=date.today(),
                source="RERA Index"
            )

            # Add UNIQUE Images (Phase 2)
            url_pool = []
            if p_type == Property.PropertyType.LX_VILLA: url_pool = luxury_urls
            elif p_type == Property.PropertyType.ST_VILLA: url_pool = standard_urls
            elif p_type == Property.PropertyType.APARTMENT: url_pool = apartment_urls
            else: url_pool = flat_urls

            # Pick a unique set of 3 images from pool (rotate based on i)
            start_idx = (i * 3) % len(url_pool)
            for idx in range(3):
                base_url = url_pool[(start_idx + idx) % len(url_pool)]
                # Append w=800 param for consistent resolution
                img_url = f"{base_url}?w=800"
                PropertyImage.objects.create(property=property, image_url=img_url, order=idx)

            # 4. LEASES, TENANTS & OCCUPANCY
            # 80% Occupied, 20% Vacant
            is_occupied = (i % 5) != 0
            
            if is_occupied:
                tenant = Tenant.objects.create(
                    name=f"Tenant {i}",
                    contact=f"+9715{random.randint(100, 999)}{random.randint(1000, 9999)}",
                    email=f"tenant{i}@example.com",
                    id_passport=f"DXB-{random.randint(10000, 99999)}",
                    nationality=random.choice(nationalities)
                )

                # Lease Start: some long ago, some recent
                start_date = date.today() - timedelta(days=random.randint(30, 400))
                
                # Lease End: some expiring soon (Phase 14 Alerts)
                if i % 10 == 0: # 10% expiring soon
                    end_date = date.today() + timedelta(days=random.randint(1, 13))
                else:
                    end_date = start_date + timedelta(days=365)

                Lease.objects.create(
                    tenant=tenant,
                    property=property,
                    start_date=start_date,
                    end_date=end_date,
                    annual_rent=current_annual,
                    monthly_rent=current_annual / 12,
                    payment_frequency="Quarterly",
                    deposit=current_annual / 10,
                    status=Lease.LeaseStatus.ACTIVE
                )
                # Successive update by Signal to 'Occupied'
            else:
                # Set as Vacant
                # Vacancy Start: some long ago (Phase 14 Alerts)
                if i % 8 == 0: # Some critical vacancies
                     vac_start = date.today() - timedelta(days=random.randint(61, 120))
                else:
                     vac_start = date.today() - timedelta(days=random.randint(5, 45))
                
                occ = Occupancy.objects.get(property=property)
                occ.status = Occupancy.OccupancyStatus.VACANT
                occ.vacancy_start_date = vac_start
                occ.save()

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded 60 properties for H. Siddiqui."))
