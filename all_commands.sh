#!/bin/bash

# Activate virtual environment
source /opt/venv/bin/activate

# Ensure /app/logs directory exists
mkdir -p /app/logs

# Function to handle process termination
function terminate_processes {
    echo "Terminating processes..."
    pkill -f "python3 manage.py"
    pkill -f "daphne"
    exit
}

# Trap SIGTERM signal to gracefully terminate processes
trap terminate_processes SIGTERM

## Run the delete_mqtt command
#echo "Running delete_mqtt cleanup..."
#python3 manage.py delete_mqtt &> /app/logs/delete_mqtt.log
#if [ $? -ne 0 ]; then
#    echo "Error running delete_mqtt command"
#    exit 1
#fi

# Run the delete_mqtt command in background
echo "Running delete_mqtt cleanup..."
python3 manage.py delete_mqtt &> /app/logs/delete_mqtt.log &

# Run MQTT subscriber
echo "Starting MQTT subscriber..."
python3 manage.py run_mqtt &> /app/logs/mqtt.log &

# Start Django server
echo "Starting Django server..."
python3 manage.py runserver 0.0.0.0:8000 &> /app/logs/django_server.log &

# Keep container running
wait











