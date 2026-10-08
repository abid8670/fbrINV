import os
import sys
import json
from sqlalchemy import create_engine, text

def get_app_dir():
    """Returns directory where the application and its persistent data reside."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

INSTANCE_DIR = os.path.abspath(os.path.join(get_app_dir(), 'instance'))
CONFIG_FILE = os.path.join(INSTANCE_DIR, 'app_config.json')

def ensure_instance_dir():
    try:
        os.makedirs(INSTANCE_DIR, exist_ok=True)
    except OSError:
        pass

def is_configured():
    """Returns True if the system has completed the first-time setup or has existing users."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('is_configured', False)
        except Exception:
            pass
    try:
        from app.models import User
        if User.query.count() > 0:
            return True
    except Exception:
        pass
    return False

def get_config():
    """Reads saved configuration or returns sensible defaults."""
    ensure_instance_dir()
    sqlite_path = os.path.abspath(os.path.join(INSTANCE_DIR, 'fbr_invoicing.db'))
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('db_type') == 'sqlite':
                    data['sqlite_path'] = sqlite_path
                    data['sqlalchemy_uri'] = f"sqlite:///{sqlite_path}"
                return data
        except Exception:
            pass
    # Default fallback config
    return {
        "is_configured": False,
        "db_type": "sqlite",
        "sqlite_path": sqlite_path,
        "sqlalchemy_uri": f"sqlite:///{sqlite_path}",
        "mysql": {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "fbr_invoicing"
        },
        "postgresql": {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "",
            "database": "fbr_invoicing"
        },
        "ai_voice": {
            "enabled": True,
            "language": "en-US", # "en-US" or "ur-PK"
            "speech_rate": 1.0,
            "api_provider": "browser", # "browser", "google_tts", "openai"
            "api_key": ""
        }
    }

def save_config(cfg_dict):
    """Saves updated configuration to instance/app_config.json."""
    try:
        ensure_instance_dir()
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg_dict, f, indent=4)
    except OSError:
        pass

def build_sqlalchemy_uri(db_type, params=None):
    """Constructs SQLAlchemy Database URI for SQLite, MySQL, or PostgreSQL."""
    ensure_instance_dir()
    if db_type == 'mysql':
        p = params or {}
        user = p.get('user', 'root')
        pwd = p.get('password', '')
        host = p.get('host', 'localhost')
        port = p.get('port', 3306)
        db = p.get('database', 'fbr_invoicing')
        # Using PyMySQL driver
        return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?charset=utf8mb4"
    elif db_type == 'postgresql':
        p = params or {}
        user = p.get('user', 'postgres')
        pwd = p.get('password', '')
        host = p.get('host', 'localhost')
        port = p.get('port', 5432)
        db = p.get('database', 'fbr_invoicing')
        # Using psycopg2 driver
        return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
    else:
        # Default SQLite
        sqlite_file = os.path.abspath(os.path.join(INSTANCE_DIR, 'fbr_invoicing.db'))
        return f"sqlite:///{sqlite_file}"

def test_db_connection(db_type, params=None):
    """Tests if database connection can be established before saving."""
    try:
        uri = build_sqlalchemy_uri(db_type, params)
        engine = create_engine(uri, connect_args={"connect_timeout": 5} if db_type != 'sqlite' else {})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        return {"success": True, "message": f"Connection successful to {db_type.upper()}!"}
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}

def reconfigure_sqlalchemy_engine(app, new_uri):
    """Safely updates the active SQLAlchemy engine on the running app without re-calling init_app."""
    from app.models import db
    app.config['SQLALCHEMY_DATABASE_URI'] = new_uri
    engines = db._app_engines.setdefault(app, {})
    if engines:
        for eng in list(engines.values()):
            try:
                eng.dispose()
            except Exception:
                pass
        engines.clear()

    options = db._engine_options.copy()
    options.update(app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}))
    options["url"] = new_uri
    db._apply_driver_defaults(options, app)
    engines[None] = db._make_engine(None, options, app)
    return engines[None]
