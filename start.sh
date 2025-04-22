
#!/bin/bash

echo "Starting Web Terminal..."
echo "-------------------------"
echo "Building frontend..."
npm run build

echo "-------------------------"
echo "Starting Flask terminal server..."
python server.py
