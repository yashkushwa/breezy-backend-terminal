import { useEffect, useRef, useState } from "react";
import { Terminal } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import axios from "axios";
import io from "socket.io-client";
import "xterm/css/xterm.css";

const Index = () => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const terminalInstance = useRef<Terminal | null>(null);
  const socketRef = useRef<any>(null);

  useEffect(() => {
    // Initialize terminal
    if (!terminalRef.current) return;
    
    const term = new Terminal({
      cursorBlink: true,
      theme: {
        background: '#1E1E2E',
        foreground: '#CDD6F4',
        cursor: '#F5E0DC',
        selectionBackground: '#45475A',
        black: '#45475A',
        red: '#F38BA8',
        green: '#A6E3A1',
        yellow: '#F9E2AF',
        blue: '#89B4FA',
        magenta: '#F5C2E7',
        cyan: '#94E2D5',
        white: '#BAC2DE',
        brightBlack: '#585B70',
        brightRed: '#F38BA8',
        brightGreen: '#A6E3A1',
        brightYellow: '#F9E2AF',
        brightBlue: '#89B4FA',
        brightMagenta: '#F5C2E7',
        brightCyan: '#94E2D5',
        brightWhite: '#A6ADC8',
      },
      fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
      fontSize: 14,
      lineHeight: 1.2,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    
    term.open(terminalRef.current);
    fitAddon.fit();
    terminalInstance.current = term;

    // Connect to the Flask backend with Socket.IO
    const socket = io('http://localhost:8080', {
      transports: ['websocket'],
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      term.writeln('\r\n\x1b[32mConnected to terminal server\x1b[0m');
      term.writeln('');
      term.write('$ ');
    });

    socket.on('connect_error', (err) => {
      console.error('Connection error:', err);
      term.writeln('\r\n\x1b[31mConnection error: ' + err.message + '\x1b[0m');
    });

    socket.on('terminal-output', (data) => {
      term.write(data);
    });

    // Handle user input
    let commandBuffer = '';
    term.onData((data) => {
      if (data === '\r') { // Enter key
        term.writeln('');
        socket.emit('terminal-input', commandBuffer);
        commandBuffer = '';
      } else if (data === '\u007F') { // Backspace
        if (commandBuffer.length > 0) {
          commandBuffer = commandBuffer.slice(0, -1);
          term.write('\b \b'); // Erase the character from terminal
        }
      } else {
        commandBuffer += data;
        term.write(data);
      }
    });

    // Handle window resize
    const handleResize = () => {
      fitAddon.fit();
      socket.emit('resize', { cols: term.cols, rows: term.rows });
    };

    window.addEventListener('resize', handleResize);
    
    // Ping to keep connection alive
    const pingInterval = setInterval(() => {
      if (socket.connected) {
        socket.emit('ping');
      }
    }, 30000);

    // Cleanup on unmount
    return () => {
      window.removeEventListener('resize', handleResize);
      clearInterval(pingInterval);
      socket.disconnect();
      term.dispose();
    };
  }, []);

  // Check server status
  useEffect(() => {
    const checkServer = async () => {
      try {
        await axios.get('http://localhost:8080/health');
      } catch (error) {
        console.error('Terminal server is not running:', error);
        if (terminalInstance.current) {
          terminalInstance.current.writeln('\r\n\x1b[31mERROR: Terminal server is not running!\x1b[0m');
          terminalInstance.current.writeln('Please start the Python Flask server with:');
          terminalInstance.current.writeln('\x1b[33mpython server.py\x1b[0m');
        }
      }
    };
    
    checkServer();
  }, []);

  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if socket connects within a timeout period
    const connectionTimeout = setTimeout(() => {
      if (!isConnected) {
        setIsLoading(false);
      }
    }, 3000);

    return () => clearTimeout(connectionTimeout);
  }, [isConnected]);

  // Update connected state when socket connects
  useEffect(() => {
    if (socketRef.current) {
      socketRef.current.on('connect', () => {
        setIsConnected(true);
        setIsLoading(false);
      });
      
      socketRef.current.on('disconnect', () => {
        setIsConnected(false);
      });
    }
  }, [socketRef.current]);

  return (
    <div className="min-h-screen bg-[#1E1E2E] flex flex-col">
      <header className="bg-[#181825] text-[#CDD6F4] p-3 shadow-md">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-mono">Web Terminal</h1>
          <div className="flex items-center space-x-3">
            <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-[#A6E3A1]' : 'bg-[#F38BA8]'}`}></div>
            <div className="flex space-x-2">
              <div className="h-3 w-3 rounded-full bg-[#F38BA8]"></div>
              <div className="h-3 w-3 rounded-full bg-[#F9E2AF]"></div>
              <div className="h-3 w-3 rounded-full bg-[#A6E3A1]"></div>
            </div>
          </div>
        </div>
      </header>
      
      <div className="flex-1 p-2 overflow-hidden">
        {isLoading ? (
          <div className="h-full w-full flex flex-col items-center justify-center text-[#CDD6F4]">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#89B4FA] mb-4"></div>
            <p className="text-lg font-mono">Connecting to terminal...</p>
          </div>
        ) : !isConnected ? (
          <div className="h-full w-full flex flex-col items-center justify-center text-[#CDD6F4] p-4">
            <div className="bg-[#F38BA8]/20 border border-[#F38BA8] p-4 rounded-md max-w-md">
              <h2 className="text-[#F38BA8] text-lg font-bold mb-2">Terminal Server Not Running</h2>
              <p className="mb-4">The Flask terminal server is not running. Please start it with the following command:</p>
              <div className="bg-[#11111B] p-3 rounded-md font-mono text-sm mb-4 overflow-x-auto">
                <code>python server.py</code>
              </div>
              <p className="text-sm">Once started, the terminal will connect automatically.</p>
            </div>
          </div>
        ) : (
          <div 
            ref={terminalRef} 
            className="h-full w-full rounded-md overflow-hidden border border-[#313244]"
          />
        )}
      </div>
      
      <footer className="bg-[#181825] text-[#6C7086] p-2 text-xs text-center">
        <p>Flask Terminal • Port 8080 • Press Ctrl+C to terminate running commands</p>
      </footer>
    </div>
  );
};

export default Index;
