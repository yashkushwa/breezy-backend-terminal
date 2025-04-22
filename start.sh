
#!/bin/bash

echo "Starting Web Terminal..."
echo "-------------------------"

# Check if the dist directory exists
if [ ! -d "./dist" ]; then
    echo "ERROR: 'dist' directory not found!"
    echo "The frontend needs to be pre-built for this application to work."
    exit 1
fi

echo "-------------------------"
echo "Starting Flask terminal server..."
python server.py
