import os
import sys
from dotenv import load_dotenv
from app.setup_manager import get_config, get_app_dir

load_dotenv()

BASE_DIR = get_app_dir()

def normalize_database_uri(url: str) -> str:
    """
    Normalizes PostgreSQL and MySQL database URIs for SQLAlchemy compatibility.
    Handles 'postgres://' -> 'postgresql://' as well as dynamic driver selection
    between psycopg (v3) and psycopg2 (v2) based on installed modules.
    """
    if not url:
        return url
        
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    has_psycopg = False
    try:
        import psycopg  # noqa: F401
        has_psycopg = True
    except ImportError:
        pass

    has_psycopg2 = False
    try:
        import psycopg2  # noqa: F401
        has_psycopg2 = True
    except ImportError:
        pass

    # If URI requests psycopg (v3) but only psycopg2 is available:
    if url.startswith('postgresql+psycopg://') and not has_psycopg and has_psycopg2:
        url = url.replace('postgresql+psycopg://', 'postgresql+psycopg2://', 1)
    # If URI requests psycopg2 but only psycopg (v3) is available:
    elif url.startswith('postgresql+psycopg2://') and not has_psycopg2 and has_psycopg:
        url = url.replace('postgresql+psycopg2://', 'postgresql+psycopg://', 1)
    # If standard postgresql:// is provided, SQLAlchemy defaults to psycopg2.
    # If psycopg2 is missing but psycopg (v3) is available, route to postgresql+psycopg://
    elif url.startswith('postgresql://') and not has_psycopg2 and has_psycopg:
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)

    return url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fbr-digital-invoicing-secret-key-2026-safe-default')
    
    # Neon remote PostgreSQL cloud database (used as seamless fallback on serverless if env var is missing)
    NEON_CLOUD_DB = "postgresql://FBR_owner:npg_QaPSb6HCkx5f@ep-muddy-brook-b48oeoyd-pooler.c-6.us-east-2.aws.neon.tech/FBR?sslmode=require&channel_binding=require"
    
    _cfg = get_config()
    is_serverless = bool(os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
    default_sqlite = "sqlite:////tmp/fbr_invoicing.db" if is_serverless else f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'fbr_invoicing.db')}"
    raw_db_url = os.environ.get('DATABASE_URL')
    
    if raw_db_url:
        SQLALCHEMY_DATABASE_URI = normalize_database_uri(raw_db_url)
    elif is_serverless:
        # On Vercel serverless, disk is read-only so always use Neon cloud PostgreSQL
        SQLALCHEMY_DATABASE_URI = normalize_database_uri(NEON_CLOUD_DB)
    else:
        configured_uri = _cfg.get('sqlalchemy_uri')
        SQLALCHEMY_DATABASE_URI = normalize_database_uri(configured_uri) if configured_uri else default_sqlite
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    UPLOAD_FOLDER = '/tmp/uploads' if is_serverless else os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload


