from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from app.models import Invoice, Customer, Item, CompanySetting, db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    total_invoices = Invoice.query.count()
    fbr_submitted = Invoice.query.filter_by(status='FBR_Submitted').count()
    draft_invoices = Invoice.query.filter_by(status='Draft').count()
    failed_invoices = Invoice.query.filter_by(status='Failed').count()

    total_sales = db.session.query(func.coalesce(func.sum(Invoice.grand_total), 0)).scalar() or 0
    total_sales_tax = db.session.query(func.coalesce(func.sum(Invoice.total_sales_tax), 0)).scalar() or 0
    total_further_tax = db.session.query(func.coalesce(func.sum(Invoice.total_further_tax), 0)).scalar() or 0

    total_customers = Customer.query.count()
    total_items = Item.query.count()

    recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(7).all()
    settings = CompanySetting.get_settings()

    return render_template(
        'dashboard.html',
        total_invoices=total_invoices,
        fbr_submitted=fbr_submitted,
        draft_invoices=draft_invoices,
        failed_invoices=failed_invoices,
        total_sales=total_sales,
        total_sales_tax=total_sales_tax,
        total_further_tax=total_further_tax,
        total_customers=total_customers,
        total_items=total_items,
        recent_invoices=recent_invoices,
        settings=settings
    )
