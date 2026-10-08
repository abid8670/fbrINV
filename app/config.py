import os
import sys
from dotenv import load_dotenv
from app.setup_manager import get_config, get_app_dir

load_dotenv()

BASE_DIR = get_app_dir()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fbr-digital-invoicing-secret-key-2026-safe-default')
    
    # Read dynamic database URI configured by user or environment variable
    _cfg = get_config()
    is_serverless = bool(os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
    default_sqlite = "sqlite:////tmp/fbr_invoicing.db" if is_serverless else f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'fbr_invoicing.db')}"
    raw_db_url = os.environ.get('DATABASE_URL')
    if raw_db_url and raw_db_url.startswith('postgres://'):
        raw_db_url = raw_db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = raw_db_url or _cfg.get('sqlalchemy_uri', default_sqlite)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = '/tmp/uploads' if is_serverless else os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload


