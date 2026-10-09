import os
import sys
import socket
from waitress import serve
from app import create_app

# Ensure UTF-8 console output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    lan_ip = get_lan_ip()
    threads = int(os.environ.get('THREADS', 16))

    print("=========================================================================")
    print(" 🚀 FISCALSYNC DI • PRODUCTION WSGI SERVER (WAITRESS)")
    print("=========================================================================")
    print(f" [*] Local Machine Access:      http://127.0.0.1:{port}")
    print(f" [*] LAN Office / Shop Access:   http://{lan_ip}:{port}")
    print(f" [*] First-Time Setup Wizard:   http://{lan_ip}:{port}/setup")
    print(f" [*] Concurrency:              {threads} Multi-Threaded Workers Active")
    print(" [*] Server Status:             Ready to handle live cashier billing 24/7")
    print("=========================================================================")
    print(" Press Ctrl+C to stop the server.\n")

    serve(app, host='0.0.0.0', port=port, threads=threads)
