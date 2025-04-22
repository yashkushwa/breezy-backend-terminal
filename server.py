
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import pty
import os
import subprocess
import select
import termios
import struct
import fcntl
import signal
import threading
import time

# Check if dist directory exists, if not display a useful error
if not os.path.exists('./dist'):
    print("\033[91mERROR: 'dist' directory not found! Make sure to build the frontend first.\033[0m")
    print("\033[93mTo build the frontend, you need Node.js and npm installed.\033[0m")
    print("\033[93mRun: 'npm install' and then 'npm run build'\033[0m")
    print("\033[93mOr use './start.sh' if Node.js is available in your environment.\033[0m")
    
app = Flask(__name__, static_folder='./dist', static_url_path='/')
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active terminals
terminals = {}

class Terminal:
    def __init__(self, socket_id):
        self.socket_id = socket_id
        self.fd = None
        self.pid = None
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
            
        # Create PTY
        self.pid, self.fd = pty.fork()
        
        if self.pid == 0:  # Child process
            # Execute shell
            env = os.environ.copy()
            env["TERM"] = "xterm-256color"
            os.execvpe('/bin/bash', ['/bin/bash'], env)
        else:  # Parent process
            self.running = True
            self.thread = threading.Thread(target=self.read_output)
            self.thread.daemon = True
            self.thread.start()
            
    # ... keep existing code (read_output, write_input, resize, stop methods)

@app.route('/')
def index():
    if not os.path.exists('./dist/index.html'):
        return "<html><body style='font-family: sans-serif; padding: 20px; line-height: 1.6;'>" \
               "<h1 style='color: #e53e3e;'>Error: Frontend not built</h1>" \
               "<p>The web terminal frontend has not been built. To use this terminal, you need to:</p>" \
               "<ol>" \
               "<li>Make sure Node.js and npm are installed</li>" \
               "<li>Run <code>npm install</code> to install dependencies</li>" \
               "<li>Run <code>npm run build</code> to build the frontend</li>" \
               "</ol>" \
               "<p>After building the frontend, restart this server.</p>" \
               "</body></html>"
    return app.send_static_file('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.errorhandler(404)
def not_found(e):
    return app.send_static_file('index.html')

@socketio.on('connect')
def handle_connect():
    socket_id = request.sid
    terminal = Terminal(socket_id)
    terminals[socket_id] = terminal
    terminal.start()
    print(f"Client connected: {socket_id}")

# ... keep existing code (handle_disconnect, handle_terminal_input, handle_resize, handle_ping)

if __name__ == '__main__':
    # Display clear instructions
    if not os.path.exists('./dist'):
        print("\n\033[91mERROR: Frontend not built!\033[0m")
        try:
            # Check if npm is available
            npm_check = subprocess.run(["which", "npm"], capture_output=True, text=True)
            if npm_check.returncode == 0:
                print("\033[93mAttempting to build the frontend...\033[0m")
                try:
                    subprocess.run(["npm", "run", "build"], check=True)
                    print("\033[92mFrontend built successfully!\033[0m")
                except subprocess.CalledProcessError:
                    print("\033[91mFailed to build frontend. Please run 'npm run build' manually.\033[0m")
            else:
                print("\033[91mNode.js/npm not found in your environment!\033[0m")
                print("\033[93mPlease install Node.js and npm, then run:\033[0m")
                print("\033[93m  npm install\033[0m")
                print("\033[93m  npm run build\033[0m")
                print("\033[93mOr build the frontend on a system with Node.js installed.\033[0m")
        except Exception as e:
            print(f"\033[91mError checking for npm: {str(e)}\033[0m")
            print("\033[93mPlease build the frontend manually with 'npm run build'\033[0m")
            
    if os.path.exists('./dist'):
        print("\033[92mStarting terminal server on http://localhost:8080\033[0m")
        print("Press Ctrl+C to stop the server")
        socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)
    else:
        print("\033[91mWarning: Starting server without frontend build.\033[0m")
        print("\033[93mThe terminal interface will not be available until you build the frontend.\033[0m")
        socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)
