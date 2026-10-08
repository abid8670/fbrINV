from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models import ActivityLog
from app.utils import permission_required

audit_bp = Blueprint('audit', __name__, url_prefix='/audit-logs')

@audit_bp.route('/')
@login_required
@permission_required('can_manage_users')
def index():
    action_filter = request.args.get('action', '').strip()
    entity_filter = request.args.get('entity_type', '').strip()

    query = ActivityLog.query
    if action_filter:
        query = query.filter(ActivityLog.action.ilike(f'%{action_filter}%'))
    if entity_filter:
        query = query.filter_by(entity_type=entity_filter)

    logs = query.order_by(ActivityLog.created_at.desc()).limit(150).all()
    return render_template('audit/list.html', logs=logs, action_filter=action_filter, entity_filter=entity_filter)
