from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user

def permission_required(permission_name):
    """Decorator to enforce role permissions on route handlers."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.has_perm(permission_name):
                flash(f"Access Denied: You do not have permission for '{permission_name}'.", "danger")
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def num_to_words_pkr(number):
    """Converts a numerical amount into Pakistani Rupees in words (Lakh, Crore format)."""
    try:
        number = round(float(number), 2)
    except (ValueError, TypeError):
        return "Zero Rupees Only"

    if number == 0:
        return "Zero Rupees Only"

    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
             "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
             "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def convert_below_thousand(n):
        res = ""
        if n >= 100:
            res += units[n // 100] + " Hundred "
            n %= 100
        if n >= 20:
            res += tens[n // 10] + " "
            n %= 10
        if n > 0:
            res += units[n] + " "
        return res.strip()

    rupees = int(number)
    paisa = int(round((number - rupees) * 100))

    if rupees == 0:
        rupees_str = "Zero"
    else:
        # South Asian Numbering System: Crore (1,00,00,000), Lakh (1,00,000), Thousand (1,000)
        crore = rupees // 10000000
        rupees %= 10000000
        lakh = rupees // 100000
        rupees %= 100000
        thousand = rupees // 1000
        remainder = rupees % 1000

        parts = []
        if crore > 0:
            parts.append(convert_below_thousand(crore) + " Crore")
        if lakh > 0:
            parts.append(convert_below_thousand(lakh) + " Lakh")
        if thousand > 0:
            parts.append(convert_below_thousand(thousand) + " Thousand")
        if remainder > 0:
            parts.append(convert_below_thousand(remainder))

        rupees_str = " ".join(parts).strip()

    result = f"Rupees {rupees_str}"
    if paisa > 0:
        result += f" and {convert_below_thousand(paisa)} Paisa"
    result += " Only"
    return result


def log_activity(action, entity_type=None, entity_id=None, details=None):
    """Records an action in the system activity/audit log."""
    from app.models import db, ActivityLog
    try:
        user_id = current_user.id if current_user and current_user.is_authenticated else None
        ip_addr = request.remote_addr if request else None
        log_entry = ActivityLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            details=str(details) if details else None,
            ip_address=ip_addr
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Failed to record activity log: {e}")
