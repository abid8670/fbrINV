from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import CompanySetting, db
from app.fbr_service import FBRService
from app.utils import permission_required, log_activity
from app.setup_manager import get_config, save_config

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
@permission_required('can_edit_settings')
def index():
    settings = CompanySetting.get_settings()
    cfg = get_config()

    if request.method == 'POST':
        settings.company_name = request.form.get('company_name', '').strip()
        settings.ntn = request.form.get('ntn', '').strip()
        settings.strn = request.form.get('strn', '').strip()
        settings.business_address = request.form.get('business_address', '').strip()
        settings.city = request.form.get('city', '').strip()
        settings.province = request.form.get('province', 'Punjab')
        settings.phone = request.form.get('phone', '').strip()
        settings.email = request.form.get('email', '').strip()
        settings.pos_id = request.form.get('pos_id', '').strip()
        settings.branch_code = request.form.get('branch_code', '').strip()
        
        settings.fbr_environment = request.form.get('fbr_environment', 'mock')
        settings.fbr_api_url = request.form.get('fbr_api_url', '').strip()
        
        token_input = request.form.get('fbr_bearer_token', '').strip()
        if token_input:
            settings.fbr_bearer_token = token_input

        settings.default_tax_rate = float(request.form.get('default_tax_rate') or 18.0)
        settings.default_further_tax_rate = float(request.form.get('default_further_tax_rate') or 4.0)

        # AI Voice settings
        if 'ai_voice_language' in request.form:
            cfg['ai_voice'] = {
                'enabled': bool(request.form.get('ai_voice_enabled')),
                'language': request.form.get('ai_voice_language', 'en-US'),
                'speech_rate': float(request.form.get('ai_voice_rate') or 1.0),
                'api_provider': request.form.get('ai_voice_provider', 'browser'),
                'api_key': request.form.get('ai_voice_api_key', '').strip()
            }
            save_config(cfg)

        db.session.commit()
        log_activity("Updated Company, FBR Gateway & AI Voice Settings", "Settings", settings.id)
        flash('Company, FBR Gateway, and AI Voice settings have been saved successfully.', 'success')
        return redirect(url_for('settings.index'))

    return render_template('settings/fbr.html', settings=settings, cfg=cfg)

@settings_bp.route('/test-connection', methods=['POST'])
@login_required
@permission_required('can_edit_settings')
def test_connection():
    settings = CompanySetting.get_settings()
    result = FBRService.test_connection(settings)
    log_activity(f"Tested FBR Connection ({settings.fbr_environment}): {'Success' if result.get('success') else 'Failed'}", "Settings", settings.id)
    return jsonify(result)

@settings_bp.route('/test-voice', methods=['POST'])
def test_voice():
    from app.ai_voice_service import AIVoiceService
    data = request.get_json() or {}
    cfg = get_config()
    
    provider = data.get('provider') or cfg.get('ai_voice', {}).get('api_provider', 'browser')
    api_key = data.get('api_key')
    if api_key is None:
        api_key = cfg.get('ai_voice', {}).get('api_key', '')
    language = data.get('language') or cfg.get('ai_voice', {}).get('language', 'en-US')
    
    result = AIVoiceService.test_voice_api(provider, api_key, language)
    return jsonify(result)
