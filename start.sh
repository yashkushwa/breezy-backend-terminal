
#!/bin/bash

echo "Starting Web Terminal..."
echo "-------------------------"

# Check if npm is available
if command -v npm &> /dev/null; then
    echo "Building frontend..."
    npm run build
    
    if [ $? -ne 0 ]; then
        echo "-------------------------"
        echo "ERROR: Frontend build failed!"
        echo "You can still start the server, but the web interface will show an error message."
        read -p "Continue anyway? (y/n): " choice
        if [[ "$choice" != "y" && "$choice" != "Y" ]]; then
            echo "Exiting."
            exit 1
        fi
    fi
else
    echo "WARNING: npm not found. Cannot build frontend."
    echo "If you haven't built the frontend yet, the terminal will not work correctly."
    read -p "Continue anyway? (y/n): " choice
    if [[ "$choice" != "y" && "$choice" != "Y" ]]; then
        echo "Exiting."
        exit 1
    fi
fi

echo "-------------------------"
echo "Starting Flask terminal server..."
python server.py
