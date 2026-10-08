from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, db
from app.utils import permission_required, log_activity

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/')
@login_required
@permission_required('can_manage_users')
def index():
    users = User.query.order_by(User.id.asc()).all()
    return render_template('users/list.html', users=users)

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_users')
def create():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'operator')

        if not username or not email or not password or not full_name:
            flash('All fields are required.', 'danger')
            return render_template('users/form.html', user=None)

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists.', 'danger')
            return render_template('users/form.html', user=None)

        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role
        )
        new_user.set_password(password)

        # Apply role preset or custom checkboxes
        if 'custom_perms' in request.form:
            new_user.can_manage_invoices = bool(request.form.get('can_manage_invoices'))
            new_user.can_submit_fbr = bool(request.form.get('can_submit_fbr'))
            new_user.can_manage_items = bool(request.form.get('can_manage_items'))
            new_user.can_manage_customers = bool(request.form.get('can_manage_customers'))
            new_user.can_manage_users = bool(request.form.get('can_manage_users'))
            new_user.can_edit_settings = bool(request.form.get('can_edit_settings'))
            new_user.can_export_data = bool(request.form.get('can_export_data'))
        else:
            new_user.apply_role_preset(role)

        db.session.add(new_user)
        db.session.commit()
        log_activity(f"Created User: {new_user.username} ({new_user.role})", "User", new_user.id)
        flash(f'User "{username}" created successfully.', 'success')
        return redirect(url_for('users.index'))

    return render_template('users/form.html', user=None)

@users_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_users')
def edit(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '').strip()
        user.email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', user.role)
        new_password = request.form.get('password', '').strip()

        if new_password:
            user.set_password(new_password)

        user.role = role
        user.can_manage_invoices = bool(request.form.get('can_manage_invoices'))
        user.can_submit_fbr = bool(request.form.get('can_submit_fbr'))
        user.can_manage_items = bool(request.form.get('can_manage_items'))
        user.can_manage_customers = bool(request.form.get('can_manage_customers'))
        user.can_manage_users = bool(request.form.get('can_manage_users'))
        user.can_edit_settings = bool(request.form.get('can_edit_settings'))
        user.can_export_data = bool(request.form.get('can_export_data'))

        db.session.commit()
        log_activity(f"Updated User: {user.username}", "User", user.id)
        flash(f'User "{user.username}" updated successfully.', 'success')
        return redirect(url_for('users.index'))

    return render_template('users/form.html', user=user)

@users_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
@permission_required('can_manage_users')
def toggle_status(id):
    if id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('users.index'))

    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    status_str = "activated" if user.is_active else "deactivated"
    log_activity(f"{status_str.title()} User: {user.username}", "User", user.id)
    flash(f'User "{user.username}" has been {status_str}.', 'info')
    return redirect(url_for('users.index'))

@users_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        full_name = request.form.get('full_name', '').strip()

        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('users/profile.html')

        if full_name:
            current_user.full_name = full_name
        if new_password:
            current_user.set_password(new_password)

        db.session.commit()
        log_activity("Updated profile/password", "User", current_user.id)
        flash('Your profile has been updated successfully.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('users/profile.html')
