#!/usr/bin/env python3
import os
import sys
import socket
import signal
import time
import shutil
import http.server
import socketserver
import subprocess
import requests
import argparse
from pathlib import Path

# === CONFIG ===
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SITE_DIR = SCRIPT_DIR / "DOCS"
CONFIG_FILE = SCRIPT_DIR / "CONFIG"

# === Quiet HTTP Handler ===
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

# === Helpers ===
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def setup_docs(site_dir: Path):
    site_dir.mkdir(exist_ok=True)
    index_file = site_dir / "index.html"
    if not index_file.exists():
        index_file.write_text("<h1>Hello World!</h1><p>Python HTTP server is running.</p>")

def read_token(config_file: Path):
    if not config_file.exists():
        config_file.write_text("# Add your NGROK_AUTHTOKEN below:\nNGROK_AUTHTOKEN=\n")
        print(f"Created empty config file at {config_file}. Please add your NGROK_AUTHTOKEN.")
        return None

    for line in config_file.read_text().splitlines():
        if line.strip().startswith("NGROK_AUTHTOKEN="):
            token = line.split("=", 1)[1].strip()
            return token or None
    return None

def start_ngrok(port, token):
    ngrok_cmd = shutil.which("ngrok") or shutil.which("/snap/bin/ngrok")
    if not ngrok_cmd:
        print("Ngrok not found.")
        return None, None

    if not token:
        print("NGROK_AUTHTOKEN missing in CONFIG.")
        return None, None

    config_dir = Path.home() / ".ngrok2"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "ngrok.yml"
    if not config_file.exists():
        config_file.write_text(f"authtoken: {token}\n")

    print("Starting ngrok tunnel...")
    ngrok_process = subprocess.Popen(
        [ngrok_cmd, "http", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    public_url = None
    for delay in [0.5, 1, 2, 3, 5]:
        try:
            info = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2).json()
            tunnels = info.get("tunnels", [])
            if tunnels:
                public_url = tunnels[0].get("public_url")
                break
        except requests.RequestException:
            time.sleep(delay)
    return ngrok_process, public_url

def serve_site(host, port, site_dir):
    os.chdir(site_dir)
    with socketserver.ThreadingTCPServer((host, port), QuietHandler) as httpd:
        print(f"Serving locally → http://127.0.0.1:{port}")
        print("Press Ctrl+C to stop.")
        httpd.serve_forever()

# === Main logic ===
def main():
    parser = argparse.ArgumentParser(description="VNGSS lightweight HTTP + ngrok server")
    parser.add_argument("--dir", type=str, default=str(DEFAULT_SITE_DIR), help="Directory to serve")
    parser.add_argument("--port", type=int, help="Port to use (default: auto)")
    parser.add_argument("--no-ngrok", action="store_true", help="Disable ngrok tunnel")
    args = parser.parse_args()

    site_dir = Path(args.dir)
    setup_docs(site_dir)
    port = args.port or find_free_port()
    token = read_token(CONFIG_FILE)
    host = "0.0.0.0"

    ngrok_process = None
    public_url = None

    def cleanup(signum=None, frame=None):
        if ngrok_process and ngrok_process.poll() is None:
            ngrok_process.terminate()
            print("Ngrok tunnel terminated.")
        print("Server stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    if not args.no_ngrok:
        ngrok_process, public_url = start_ngrok(port, token)
        if public_url:
            print(f"Ngrok URL → {public_url}")
        else:
            print("Ngrok tunnel failed, continuing in local mode.")

    print("\n=== VNGSS SERVER ===")
    print(f"Serving: {site_dir}")
    print(f"Port: {port}")
    print(f"Ngrok: {'Enabled' if public_url else 'Disabled'}")
    print("====================\n")

    try:
        serve_site(host, port, site_dir)
    finally:
        cleanup()

if __name__ == "__main__":
    main()
