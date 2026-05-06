import os
import django
import random
from datetime import date, timedelta
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Property, RentData, Occupancy, OwnerProfile, Valuation, PropertyImage, Tenant, Lease
from django.contrib.auth.models import User

def populate():
    print("Flushing existing data...")
    Property.objects.all().delete()
    User.objects.all().delete()
    Tenant.objects.all().delete()

    print("Creating Superuser and Owner Profile...")
    user = User.objects.create_superuser('admin', 'admin@amwal.com', 'admin123')
    # Signal creates Profile, let's update it
    profile = user.owner_profile
    profile.portfolio_units = 60
    profile.full_name = "H. Siddiqui"
    profile.save()

    property_types = [
        (Property.PropertyType.LX_VILLA, 10, "Luxury Villas"),
        (Property.PropertyType.ST_VILLA, 15, "Standard Villas"),
        (Property.PropertyType.APARTMENT, 20, "Larger Apartments"),
        (Property.PropertyType.FLAT, 15, "Standard Flats"),
    ]

    assets = {
        Property.PropertyType.LX_VILLA: {
            "areas": ["Palm Jumeirah", "Emirates Hills"],
            "beds": [5, 6, 7],
            "sqft": [6000, 8500, 10000],
            "rent": [800000, 1200000],
            "value": [15000000, 25000000],
            "img": [
                "https://images.unsplash.com/photo-1600607687644-c7171b42498b",
                "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c",
                "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde",
                "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea",
                "https://images.unsplash.com/photo-1600607688969-a5bfcd646154"
            ]
        },
        Property.PropertyType.ST_VILLA: {
            "areas": ["Dubai Hills", "Arabian Ranches"],
            "beds": [3, 4, 5],
            "sqft": [3500, 5000],
            "rent": [250000, 450000],
            "value": [4000000, 7000000],
            "img": [
                "https://images.unsplash.com/photo-1572120360610-d971b9d7767c",
                "https://images.unsplash.com/photo-1600585152915-d208bec867a1",
                "https://images.unsplash.com/photo-1605276373954-0c4a0dac5b12",
                "https://images.unsplash.com/photo-1600585154340-be6161a56a0c"
            ]
        },
        Property.PropertyType.APARTMENT: {
            "areas": ["Dubai Marina", "Downtown Dubai"],
            "beds": [2, 3],
            "sqft": [1400, 2200],
            "rent": [150000, 280000],
            "value": [2000000, 4500000],
            "img": [
                "https://images.unsplash.com/photo-1501183638710-841dd1904471",
                "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
                "https://images.unsplash.com/photo-1493809842364-78817add7ffb",
                "https://images.unsplash.com/photo-1493666438817-866a91353ca9"
            ]
        },
        Property.PropertyType.FLAT: {
            "areas": ["JVC", "Silicon Oasis"],
            "beds": [0, 1],
            "sqft": [500, 900],
            "rent": [50000, 95000],
            "value": [600000, 1200000],
            "img": [
                "https://images.unsplash.com/photo-1484154218962-a197022b5858",
                "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85",
                "https://images.unsplash.com/photo-1505691938895-1758d7feb511",
                "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688"
            ]
        }
    }

    print("Generating 60 Units...")
    
    all_properties = []
    for p_type, count, cat_name in property_types:
        config = assets[p_type]
        for i in range(count):
            p = Property.objects.create(
                property_type=p_type,
                area=random.choice(config['areas']),
                bedrooms=random.choice(config['beds']),
                floor_area=Decimal(str(random.choice(config['sqft'])))
            )
            
            # Create RentData
            market_annual = Decimal(str(random.randint(config['rent'][0], config['rent'][1])))
            # Leakage: 20% of units are below market
            current_annual = market_annual * (Decimal('0.88') if random.random() < 0.2 else Decimal('1.0'))
            
            RentData.objects.create(
                property=p,
                current_annual_rent=current_annual,
                current_monthly_rent=current_annual / 12,
                market_annual_rent=market_annual,
                market_monthly_rent=market_annual / 12
            )
            
            # Valuation
            val_amount = Decimal(str(random.randint(config['value'][0], config['value'][1])))
            Valuation.objects.create(
                property=p,
                value=val_amount,
                valuation_date=date.today(),
                source="Internal Assessment"
            )
            
            # Images
            for img_idx, img_url in enumerate(config['img']):
                PropertyImage.objects.create(
                    property=p,
                    image_url=img_url,
                    order=img_idx + 1 # Order 1 is primary
                )

            all_properties.append(p)

    # Manage Occupancy & Leases
    print("Setting up Occupancy & Leases...")
    # Target 95% occupancy -> ~57 occupied, 3 vacant
    random.shuffle(all_properties)
    
    tenant_count = 0
    for idx, p in enumerate(all_properties):
        occ = p.occupancy
        if idx < 57: # 57 units occupied
            occ.status = Occupancy.OccupancyStatus.OCCUPIED
            occ.save()
            
            # Create Tenant and Lease
            tenant_count += 1
            tenant = Tenant.objects.create(
                name=f"Tenant {tenant_count}",
                email=f"tenant{tenant_count}@example.com"
            )
            
            start_date = date.today() - timedelta(days=random.randint(30, 300))
            end_date = start_date + timedelta(days=365)
            
            Lease.objects.create(
                tenant=tenant,
                property=p,
                start_date=start_date,
                end_date=end_date,
                annual_rent=p.rent_data.current_annual_rent,
                monthly_rent=p.rent_data.current_monthly_rent,
                status=Lease.LeaseStatus.ACTIVE
            )
        else:
            # Vacant
            occ.status = Occupancy.OccupancyStatus.VACANT
            occ.vacancy_start_date = date.today() - timedelta(days=random.randint(10, 90))
            occ.vacancy_reason = random.choice(["End of Lease", "Renovation Pending", "Market Listing"])
            occ.save()

    print(f"Successfully populated {Property.objects.count()} properties.")

if __name__ == '__main__':
    populate()
