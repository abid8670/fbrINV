from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Invoice, InvoiceItem, Customer, Item, CompanySetting, db
from app.fbr_service import FBRService
from app.utils import permission_required, log_activity

invoices_bp = Blueprint('invoices', __name__, url_prefix='/invoices')

def generate_next_invoice_number(prefix_type="INV"):
    """Generates an incremental unique invoice number."""
    year = datetime.utcnow().year
    prefix = f"{prefix_type}-{year}-"
    last_inv = Invoice.query.filter(Invoice.invoice_number.like(f"{prefix}%")).order_by(Invoice.id.desc()).first()
    if last_inv:
        try:
            last_seq = int(last_inv.invoice_number.split("-")[-1])
            return f"{prefix}{last_seq + 1:04d}"
        except Exception:
            pass
    return f"{prefix}0001"

@invoices_bp.route('/')
@login_required
def index():
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()
    customer_id = request.args.get('customer_id', type=int)
    inv_type = request.args.get('type', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = Invoice.query
    if status:
        query = query.filter_by(status=status)
    if inv_type:
        query = query.filter_by(invoice_type=inv_type)
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if date_from:
        try:
            d_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(Invoice.invoice_date >= d_from)
        except Exception:
            pass
    if date_to:
        try:
            d_to = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(Invoice.invoice_date <= d_to)
        except Exception:
            pass

    if search:
        query = query.join(Customer).filter(
            (Invoice.invoice_number.ilike(f'%{search}%')) |
            (Invoice.fbr_invoice_number.ilike(f'%{search}%')) |
            (Customer.name.ilike(f'%{search}%'))
        )

    invoices = query.order_by(Invoice.invoice_date.desc(), Invoice.id.desc()).all()
    customers = Customer.query.order_by(Customer.name.asc()).all()

    return render_template(
        'invoices/list.html',
        invoices=invoices,
        customers=customers,
        current_status=status,
        current_type=inv_type,
        search=search,
        date_from=date_from,
        date_to=date_to
    )

@invoices_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_invoices')
def create():
    settings = CompanySetting.get_settings()
    customers = Customer.query.filter_by(is_active=True).order_by(Customer.name.asc()).all()
    items = Item.query.filter_by(is_active=True).order_by(Item.name.asc()).all()

    # Pre-population for Credit Note or Debit Note from existing invoice
    ref_id = request.args.get('ref_id', type=int)
    preset_type = request.args.get('type', 'Sales Invoice')
    ref_invoice = Invoice.query.get(ref_id) if ref_id else None

    if request.method == 'POST':
        action = request.form.get('action', 'draft') # 'draft' or 'fbr_submit'
        invoice_number = request.form.get('invoice_number', '').strip()
        customer_id = request.form.get('customer_id', type=int)
        invoice_type = request.form.get('invoice_type', 'Sales Invoice')
        payment_mode = request.form.get('payment_mode', 'Cash')
        remarks = request.form.get('remarks', '').strip()
        date_str = request.form.get('invoice_date', '')
        
        # Credit / Debit note specific fields
        orig_fbr_no = request.form.get('original_fbr_invoice_number', '').strip()
        orig_inv_id = request.form.get('original_invoice_id', type=int)
        reason = request.form.get('reason_for_issuance', '').strip()

        if not customer_id:
            flash('Please select a customer/buyer.', 'danger')
            return redirect(url_for('invoices.create'))

        try:
            inv_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            inv_date = datetime.utcnow().date()

        prefix_code = "CN" if invoice_type == "Credit Note" else ("DN" if invoice_type == "Debit Note" else "INV")
        if not invoice_number:
            invoice_number = generate_next_invoice_number(prefix_code)

        # Check invoice number uniqueness
        if Invoice.query.filter_by(invoice_number=invoice_number).first():
            invoice_number = f"{invoice_number}-{datetime.utcnow().strftime('%H%M%S')}"

        invoice = Invoice(
            invoice_number=invoice_number,
            invoice_date=inv_date,
            invoice_type=invoice_type,
            customer_id=customer_id,
            payment_mode=payment_mode,
            remarks=remarks,
            original_fbr_invoice_number=orig_fbr_no,
            original_invoice_id=orig_inv_id,
            reason_for_issuance=reason,
            status='Draft',
            created_by_id=current_user.id
        )
        db.session.add(invoice)
        db.session.flush()

        customer = Customer.query.get(customer_id)

        # Process invoice item rows
        item_ids = request.form.getlist('item_id[]')
        descriptions = request.form.getlist('description[]')
        hs_codes = request.form.getlist('hs_code[]')
        uoms = request.form.getlist('uom[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        tax_rates = request.form.getlist('sales_tax_rate[]')
        discounts = request.form.getlist('discount[]')

        has_valid_items = False
        for i in range(len(descriptions)):
            desc = descriptions[i].strip()
            if not desc:
                continue

            qty = float(quantities[i]) if i < len(quantities) and quantities[i] else 1.0
            price = float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0.0
            hs = hs_codes[i].strip() if i < len(hs_codes) and hs_codes[i] else '8471.3010'
            uom = uoms[i].strip() if i < len(uoms) and uoms[i] else 'NOS'
            tax_rate = float(tax_rates[i]) if i < len(tax_rates) and tax_rates[i] else settings.default_tax_rate
            disc = float(discounts[i]) if i < len(discounts) and discounts[i] else 0.0
            raw_item_id = int(item_ids[i]) if i < len(item_ids) and item_ids[i] and item_ids[i].isdigit() else None

            val_of_supply = round(qty * price, 2)
            sales_tax = round(val_of_supply * (tax_rate / 100.0), 2)
            
            # 4% Further Tax if buyer is Unregistered
            further_rate = settings.default_further_tax_rate if customer.buyer_type == 'Unregistered' else 0.0
            further_tax = round(val_of_supply * (further_rate / 100.0), 2)
            total_amt = round(val_of_supply + sales_tax + further_tax - disc, 2)

            item_obj = Item.query.get(raw_item_id) if raw_item_id else None
            item_code = item_obj.item_code if item_obj else f"ITM-{i+1}"

            inv_item = InvoiceItem(
                invoice_id=invoice.id,
                item_id=raw_item_id,
                item_code=item_code,
                description=desc,
                hs_code=hs,
                uom=uom,
                quantity=qty,
                unit_price=price,
                value_of_supply=val_of_supply,
                sales_tax_rate=tax_rate,
                sales_tax_amount=sales_tax,
                further_tax_rate=further_rate,
                further_tax_amount=further_tax,
                discount_amount=disc,
                total_amount=total_amt
            )
            db.session.add(inv_item)
            has_valid_items = True

        if not has_valid_items:
            db.session.rollback()
            flash('At least one line item is required.', 'danger')
            return redirect(url_for('invoices.create'))

        invoice.calculate_totals()
        db.session.commit()
        log_activity(f"Created {invoice.invoice_type}: {invoice.invoice_number}", "Invoice", invoice.id)

        # If user selected "Save & Post to FBR"
        if action == 'fbr_submit':
            if not current_user.has_perm('can_submit_fbr'):
                flash(f"Invoice saved as Draft. You do not have permission to transmit to FBR directly.", "warning")
                return redirect(url_for('invoices.view', id=invoice.id))

            fbr_res = FBRService.submit_invoice(invoice, settings)
            db.session.commit()
            if fbr_res.get('success'):
                log_activity(f"Submitted to FBR: {invoice.invoice_number} (FBR No: {invoice.fbr_invoice_number})", "Invoice", invoice.id)
                flash(f"Invoice {invoice.invoice_number} successfully registered with FBR! FBR No: {invoice.fbr_invoice_number}", 'success')
            else:
                log_activity(f"FBR Submission Failed: {invoice.invoice_number}", "Invoice", invoice.id, fbr_res.get('message'))
                flash(f"Invoice saved locally as Draft/Failed. FBR Submission error: {fbr_res.get('message')}", 'warning')

            return redirect(url_for('invoices.view', id=invoice.id))
        else:
            flash(f"Invoice {invoice.invoice_number} saved as Draft.", 'success')
            return redirect(url_for('invoices.view', id=invoice.id))

    prefix_code = "CN" if preset_type == "Credit Note" else ("DN" if preset_type == "Debit Note" else "INV")
    next_inv_no = generate_next_invoice_number(prefix_code)

    return render_template(
        'invoices/create.html',
        customers=customers,
        items=items,
        settings=settings,
        next_inv_no=next_inv_no,
        today=datetime.utcnow().strftime("%Y-%m-%d"),
        ref_invoice=ref_invoice,
        preset_type=preset_type
    )

@invoices_bp.route('/<int:id>')
@login_required
def view(id):
    invoice = Invoice.query.get_or_404(id)
    settings = CompanySetting.get_settings()
    return render_template('invoices/view.html', invoice=invoice, settings=settings)

@invoices_bp.route('/<int:id>/print')
@login_required
def print_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    settings = CompanySetting.get_settings()
    return render_template('invoices/print.html', invoice=invoice, settings=settings)

@invoices_bp.route('/<int:id>/print-thermal')
@login_required
def print_thermal(id):
    invoice = Invoice.query.get_or_404(id)
    settings = CompanySetting.get_settings()
    return render_template('invoices/print_thermal.html', invoice=invoice, settings=settings)

@invoices_bp.route('/<int:id>/post-fbr', methods=['POST'])
@login_required
@permission_required('can_submit_fbr')
def post_fbr(id):
    invoice = Invoice.query.get_or_404(id)
    settings = CompanySetting.get_settings()
    
    res = FBRService.submit_invoice(invoice, settings)
    db.session.commit()

    if res.get('success'):
        log_activity(f"Submitted to FBR: {invoice.invoice_number} (FBR No: {invoice.fbr_invoice_number})", "Invoice", invoice.id)
        flash(f"Success! Registered with FBR. FBR Fiscal Number: {invoice.fbr_invoice_number}", "success")
    else:
        log_activity(f"FBR Submission Failed: {invoice.invoice_number}", "Invoice", invoice.id, res.get('message'))
        flash(f"FBR Registration Error: {res.get('message')}", "danger")

    return redirect(url_for('invoices.view', id=invoice.id))

@invoices_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('can_manage_invoices')
def delete(id):
    invoice = Invoice.query.get_or_404(id)
    if invoice.status == 'FBR_Submitted':
        flash('Submitted FBR invoices cannot be deleted to maintain fiscal audit compliance. You may issue a Credit Note instead.', 'danger')
    else:
        inv_no = invoice.invoice_number
        inv_id = invoice.id
        db.session.delete(invoice)
        db.session.commit()
        log_activity(f"Deleted Draft Invoice: {inv_no}", "Invoice", inv_id)
        flash(f'Invoice {inv_no} deleted.', 'info')
    return redirect(url_for('invoices.index'))

@invoices_bp.route('/batch-submit', methods=['POST'])
@login_required
@permission_required('can_submit_fbr')
def batch_submit():
    raw_ids = request.form.getlist('invoice_ids')
    submit_all_drafts = request.form.get('submit_all_drafts') == 'true'

    if submit_all_drafts:
        invoices = Invoice.query.filter(Invoice.status != 'FBR_Submitted').all()
    elif raw_ids:
        ids = [int(i) for i in raw_ids if i.isdigit()]
        invoices = Invoice.query.filter(Invoice.id.in_(ids), Invoice.status != 'FBR_Submitted').all()
    else:
        flash("No draft invoices selected for batch FBR submission.", "warning")
        return redirect(url_for('invoices.index'))

    if not invoices:
        flash("No eligible draft invoices found for submission.", "info")
        return redirect(url_for('invoices.index'))

    settings = CompanySetting.get_settings()
    success_count = 0
    fail_count = 0
    error_details = []

    for inv in invoices:
        res = FBRService.submit_invoice(inv, settings)
        if res.get('success'):
            success_count += 1
        else:
            fail_count += 1
            error_details.append(f"{inv.invoice_number}: {res.get('message', 'Failed')}")

    db.session.commit()
    log_activity(f"Batch FBR Submission: {success_count} succeeded, {fail_count} failed", "Invoice")

    if fail_count == 0:
        flash(f"⚡ Batch FBR Submission Complete: All {success_count} invoices were successfully transmitted and registered with FBR!", "success")
    else:
        flash(f"⚡ Batch FBR Submission: {success_count} succeeded, {fail_count} failed. Details: {'; '.join(error_details[:3])}", "warning")

    return redirect(url_for('invoices.index'))

