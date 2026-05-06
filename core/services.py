from django.db.models import Sum, F, Count, Q
from django.utils import timezone
from .models import Property, Lease, RentData, Occupancy, Valuation, Tenant
from decimal import Decimal

class KPIService:
    @staticmethod
    def get_portfolio_kpis():
        total_units = Property.objects.count()
        occupied_units = Occupancy.objects.filter(status='Occupied').count()
        
        occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
        
        # Monthly Income = Sum of current_monthly_rent for occupied units
        monthly_income = RentData.objects.filter(
            property__occupancy__status='Occupied'
        ).aggregate(total=Sum('current_monthly_rent'))['total'] or Decimal('0')
        
        # Rent Leakage = Sum of positive rent gaps (Market - Current)
        # Handle cases where market or current rents might be None or 0
        rent_leakage = RentData.objects.annotate(
            gap=F('market_annual_rent') - F('current_annual_rent')
        ).filter(gap__gt=0).aggregate(total=Sum('gap'))['total'] or Decimal('0')
        
        market_potential = RentData.objects.aggregate(total=Sum('market_annual_rent'))['total'] or Decimal('0')
        
        return {
            "total_units": total_units,
            "occupancy_rate": round(occupancy_rate, 2),
            "monthly_income": float(monthly_income),
            "rent_leakage": float(rent_leakage),
            "market_potential": float(market_potential)
        }

    @staticmethod
    def export_to_csv(view_id):
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)

        if view_id == 'rental-intelligence':
            data = RentGapService.get_rent_gap_analysis()
            writer.writerow(['Unit Ref', 'Type', 'Current Rent', 'Market Rent', 'Gap', 'Status'])
            for row in data:
                writer.writerow([row['unit_ref'], row['type'], row['current'], row['market'], row['gap'], row['status']])
        
        elif view_id == 'occupancy':
            data = OccupancyService.get_vacancy_data()
            writer.writerow(['Unit Ref', 'Days Vacant', 'Monthly Rent', 'Vacancy Loss', 'Reason'])
            for row in data['vacancy_details']:
                writer.writerow([row['unit_ref'], row['days_vacant'], row['monthly_rent'], row['vacancy_loss'], row['reason']])

        return output.getvalue()

class RentGapService:
    @staticmethod
    def get_rent_gap_analysis():
        rent_data = RentData.objects.all().select_related('property')
        
        analysis = []
        for rd in rent_data:
            current = rd.current_annual_rent or Decimal('0')
            market = rd.market_annual_rent or Decimal('0')
            gap = market - current
            
            if gap > 60000:
                status = "Critical"
            elif gap >= 8000:
                status = "Review"
            else:
                status = "At Market"
            
            analysis.append({
                "unit_ref": rd.property.unit_ref if rd.property else "Unknown",
                "type": rd.property.get_property_type_display() if rd.property else "Unknown",
                "current": float(current),
                "market": float(market),
                "gap": float(gap),
                "status": status
            })
            
        return analysis

class OccupancyService:
    @staticmethod
    def get_vacancy_data():
        vacant_records = Occupancy.objects.filter(status='Vacant').select_related('property', 'property__rent_data')
        
        today = timezone.now().date()
        vacancy_details = []
        total_vacancy_loss = Decimal('0')
        
        for occ in vacant_records:
            if not occ.property: continue
            
            days_vacant = (today - occ.vacancy_start_date).days if occ.vacancy_start_date else 0
            
            # Safe Rent Access
            try:
                monthly_rent = occ.property.rent_data.current_monthly_rent
            except AttributeError:
                monthly_rent = Decimal('0')
                
            monthly_rent = monthly_rent or Decimal('0')
            
            # Vacancy Loss = (days_vacant * monthly_rent) / 30
            loss = (Decimal(days_vacant) * monthly_rent) / Decimal('30') if days_vacant > 0 else Decimal('0')
            total_vacancy_loss += loss
            
            vacancy_details.append({
                "unit_ref": occ.property.unit_ref,
                "days_vacant": days_vacant,
                "monthly_rent": float(monthly_rent),
                "vacancy_loss": float(loss),
                "reason": occ.vacancy_reason or "N/A"
            })
        
        return {
            "vacancy_details": vacancy_details,
            "total_vacancy_loss": float(total_vacancy_loss)
        }

class FinancialService:
    @staticmethod
    def get_revenue_waterfall():
        # Revenue Waterfall: Market Potential - Vacancy Loss - Rent Leakage - Management Fees = Net Income
        kpis = KPIService.get_portfolio_kpis()
        vacancy_data = OccupancyService.get_vacancy_data()
        
        market_potential = Decimal(str(kpis['market_potential']))
        vacancy_loss = Decimal(str(vacancy_data['total_vacancy_loss']))
        rent_leakage = Decimal(str(kpis['rent_leakage']))
        
        # Management Fees: Assuming 5% of potential for this calculation as a placeholder if not in FRD
        management_fees = market_potential * Decimal('0.05')
        
        net_income = market_potential - vacancy_loss - rent_leakage - management_fees
        
        return {
            "market_potential": float(market_potential),
            "vacancy_loss": float(vacancy_loss),
            "rent_leakage": float(rent_leakage),
            "management_fees": float(management_fees),
            "net_income": float(net_income)
        }

    @staticmethod
    def get_portfolio_yield():
        # Yield = (Annual Income / Property Value) * 100
        # Annual Income = Total current_annual_rent of occupied properties
        annual_income = RentData.objects.filter(
            property__occupancy__status='Occupied'
        ).aggregate(total=Sum('current_annual_rent'))['total'] or Decimal('0')
        
        total_value = Valuation.objects.aggregate(total=Sum('value'))['total'] or Decimal('0')
        
        if total_value == 0:
            return 0
            
        yield_val = (annual_income / total_value * 100)
        return round(float(yield_val), 2)

class AlertService:
    @staticmethod
    def get_dashboard_alerts():
        alerts = []
        today = timezone.now().date()
        
        # 1. Vacancy > 60 days -> Critical
        vacant_long = Occupancy.objects.filter(status='Vacant', vacancy_start_date__lte=today - timezone.timedelta(days=60))
        for item in vacant_long:
            alerts.append({
                "severity": "Critical",
                "message": f"Unit {item.property.unit_ref} has been vacant for over 60 days.",
                "type": "Vacancy"
            })
            
        # 2. Lease < 14 days -> Urgent
        expiring_leases = Lease.objects.filter(status='Active', end_date__lte=today + timezone.timedelta(days=14))
        for lease in expiring_leases:
            alerts.append({
                "severity": "Urgent",
                "message": f"Lease for {lease.tenant.name} ({lease.property.unit_ref}) expires in less than 14 days.",
                "type": "Lease"
            })
            
        # 3. Rent gap > 80k -> Review
        high_gaps = RentData.objects.annotate(
            gap=F('market_annual_rent') - F('current_annual_rent')
        ).filter(gap__gt=80000)
        for rd in high_gaps:
             alerts.append({
                "severity": "Review",
                "message": f"Critical rent gap of AED {float(rd.market_annual_rent - rd.current_annual_rent):,.0f} detected for {rd.property.unit_ref}.",
                "type": "Rent"
            })
             
        return alerts
