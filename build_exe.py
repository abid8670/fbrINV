import os
import sys
import shutil
import zipfile
import subprocess

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def build_standalone_exe():
    """Compiles the FBR Digital Invoicing application into a standalone Windows distribution."""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    templates_dir = os.path.join(base_dir, 'app', 'templates')
    static_dir = os.path.join(base_dir, 'app', 'static')
    icon_path = os.path.join(base_dir, 'fbr_icon.ico')

    # Ensure temp dir on D: drive because C: drive is low on disk space
    temp_dir = os.path.join(base_dir, '.tmp')
    build_dir = os.path.join(base_dir, 'build')
    dist_dir = os.path.join(base_dir, 'dist')
    os.makedirs(temp_dir, exist_ok=True)
    os.environ['TEMP'] = temp_dir
    os.environ['TMP'] = temp_dir

    print("==================================================================")
    print(" [*] Building FiscalSync DI Windows Standalone App (.EXE)")
    print("==================================================================")
    print(f" [*] Working Directory: {base_dir}")
    print(f" [*] Output Directory:  {dist_dir}")
    print(f" [*] Temp Directory:    {temp_dir} (redirected to D: drive)")
    print("==================================================================\n")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=FBR_Digital_Invoicing",
        "--noconfirm",
        "--clean",
        f"--workpath={build_dir}",
        f"--distpath={dist_dir}",
        f"--specpath={base_dir}",
        f"--add-data={templates_dir};app/templates",
        f"--add-data={static_dir};app/static",
        "--hidden-import=sqlite3",
        "--hidden-import=pymysql",
        "--hidden-import=psycopg2",
        "--hidden-import=psycopg",
        "--hidden-import=psycopg_binary",
        "--hidden-import=waitress",
        "--hidden-import=openpyxl",
        "--hidden-import=pandas",
        "--hidden-import=qrcode",
        "--hidden-import=PIL",
        "--hidden-import=jinja2",
        "--hidden-import=sqlalchemy",
        "--hidden-import=flask",
        "--hidden-import=flask_login",
        "--hidden-import=flask_sqlalchemy",
        "--hidden-import=werkzeug",
        "--hidden-import=requests",
        "--collect-all=app",
    ]

    if os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")

    cmd.append("run.py")

    print("Executing PyInstaller compiler...")
    result = subprocess.run(cmd, cwd=base_dir)

    if result.returncode == 0:
        target_dir = os.path.join(dist_dir, "FBR_Digital_Invoicing")
        
        # Ensure instance, uploads, and backups folders exist in output package
        os.makedirs(os.path.join(target_dir, "instance"), exist_ok=True)
        os.makedirs(os.path.join(target_dir, "uploads"), exist_ok=True)
        os.makedirs(os.path.join(target_dir, "backups"), exist_ok=True)

        # Copy existing database and config if present so it's ready out-of-the-box
        src_instance = os.path.join(base_dir, "instance")
        if os.path.exists(src_instance):
            for item in os.listdir(src_instance):
                s_item = os.path.join(src_instance, item)
                d_item = os.path.join(target_dir, "instance", item)
                if os.path.isfile(s_item) and not os.path.exists(d_item):
                    shutil.copy2(s_item, d_item)

        # Create quick-launcher batch script in the distribution folder
        launcher_bat = os.path.join(target_dir, "START_FBR_SYSTEM.bat")
        with open(launcher_bat, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("title FiscalSync DI - Enterprise FBR Invoicing\n")
            f.write("cd /d \"%~dp0\"\n")
            f.write("start \"\" \"FBR_Digital_Invoicing.exe\"\n")

        # Create README in distribution folder
        readme_txt = os.path.join(target_dir, "README_INSTRUCTIONS.txt")
        with open(readme_txt, "w", encoding="utf-8") as f:
            f.write("=================================================================\n")
            f.write(" 🇵🇰 FISCALSYNC DI • ENTERPRISE FBR INVOICING SUITE (STANDALONE)\n")
            f.write("=================================================================\n\n")
            f.write("HOW TO RUN:\n")
            f.write("1. Double click 'FBR_Digital_Invoicing.exe' (or START_FBR_SYSTEM.bat).\n")
            f.write("2. Your default web browser will automatically open:\n")
            f.write("   http://127.0.0.1:5000\n\n")
            f.write("DEFAULT LOGIN CREDENTIALS:\n")
            f.write("   Username: admin\n")
            f.write("   Password: admin123\n\n")
            f.write("LAN USAGE ACROSS MULTIPLE COUNTERS:\n")
            f.write("   Other computers on the same shop/office Wi-Fi or LAN can access\n")
            f.write("   the system using this PC's IP address (shown in the terminal window).\n\n")
            f.write("DATA BACKUP & SAFETY:\n")
            f.write("   All customer data, item catalogs, and FBR invoices are saved inside\n")
            f.write("   the 'instance' folder right here. You can copy this whole folder to a\n")
            f.write("   USB flash drive anytime to move or backup your data.\n")
            f.write("=================================================================\n")

        print("\n==================================================================")
        print(" ✅ BUILD COMPLETE!")
        print(f" Output Location: {target_dir}")
        print(f" Main Executable: {os.path.join(target_dir, 'FBR_Digital_Invoicing.exe')}")
        print("==================================================================")

        # Create ZIP distribution package
        zip_filename = os.path.join(dist_dir, "FBR_Digital_Invoicing_Windows_v1.12.zip")
        print(f"\nCompressing into portable distribution ZIP: {zip_filename} ...")
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(target_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, dist_dir)
                    zipf.write(full_p, rel_p)
        print(f" ✅ ZIP Package Created! File size: {round(os.path.getsize(zip_filename) / (1024*1024), 2)} MB")
        print("==================================================================")
        return True
    else:
        print(f"\n❌ Build failed with error code {result.returncode}")
        return False

if __name__ == '__main__':
    build_standalone_exe()
