from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import Item, CompanySetting, db
from app.utils import permission_required, log_activity

items_bp = Blueprint('items', __name__, url_prefix='/items')

@items_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    query = Item.query
    if search:
        query = query.filter(
            (Item.item_code.ilike(f'%{search}%')) |
            (Item.name.ilike(f'%{search}%')) |
            (Item.hs_code.ilike(f'%{search}%'))
        )
    items = query.order_by(Item.item_code.asc()).all()
    return render_template('items/list.html', items=items, search=search)

@items_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_items')
def create():
    settings = CompanySetting.get_settings()
    if request.method == 'POST':
        item_code = request.form.get('item_code', '').strip().upper()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        hs_code = request.form.get('hs_code', '').strip()
        uom = request.form.get('uom', 'NOS').strip().upper()
        unit_price = float(request.form.get('unit_price') or 0.0)
        sales_tax_rate = float(request.form.get('sales_tax_rate') or settings.default_tax_rate)

        if not item_code or not name or not hs_code:
            flash('Item Code, Name, and HS Code are mandatory.', 'danger')
            return render_template('items/form.html', item=None, default_tax_rate=settings.default_tax_rate)

        if Item.query.filter_by(item_code=item_code).first():
            flash(f'An item with code "{item_code}" already exists.', 'danger')
            return render_template('items/form.html', item=None, default_tax_rate=settings.default_tax_rate)

        item = Item(
            item_code=item_code,
            name=name,
            description=description,
            hs_code=hs_code,
            uom=uom,
            unit_price=unit_price,
            sales_tax_rate=sales_tax_rate
        )
        db.session.add(item)
        db.session.commit()
        log_activity(f"Created Item: {item.name} ({item.item_code})", "Item", item.id)
        flash(f'Item "{name}" ({item_code}) created successfully.', 'success')
        return redirect(url_for('items.index'))

    return render_template('items/form.html', item=None, default_tax_rate=settings.default_tax_rate)

@items_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_items')
def edit(id):
    item = Item.query.get_or_404(id)
    settings = CompanySetting.get_settings()
    if request.method == 'POST':
        item_code = request.form.get('item_code', '').strip().upper()
        item.name = request.form.get('name', '').strip()
        item.description = request.form.get('description', '').strip()
        item.hs_code = request.form.get('hs_code', '').strip()
        item.uom = request.form.get('uom', 'NOS').strip().upper()
        item.unit_price = float(request.form.get('unit_price') or 0.0)
        item.sales_tax_rate = float(request.form.get('sales_tax_rate') or settings.default_tax_rate)

        if item_code != item.item_code:
            if Item.query.filter_by(item_code=item_code).first():
                flash(f'An item with code "{item_code}" already exists.', 'danger')
                return render_template('items/form.html', item=item, default_tax_rate=settings.default_tax_rate)
            item.item_code = item_code

        db.session.commit()
        log_activity(f"Updated Item: {item.name} ({item.item_code})", "Item", item.id)
        flash(f'Item "{item.name}" updated successfully.', 'success')
        return redirect(url_for('items.index'))

    return render_template('items/form.html', item=item, default_tax_rate=settings.default_tax_rate)

@items_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('can_manage_items')
def delete(id):
    item = Item.query.get_or_404(id)
    item_name = item.name
    item_id = item.id
    db.session.delete(item)
    db.session.commit()
    log_activity(f"Deleted Item: {item_name}", "Item", item_id)
    flash(f'Item "{item_name}" deleted.', 'info')
    return redirect(url_for('items.index'))

@items_bp.route('/api/all')
@login_required
def api_all():
    items = Item.query.filter_by(is_active=True).order_by(Item.name.asc()).all()
    return jsonify([{
        "id": it.id,
        "item_code": it.item_code,
        "name": it.name,
        "hs_code": it.hs_code,
        "uom": it.uom,
        "unit_price": it.unit_price,
        "sales_tax_rate": it.sales_tax_rate
    } for it in items])

@items_bp.route('/api/<int:id>')
@login_required
def api_detail(id):
    item = Item.query.get_or_404(id)
    return jsonify({
        "id": item.id,
        "item_code": item.item_code,
        "name": item.name,
        "hs_code": item.hs_code,
        "uom": item.uom,
        "unit_price": item.unit_price,
        "sales_tax_rate": item.sales_tax_rate
    })
