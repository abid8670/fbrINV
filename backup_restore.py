import os
import sys
import shutil
import zipfile
from datetime import datetime

# UTF-8 console output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))

BASE_DIR = get_app_dir()
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')

def create_backup():
    """Creates a timestamped compressed backup of all databases and configuration."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'FBR_Data_Backup_{timestamp}.zip')

    with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add instance folder (contains SQLite DB and app_config.json)
        if os.path.exists(INSTANCE_DIR):
            for root, _, files in os.walk(INSTANCE_DIR):
                for f in files:
                    file_path = os.path.join(root, f)
                    arcname = os.path.relpath(file_path, BASE_DIR)
                    zipf.write(file_path, arcname)

        # Add uploads folder
        if os.path.exists(UPLOADS_DIR):
            for root, _, files in os.walk(UPLOADS_DIR):
                for f in files:
                    file_path = os.path.join(root, f)
                    arcname = os.path.relpath(file_path, BASE_DIR)
                    zipf.write(file_path, arcname)

    print("=================================================================")
    print(" [OK] BACKUP CREATED SUCCESSFULLY!")
    print(f" Backup Archive: {backup_file}")
    print(f" File Size:      {round(os.path.getsize(backup_file) / 1024, 2)} KB")
    print("=================================================================")
    return backup_file

def restore_backup(backup_file):
    """Restores database and configuration from a specified backup ZIP file."""
    if not os.path.exists(backup_file):
        print(f" [ERROR] Backup archive not found: {backup_file}")
        return False

    with zipfile.ZipFile(backup_file, 'r') as zipf:
        zipf.extractall(BASE_DIR)

    print("=================================================================")
    print(" [OK] RESTORE COMPLETED SUCCESSFULLY!")
    print(f" Restored from: {backup_file}")
    print(" Instance data & configs have been restored.")
    print("=================================================================")
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        if len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            print("Usage: python backup_restore.py --restore <path_to_zip>")
    else:
        create_backup()
