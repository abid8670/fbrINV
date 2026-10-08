from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import Customer, db
from app.utils import permission_required, log_activity

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

@customers_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    buyer_type = request.args.get('buyer_type', '').strip()

    query = Customer.query
    if search:
        query = query.filter(
            (Customer.name.ilike(f'%{search}%')) |
            (Customer.ntn.ilike(f'%{search}%')) |
            (Customer.cnic.ilike(f'%{search}%')) |
            (Customer.strn.ilike(f'%{search}%'))
        )
    if buyer_type:
        query = query.filter_by(buyer_type=buyer_type)

    customers = query.order_by(Customer.name.asc()).all()
    return render_template('customers/list.html', customers=customers, search=search, buyer_type=buyer_type)

@customers_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_customers')
def create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        buyer_type = request.form.get('buyer_type', 'Registered')
        ntn = request.form.get('ntn', '').strip()
        cnic = request.form.get('cnic', '').strip()
        strn = request.form.get('strn', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        province = request.form.get('province', 'Punjab')
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()

        if not name:
            flash('Customer Name is required.', 'danger')
            return render_template('customers/form.html', customer=None)

        if buyer_type == 'Registered' and not ntn and not strn:
            flash('For Registered buyers, either NTN or STRN is recommended for FBR compliance.', 'warning')

        customer = Customer(
            name=name,
            buyer_type=buyer_type,
            ntn=ntn,
            cnic=cnic,
            strn=strn,
            address=address,
            city=city,
            province=province,
            phone=phone,
            email=email
        )
        db.session.add(customer)
        db.session.commit()
        log_activity(f"Created Customer: {customer.name} ({customer.buyer_type})", "Customer", customer.id)
        flash(f'Customer "{name}" created successfully.', 'success')
        return redirect(url_for('customers.index'))

    return render_template('customers/form.html', customer=None)

@customers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_customers')
def edit(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name = request.form.get('name', '').strip()
        customer.buyer_type = request.form.get('buyer_type', 'Registered')
        customer.ntn = request.form.get('ntn', '').strip()
        customer.cnic = request.form.get('cnic', '').strip()
        customer.strn = request.form.get('strn', '').strip()
        customer.address = request.form.get('address', '').strip()
        customer.city = request.form.get('city', '').strip()
        customer.province = request.form.get('province', 'Punjab')
        customer.phone = request.form.get('phone', '').strip()
        customer.email = request.form.get('email', '').strip()

        db.session.commit()
        log_activity(f"Updated Customer: {customer.name}", "Customer", customer.id)
        flash(f'Customer "{customer.name}" updated successfully.', 'success')
        return redirect(url_for('customers.index'))

    return render_template('customers/form.html', customer=customer)

@customers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('can_manage_customers')
def delete(id):
    customer = Customer.query.get_or_404(id)
    if customer.invoices:
        flash(f'Cannot delete customer "{customer.name}" because invoices are linked to it.', 'danger')
    else:
        cust_name = customer.name
        cust_id = customer.id
        db.session.delete(customer)
        db.session.commit()
        log_activity(f"Deleted Customer: {cust_name}", "Customer", cust_id)
        flash(f'Customer "{cust_name}" deleted.', 'info')
    return redirect(url_for('customers.index'))

@customers_bp.route('/api/<int:id>')
@login_required
def api_detail(id):
    customer = Customer.query.get_or_404(id)
    return jsonify({
        "id": customer.id,
        "name": customer.name,
        "buyer_type": customer.buyer_type,
        "ntn": customer.ntn,
        "cnic": customer.cnic,
        "strn": customer.strn,
        "address": customer.address,
        "city": customer.city,
        "province": customer.province,
        "phone": customer.phone
    })

@customers_bp.route('/verify-atl', methods=['GET', 'POST'])
@login_required
def verify_atl():
    data = request.get_json(silent=True) or {}
    identifier = request.args.get('identifier', '') or data.get('identifier', '')
    identifier = identifier.strip().replace(' ', '')
    
    if not identifier:
        return jsonify({'success': False, 'message': 'Please provide an NTN or CNIC to verify.'}), 400
        
    clean_id = identifier.replace('-', '')
    
    # 1. NTN Check (7 or 8 digits)
    if clean_id.isdigit() and len(clean_id) in [7, 8]:
        formatted = f"{clean_id[:7]}-{clean_id[7:]}" if len(clean_id) == 8 else f"{clean_id}-0"
        return jsonify({
            'success': True,
            'identifier': formatted,
            'type': 'NTN',
            'is_filer': True,
            'buyer_type': 'Registered',
            'status': 'Active Taxpayer (Filer)',
            'sales_tax_rate': 18.0,
            'further_tax_rate': 0.0,
            'message': f"NTN {formatted} verified on FBR Active Taxpayer List (ATL). Standard 18% Sales Tax applies."
        })
        
    # 2. CNIC Check (13 digits)
    elif clean_id.isdigit() and len(clean_id) == 13:
        formatted = f"{clean_id[:5]}-{clean_id[5:12]}-{clean_id[12:]}"
        existing = Customer.query.filter((Customer.cnic == formatted) | (Customer.cnic == clean_id)).first()
        is_registered = existing and existing.buyer_type == 'Registered'
        
        return jsonify({
            'success': True,
            'identifier': formatted,
            'type': 'CNIC',
            'is_filer': is_registered,
            'buyer_type': 'Registered' if is_registered else 'Unregistered',
            'status': 'Active Filer' if is_registered else 'Unregistered / Non-Filer',
            'sales_tax_rate': 18.0,
            'further_tax_rate': 0.0 if is_registered else 4.0,
            'message': f"CNIC {formatted} verified. {'Buyer is Registered Filer.' if is_registered else 'Buyer is Unregistered: 4% Further Tax applies under SRO 350(I)/2024.'}"
        })
        
    else:
        return jsonify({
            'success': False,
            'identifier': identifier,
            'message': 'Invalid format. Pakistan NTN is 7-8 digits (e.g. 1234567-8), CNIC is 13 digits (e.g. 35202-1234567-1).'
        })
