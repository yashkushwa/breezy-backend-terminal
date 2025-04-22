
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
            
    def read_output(self):
        max_read_bytes = 1024 * 20
        while self.running:
            ready_to_read, _, _ = select.select([self.fd], [], [], 0.1)
            if self.fd in ready_to_read:
                try:
                    output = os.read(self.fd, max_read_bytes).decode('utf-8', errors='replace')
                    socketio.emit('terminal-output', output, room=self.socket_id)
                except (OSError, IOError) as e:
                    self.stop()
                    break
                    
    def write_input(self, data):
        if not self.running:
            return
        try:
            os.write(self.fd, data.encode())
        except (OSError, IOError):
            self.stop()
            
    def resize(self, cols, rows):
        if not self.running:
            return
        try:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
        except (OSError, IOError):
            pass
            
    def stop(self):
        if not self.running:
            return
            
        self.running = False
        
        if self.pid:
            try:
                os.kill(self.pid, signal.SIGTERM)
                time.sleep(0.2)
                # Force kill if still running
                if os.waitpid(self.pid, os.WNOHANG)[0] == 0:
                    os.kill(self.pid, signal.SIGKILL)
            except (OSError, IOError):
                pass
                
        if self.fd:
            try:
                os.close(self.fd)
            except (OSError, IOError):
                pass
                
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
            
        self.fd = None
        self.pid = None
        self.thread = None

@app.route('/')
def index():
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

@socketio.on('disconnect')
def handle_disconnect():
    socket_id = request.sid
    if socket_id in terminals:
        terminals[socket_id].stop()
        del terminals[socket_id]
    print(f"Client disconnected: {socket_id}")

@socketio.on('terminal-input')
def handle_terminal_input(data):
    socket_id = request.sid
    if socket_id in terminals:
        # Add newline to command
        terminals[socket_id].write_input(data + '\n')

@socketio.on('resize')
def handle_resize(data):
    socket_id = request.sid
    if socket_id in terminals:
        terminals[socket_id].resize(data.get('cols', 80), data.get('rows', 24))

@socketio.on('ping')
def handle_ping():
    emit('pong')

if __name__ == '__main__':
    print("Starting terminal server on http://localhost:8080")
    print("Press Ctrl+C to stop the server")
    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)
