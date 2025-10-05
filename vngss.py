#!/usr/bin/env python3
import os
import http.server
import socketserver
import socket
import subprocess
import sys
import time
import shutil
import requests

# --- Step 0: determine script folder ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- CONFIG ---
SITE_DIR = os.path.join(SCRIPT_DIR, "DOCS")  # All site files go here
CONFIG_FILE = os.path.join(SCRIPT_DIR, "CONFIG")

# --- Step 1: ensure DOCS folder exists ---
os.makedirs(SITE_DIR, exist_ok=True)

# --- Step 2: create default index.html if missing ---
index_file = os.path.join(SITE_DIR, "index.html")
if not os.path.exists(index_file):
    with open(index_file, "w") as f:
        f.write("<h1>Hello World!</h1><p>This site is running via Python HTTP server!</p>")

# --- Step 3: read ngrok token from CONFIG ---
NGROK_AUTHTOKEN = None
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("NGROK_AUTHTOKEN="):
                NGROK_AUTHTOKEN = line.split("=", 1)[1].strip()
else:
    # create empty config
    with open(CONFIG_FILE, "w") as f:
        f.write("# Add your NGROK_AUTHTOKEN below:\n")
        f.write("NGROK_AUTHTOKEN=\n")
    print(f"Created empty config file at {CONFIG_FILE}. Please add your NGROK_AUTHTOKEN before using ngrok.")

# --- Step 4: find a free port ---
def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

WEB_PORT = find_free_port()

# --- Step 5: check ngrok ---
NGROK_AVAILABLE = shutil.which("ngrok") is not None
if NGROK_AUTHTOKEN and NGROK_AVAILABLE:
    # preconfigure ngrok
    NGROK_CONFIG_DIR = os.path.expanduser("~/.ngrok2")
    NGROK_CONFIG_FILE = os.path.join(NGROK_CONFIG_DIR, "ngrok.yml")
    os.makedirs(NGROK_CONFIG_DIR, exist_ok=True)
    if not os.path.exists(NGROK_CONFIG_FILE):
        with open(NGROK_CONFIG_FILE, "w") as f:
            f.write(f"authtoken: {NGROK_AUTHTOKEN}\n")
        print("Ngrok config created with provided authtoken.")

    # start ngrok tunnel
    print("Starting ngrok tunnel...")
    ngrok_process = subprocess.Popen(
        ["ngrok", "http", str(WEB_PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # wait for ngrok to initialize
    public_url = None
    for _ in range(20):
        try:
            tunnel_info = requests.get("http://127.0.0.1:4040/api/tunnels").json()
            if tunnel_info['tunnels']:
                public_url = tunnel_info['tunnels'][0]['public_url']
                break
        except Exception:
            pass
        time.sleep(0.5)

    if public_url:
        print(f"Your site is publicly accessible via ngrok at: {public_url}")
    else:
        print("Could not retrieve ngrok URL. Make sure ngrok is running and try again.")
else:
    if not NGROK_AUTHTOKEN:
        print("NGROK_AUTHTOKEN not set in CONFIG. Ngrok tunnel will not start.")
    elif not NGROK_AVAILABLE:
        print("Ngrok executable not found. Please install ngrok to use public tunnels.")

# --- Step 6: start Python HTTP server ---
os.chdir(SITE_DIR)
Handler = http.server.SimpleHTTPRequestHandler
HOST = "0.0.0.0"

try:
    with socketserver.TCPServer((HOST, WEB_PORT), Handler) as httpd:
        print(f"Serving local site at http://127.0.0.1:{WEB_PORT}")
        print("Press Ctrl+C to stop the server.")
        httpd.serve_forever()
except OSError as e:
    print(f"Error starting server: {e}")
finally:
    if 'ngrok_process' in locals():
        ngrok_process.terminate()
        print("Ngrok tunnel terminated.")
    print("Server stopped.")
