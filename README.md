
# Web Terminal

A web-based terminal emulator built with Python Flask backend and xterm.js frontend.

## Features

- Real terminal emulation in the browser
- Supports all common terminal commands
- Beautiful modern UI with a dark theme
- Responsive design that works on mobile and desktop

## Installation

1. Install the Python requirements:

```bash
pip install -r requirements.txt
```

2. Build the frontend (for production):

```bash
npm run build
```

## Running the Terminal

Simply run the Python server:

```bash
python server.py
```

Then open your browser to [http://localhost:8080](http://localhost:8080)

## Development

For development, you can run:

```bash
# Terminal backend
python server.py

# Frontend development server (in another terminal)
npm run dev
```

## Technologies Used

- Backend: Python Flask, flask-socketio
- Frontend: React, xterm.js, Tailwind CSS
- Communication: WebSockets via Socket.IO

## Security Note

This terminal provides direct access to your system through a shell. Only use it in trusted environments and never expose it to the public internet without proper authentication and security measures.
