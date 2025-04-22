
#!/bin/bash

echo "Starting Web Terminal..."
echo "-------------------------"

# Check if the dist directory exists
if [ ! -d "./dist" ]; then
    echo "ERROR: 'dist' directory not found!"
    echo "The frontend needs to be pre-built for this application to work."
    echo ""
    echo "To build the frontend, run:"
    echo "npm install && npm run build"
    echo ""
    echo "Or manually create the dist directory with the built files."
    echo "-------------------------"
    
    # Ask if user wants to continue anyway
    read -p "Do you want to continue starting the server anyway? (y/n): " response
    if [[ "$response" != "y" && "$response" != "Y" ]]; then
        echo "Aborted. Please build the frontend first."
        exit 1
    fi
fi

echo "-------------------------"
echo "Starting Flask terminal server..."
python server.py
