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
    print("\033[91mERROR: 'dist' directory not found!\033[0m")
    print("\033[93mThe frontend needs to be pre-built for this application to work.\033[0m")
    
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
            try:
                timeout_sec = 0.1
                (data_ready, _, _) = select.select([self.fd], [], [], timeout_sec)
                if data_ready:
                    output = os.read(self.fd, max_read_bytes).decode()
                    socketio.emit('terminal-output', {'output': output}, room=self.socket_id)
            except OSError as e:
                if e.errno == termios.EIO:
                    # Handle EIO error (terminal closed)
                    self.stop()
                    break
                else:
                    print(f"Unhandled OSError: {e}")
                    self.stop()
                    break
            except Exception as e:
                print(f"Unhandled exception in read_output: {e}")
                self.stop()
                break

    def write_input(self, data):
        if self.running and self.fd:
            try:
                os.write(self.fd, data.encode())
            except OSError as e:
                if e.errno == termios.EIO:
                    # Handle EIO error (terminal closed)
                    self.stop()
                else:
                    print(f"Unhandled OSError: {e}")
                    self.stop()
            except Exception as e:
                print(f"Unhandled exception in write_input: {e}")
                self.stop()

    def resize(self, rows, cols):
        if self.running and self.fd:
            try:
                # Set the terminal size
                winsize = struct.pack("HH", rows, cols)
                fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
            except Exception as e:
                print(f"Error resizing terminal: {e}")

    def stop(self):
        if self.running:
            try:
                if self.fd:
                    os.close(self.fd)  # Close the file descriptor
                if self.pid:
                    os.kill(self.pid, signal.SIGTERM)  # Terminate the child process
            except OSError as e:
                print(f"Error stopping terminal (pid={self.pid}, fd={self.fd}): {e}")
            finally:
                self.running = False
                self.fd = None
                self.pid = None
                if self.socket_id in terminals:
                    del terminals[self.socket_id]
                print(f"Terminal stopped and removed: {self.socket_id}")

@app.route('/')
def index():
    if not os.path.exists('./dist/index.html'):
        return "<html><body style='font-family: sans-serif; padding: 20px; line-height: 1.6;'>" \
               "<h1 style='color: #e53e3e;'>Error: Frontend not built</h1>" \
               "<p>The web terminal frontend has not been pre-built. The frontend needs to be pre-built for this application to work.</p>" \
               "</body></html>"
    return app.send_static_file('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.errorhandler(404)
def not_found(e):
    # Make sure this doesn't try to modify the file
    if os.path.exists('./dist/index.html'):
        return app.send_static_file('index.html')
    else:
        return "<html><body style='font-family: sans-serif; padding: 20px;'><h1>404 Not Found</h1><p>The requested URL was not found.</p></body></html>", 404

@socketio.on('disconnect')
def handle_disconnect():
    socket_id = request.sid
    print(f"Client disconnected: {socket_id}")
    if socket_id in terminals:
        terminals[socket_id].stop()
        del terminals[socket_id]

@socketio.on('terminal-input')
def handle_terminal_input(data):
    socket_id = request.sid
    if socket_id in terminals:
        terminals[socket_id].write_input(data)

@socketio.on('resize')
def handle_resize(data):
    socket_id = request.sid
    if socket_id in terminals:
        terminals[socket_id].resize(data['rows'], data['cols'])

@socketio.on('ping')
def handle_ping():
    # Respond to ping to keep the connection alive
    emit('pong')

if __name__ == '__main__':
    # Display clear instructions
    if not os.path.exists('./dist'):
        print("\n\033[91mERROR: Frontend not pre-built!\033[0m")
        print("\033[93mThe frontend needs to be pre-built for this application to work.\033[0m")
    else:
        print("\033[92mStarting terminal server on http://localhost:8080\033[0m")
        print("Press Ctrl+C to stop the server")
        socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)
