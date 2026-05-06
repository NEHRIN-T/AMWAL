from rest_framework import permissions

class DashboardPermission(permissions.BasePermission):
    """
    Standard RBAC for AMWAL.
    Admin: Full Access
    Analyst: Metrics + Intelligence
    Manager: Occupancy + Financials
    Viewer: Read-only basic overview
    """
    def has_permission(self, request, view):
        # Allow safe methods for guests (Read-only access)
        if request.method in permissions.SAFE_METHODS:
            return True
            
        if not request.user.is_authenticated:
            return False
        
        # Simple mapping for this Single Client build
        user_role = getattr(request.user.owner_profile, 'role', 'Viewer')
        
        # Admin has everything
        if user_role == 'Admin' or request.user.is_superuser:
            return True
            
        # Analyst can see Overview and Rental Intel
        if user_role == 'Analyst' and view.__name__ in ['portfolio_overview', 'rental_intelligence']:
            return True
            
        # Manager can see Occupancy and Financials
        if user_role == 'Manager' and view.__name__ in ['occupancy_view', 'financial_view']:
            return True

        # Viewer can only see Overview
        if user_role == 'Viewer' and view.__name__ == 'portfolio_overview':
            return True

        return False
