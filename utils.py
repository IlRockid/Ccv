from datetime import datetime, timedelta
from models import Guest

def check_expiring_permits():
    """Check for residence permits expiring within 7 days"""
    today = datetime.now().date()
    seven_days_from_now = today + timedelta(days=7)
    
    # Find guests with permits expiring in the next 7 days
    expiring_permits = Guest.query.filter(
        Guest.permit_expiry.isnot(None),
        Guest.permit_expiry <= seven_days_from_now,
        Guest.permit_expiry >= today
    ).all()
    
    return expiring_permits

def format_date(date):
    """Format a date object to string"""
    if date:
        return date.strftime('%d/%m/%Y')
    return ''

def calculate_age(birth_date):
    """Calculate age based on birth date"""
    if birth_date:
        today = datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    return None
