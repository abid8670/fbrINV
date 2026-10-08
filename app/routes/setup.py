from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, current_user
from app.setup_manager import (
    is_configured, get_config, save_config,
    build_sqlalchemy_uri, test_db_connection
)
from app.models import db, User, CompanySetting, Customer, Item
from app.utils import log_activity

setup_bp = Blueprint('setup', __name__, url_prefix='/setup')

@setup_bp.route('/', methods=['GET', 'POST'])
def index():
    cfg = get_config()

    if request.method == 'POST':
        db_type = request.form.get('db_type', 'sqlite')
        
        # MySQL or Postgres params
        params = {}
        if db_type in ['mysql', 'postgresql']:
            params = {
                'host': request.form.get(f'{db_type}_host', 'localhost').strip(),
                'port': int(request.form.get(f'{db_type}_port') or (3306 if db_type == 'mysql' else 5432)),
                'user': request.form.get(f'{db_type}_user', '').strip(),
                'password': request.form.get(f'{db_type}_password', ''),
                'database': request.form.get(f'{db_type}_database', 'fbr_invoicing').strip()
            }
            # Test connection
            test_res = test_db_connection(db_type, params)
            if not test_res.get('success'):
                flash(f"Database Connection Failed: {test_res.get('message')}. Please check credentials or start the database server.", "danger")
                return render_template('setup/wizard.html', cfg=cfg)

        # Build URI
        sqlalchemy_uri = build_sqlalchemy_uri(db_type, params)
        cfg['db_type'] = db_type
        cfg['sqlalchemy_uri'] = sqlalchemy_uri
        if db_type == 'mysql':
            cfg['mysql'] = params
        elif db_type == 'postgresql':
            cfg['postgresql'] = params

        # AI Voice Settings
        cfg['ai_voice'] = {
            'enabled': bool(request.form.get('ai_voice_enabled')),
            'language': request.form.get('ai_voice_language', 'en-US'),
            'speech_rate': float(request.form.get('ai_voice_rate') or 1.0),
            'api_provider': request.form.get('ai_voice_provider', 'browser'),
            'api_key': request.form.get('ai_voice_api_key', '').strip()
        }
        cfg['is_configured'] = True

        save_config(cfg)

        # Reconfigure active SQLAlchemy engine
        try:
            from flask import current_app
            from app.setup_manager import reconfigure_sqlalchemy_engine
            app_obj = current_app._get_current_object()
            reconfigure_sqlalchemy_engine(app_obj, sqlalchemy_uri)

            with app_obj.app_context():
                db.create_all()

                # Seed/Update Admin
                admin_user = request.form.get('admin_username', 'admin').strip().lower()
                admin_pass = request.form.get('admin_password', 'admin123')
                admin_name = request.form.get('admin_name', 'System Administrator').strip()
                admin_email = request.form.get('admin_email', 'admin@fbr-invoice.pk').strip()

                admin = User.query.filter_by(username=admin_user).first()
                if not admin:
                    admin = User(
                        username=admin_user,
                        email=admin_email,
                        full_name=admin_name,
                        role='admin'
                    )
                    admin.set_password(admin_pass)
                    admin.apply_role_preset('admin')
                    db.session.add(admin)
                else:
                    admin.set_password(admin_pass)
                    admin.apply_role_preset('admin')

                # Company Profile
                company_name = request.form.get('company_name', 'My Business (Pvt) Ltd').strip()
                seller_ntn = request.form.get('seller_ntn', '7291845-3').strip()
                seller_strn = request.form.get('seller_strn', '3277876123456').strip()
                city = request.form.get('city', 'Lahore').strip()
                province = request.form.get('province', 'Punjab').strip()
                address = request.form.get('business_address', 'Main Boulevard').strip()

                settings = CompanySetting.query.first()
                if not settings:
                    settings = CompanySetting(
                        company_name=company_name,
                        ntn=seller_ntn,
                        strn=seller_strn,
                        city=city,
                        province=province,
                        business_address=address,
                        fbr_environment='mock'
                    )
                    db.session.add(settings)
                else:
                    settings.company_name = company_name
                    settings.ntn = seller_ntn
                    settings.strn = seller_strn
                    settings.city = city
                    settings.province = province
                    settings.business_address = address

                # Seed basic items and customer if table empty
                if Customer.query.count() == 0:
                    c1 = Customer(name="Al-Rehman Enterprises", buyer_type="Registered", ntn="1428590-7", strn="1700142859011", city="Lahore", province="Punjab")
                    c2 = Customer(name="Tariq & Sons General Mart", buyer_type="Unregistered", cnic="35202-7654321-9", city="Lahore", province="Punjab")
                    db.session.add_all([c1, c2])

                if Item.query.count() == 0:
                    i1 = Item(item_code="ITM-001", name="Dell Business Laptop Core i7", hs_code="8471.3010", uom="NOS", unit_price=225000.0, sales_tax_rate=18.0)
                    i2 = Item(item_code="ITM-002", name="Cisco Gigabit Switch 24-Port", hs_code="8517.6270", uom="NOS", unit_price=95000.0, sales_tax_rate=18.0)
                    db.session.add_all([i1, i2])

                db.session.commit()
                login_user(admin)
                log_activity(f"Completed initial software setup with {db_type.upper()} database", "Setup", admin.id)

            flash(f"Installation Complete! Connected to {db_type.upper()} database successfully.", "success")
            return redirect(url_for('dashboard.index'))

        except Exception as e:
            flash(f"Setup Error while initializing database tables: {str(e)}", "danger")
            return render_template('setup/wizard.html', cfg=cfg)

    return render_template('setup/wizard.html', cfg=cfg)

@setup_bp.route('/test-db', methods=['POST'])
def test_db():
    data = request.get_json() or {}
    db_type = data.get('db_type', 'sqlite')
    params = data.get('params', {})
    res = test_db_connection(db_type, params)
    return jsonify(res)

@setup_bp.route('/test-voice', methods=['POST'])
def test_voice():
    from app.ai_voice_service import AIVoiceService
    data = request.get_json() or {}
    provider = data.get('provider', 'browser')
    api_key = data.get('api_key', '')
    language = data.get('language', 'en-US')
    
    result = AIVoiceService.test_voice_api(provider, api_key, language)
    return jsonify(result)
