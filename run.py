import os
import sys
import threading
import time
import webbrowser

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import create_app

app = create_app()

def open_browser_tab(port):
    """Automatically opens the default browser after server starts."""
    time.sleep(1.2)
    try:
        webbrowser.open(f"http://127.0.0.1:{port}")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

import socket

def get_lan_ip():
    """Detects local LAN IP address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    auto_open = os.environ.get('AUTO_OPEN_BROWSER', '1') == '1'
    lan_ip = get_lan_ip()

    print("=================================================================")
    print(" 🇵🇰 FISCALSYNC DI • ENTERPRISE FBR INVOICING SUITE (SRO 350(I)/2024)")
    print("=================================================================")
    print(f" [*] Local Web Interface: http://127.0.0.1:{port}")
    if lan_ip != "127.0.0.1":
        print(f" [*] LAN Office / Counter: http://{lan_ip}:{port}")
    print(f" [*] Setup Wizard:        http://127.0.0.1:{port}/setup")
    print(f" [*] Default Admin Login: Username: admin | Password: admin123")
    print("=================================================================")
    print(" Starting high-performance multi-threaded server...\n")

    if auto_open:
        threading.Thread(target=open_browser_tab, args=(port,), daemon=True).start()

    try:
        from waitress import serve
        serve(app, host='0.0.0.0', port=port, threads=8)
    except Exception:
        app.run(host='0.0.0.0', port=port, debug=False)

