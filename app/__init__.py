import os
from flask import Flask
from flask_login import LoginManager
from sqlalchemy import inspect, text
from app.config import Config
from app.models import db, User, CompanySetting, Customer, Item, ActivityLog
from app.utils import num_to_words_pkr

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    import sys
    if getattr(sys, 'frozen', False):
        bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        bundle_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    templates_dir = os.path.join(bundle_dir, 'app', 'templates')
    static_dir = os.path.join(bundle_dir, 'app', 'static')

    app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        except OSError:
            pass

    db.init_app(app)
    login_manager.init_app(app)

    # Strict slashes False so /users and /users/ both work seamlessly
    app.url_map.strict_slashes = False

    # Register Jinja Template Filters
    @app.template_filter('pkr_words')
    def filter_pkr_words(amount):
        return num_to_words_pkr(amount)

    # Global Context Processor for AI Voice Assistant and Config
    @app.context_processor
    def inject_globals():
        from app.setup_manager import get_config
        cfg = get_config()
        return dict(ai_voice_config=cfg.get('ai_voice', {}), app_config=cfg)

    # First-run setup wizard redirection check
    @app.before_request
    def check_first_run_setup():
        from flask import request, redirect, url_for
        from app.setup_manager import is_configured
        if not is_configured():
            if request.endpoint and not request.endpoint.startswith('setup.') and not request.endpoint.startswith('static'):
                return redirect(url_for('setup.index'))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.customers import customers_bp
    from app.routes.items import items_bp
    from app.routes.invoices import invoices_bp
    from app.routes.settings import settings_bp
    from app.routes.excel_ops import excel_bp
    from app.routes.users import users_bp
    from app.routes.audit import audit_bp
    from app.routes.reports import reports_bp
    from app.routes.setup import setup_bp
    from app.routes.ai_assistant import ai_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(excel_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(setup_bp)
    app.register_blueprint(ai_bp)

    with app.app_context():
        try:
            db.create_all()
            run_sqlite_schema_migrations()
            seed_initial_data()
        except Exception as e:
            print(f"Cold-start database init notice: {e}")

    # Vercel Serverless & Reverse Proxy compatibility middleware
    class VercelPathFixMiddleware:
        def __init__(self, wsgi_app):
            self.wsgi_app = wsgi_app

        def __call__(self, environ, start_response):
            if environ.get('HTTP_X_DEBUG') == '1':
                import json
                headers_to_show = {k: str(v) for k, v in environ.items() if not k.startswith('wsgi.')}
                body = json.dumps(headers_to_show, indent=2).encode('utf-8')
                start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(body)))])
                return [body]

            path = environ.get('PATH_INFO', '')
            if path in ('/api/index', '/api/index.py', '/api/index/', '/api/index.py/'):
                environ['PATH_INFO'] = '/'
            elif path.startswith('/api/index.py/'):
                environ['PATH_INFO'] = path[len('/api/index.py'):]
            elif path.startswith('/api/index/'):
                environ['PATH_INFO'] = path[len('/api/index'):]

            return self.wsgi_app(environ, start_response)

    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)

    @app.route('/api/index')
    @app.route('/api/index.py')
    @app.route('/api/index/')
    @app.route('/api/index.py/')
    def vercel_entrypoint_redirect():
        from flask import redirect, url_for
        return redirect(url_for('dashboard.index'))

    return app

def run_sqlite_schema_migrations():
    """Dynamically adds missing columns to existing SQLite tables if they do not exist."""
    try:
        inspector = inspect(db.engine)
        
        # 1. Check users table columns
        user_cols = [c['name'] for c in inspector.get_columns('users')]
        new_user_cols = {
            'can_manage_invoices': 'BOOLEAN DEFAULT 1',
            'can_submit_fbr': 'BOOLEAN DEFAULT 1',
            'can_manage_items': 'BOOLEAN DEFAULT 1',
            'can_manage_customers': 'BOOLEAN DEFAULT 1',
            'can_manage_users': 'BOOLEAN DEFAULT 0',
            'can_edit_settings': 'BOOLEAN DEFAULT 0',
            'can_export_data': 'BOOLEAN DEFAULT 1',
        }
        for col, col_def in new_user_cols.items():
            if col not in user_cols:
                with db.engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_def};"))
                    conn.commit()

        # 2. Check invoices table columns
        inv_cols = [c['name'] for c in inspector.get_columns('invoices')]
        new_inv_cols = {
            'original_fbr_invoice_number': "VARCHAR(100) DEFAULT ''",
            'original_invoice_id': "INTEGER REFERENCES invoices(id)",
            'reason_for_issuance': "VARCHAR(255) DEFAULT ''"
        }
        for col, col_def in new_inv_cols.items():
            if col not in inv_cols:
                with db.engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE invoices ADD COLUMN {col} {col_def};"))
                    conn.commit()

    except Exception as e:
        print(f"Migration notice: {e}")

def seed_initial_data():
    """Seeds default admin, manager, company profile, and sample catalog."""
    # 1. Admin User
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@fbr-invoice.pk',
            full_name='System Administrator',
            role='admin'
        )
        admin.set_password('admin123')
        admin.apply_role_preset('admin')
        db.session.add(admin)
    else:
        admin.role = 'admin'
        admin.apply_role_preset('admin')

    # 2. Sample Operator / Accountant User for testing
    operator = User.query.filter_by(username='operator').first()
    if not operator:
        operator = User(
            username='operator',
            email='operator@fbr-invoice.pk',
            full_name='Sales Operator / Cashier',
            role='operator'
        )
        operator.set_password('operator123')
        operator.apply_role_preset('operator')
        db.session.add(operator)

    # 3. Sample Auditor / Viewer User
    viewer = User.query.filter_by(username='auditor').first()
    if not viewer:
        viewer = User(
            username='auditor',
            email='auditor@taxfirm.pk',
            full_name='Tax Consultant / Auditor',
            role='viewer'
        )
        viewer.set_password('auditor123')
        viewer.apply_role_preset('viewer')
        db.session.add(viewer)

    # 4. Company Settings
    settings = CompanySetting.query.first()
    if not settings:
        settings = CompanySetting(
            company_name="Apex Technologies (Pvt) Limited",
            ntn="7291845-3",
            strn="3277876123456",
            business_address="Plot 45-B, Sector I-9/2, Industrial Estate",
            city="Islamabad",
            province="Islamabad",
            phone="+92 51 4433221",
            email="accounts@apextech.com.pk",
            pos_id="POS-001",
            branch_code="BR-ISB-01",
            fbr_environment="mock",
            fbr_api_url="https://staging-di.pral.com.pk/api/v1/di/postinvoicedata",
            default_tax_rate=18.0,
            default_further_tax_rate=4.0
        )
        db.session.add(settings)

    # 5. Sample Customers
    if Customer.query.count() == 0:
        c1 = Customer(
            name="Al-Rehman Enterprises",
            buyer_type="Registered",
            ntn="1428590-7",
            strn="1700142859011",
            address="Suit 304, Business Arcade, Gulberg III",
            city="Lahore",
            province="Punjab",
            phone="042-35789123",
            email="rehman.tax@alrehman.com"
        )
        c2 = Customer(
            name="Crescent Trading Corporation",
            buyer_type="Registered",
            ntn="2948172-1",
            strn="0201294817215",
            address="Plot 18, SITE Area, Phase 2",
            city="Karachi",
            province="Sindh",
            phone="021-32567890",
            email="procurement@crescent.pk"
        )
        c3 = Customer(
            name="Tariq & Sons General Mart",
            buyer_type="Unregistered",
            cnic="35202-7654321-9",
            address="Shop 12, Main Anarkali Bazaar",
            city="Lahore",
            province="Punjab",
            phone="0300-1234567"
        )
        db.session.add_all([c1, c2, c3])

    # 6. Sample Items
    if Item.query.count() == 0:
        items = [
            Item(item_code="ITM-101", name="Dell Latitude 5520 Core i7 Laptop", description="High performance business notebook computer", hs_code="8471.3010", uom="NOS", unit_price=225000.0, sales_tax_rate=18.0),
            Item(item_code="ITM-102", name="Cisco Catalyst 24-Port Gigabit Switch", description="Managed network switch rackmount", hs_code="8517.6270", uom="NOS", unit_price=95000.0, sales_tax_rate=18.0),
            Item(item_code="ITM-103", name="APC Smart-UPS 1500VA LCD 230V", description="Uninterruptible power supply battery backup", hs_code="8504.4010", uom="NOS", unit_price=120000.0, sales_tax_rate=18.0),
            Item(item_code="ITM-104", name="Cat6 UTP Solid Copper Cable 305M Drum", description="Structured networking cable drum", hs_code="8544.4990", uom="NOS", unit_price=28500.0, sales_tax_rate=18.0),
            Item(item_code="ITM-105", name="A4 Copier Paper 80 GSM (Box of 5 Reams)", description="Premium multipurpose office paper", hs_code="4802.5600", uom="PKT", unit_price=7800.0, sales_tax_rate=18.0)
        ]
        db.session.add_all(items)

    db.session.commit()
