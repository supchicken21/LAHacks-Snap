#!/bin/bash

# --- START CLEANUP ---
echo "Performing cleanup..."

# Stop agents from previous run based on PID file
OLD_PID_FILE="agent_pids.txt"
if [ -f "$OLD_PID_FILE" ]; then
    echo "Stopping processes from $OLD_PID_FILE..."
    kill $(cat "$OLD_PID_FILE") 2>/dev/null || true # Ignore errors if file empty or processes gone
    rm -f "$OLD_PID_FILE" # Remove old PID file
fi

# Force kill specific ports known to cause issues
PORTS_TO_KILL=(8000 8001 8002 8003 8004 8005 8006 8007 8008)
for port in "${PORTS_TO_KILL[@]}"; do
    echo "Checking for process on port $port..."
    pid=$(lsof -ti :$port)
    if [ -n "$pid" ]; then
        echo "Killing process $pid on port $port..."
        kill -9 "$pid" 2>/dev/null || true
    else
        echo "Port $port seems clear."
    fi
done

echo "Waiting a second for ports to free up..."
sleep 1
echo "Cleanup complete."
# --- END CLEANUP ---


# Ensure the virtual environment is active or use its Python directly
PYTHON_EXEC=".venv/bin/python"
if [ ! -f "$PYTHON_EXEC" ]; then
    echo "Error: Virtual environment Python not found at $PYTHON_EXEC"
    echo "Please ensure the .venv directory exists and contains the Python interpreter."
    exit 1
fi

# Create logs directory if it doesn't exist
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# File to store PIDs for the new run
PID_FILE="agent_pids.txt"
> "$PID_FILE" # Clear/create PID file

echo "Starting agents..."

# Find and run only necessary python files
NECESSARY_AGENTS=(
    "main_orchestrator_agent.py"
    "medical_profile_agent.py"
    "background_analyzer_agent.py"
    "game_data_agent.py"

)

for agent_script in "${NECESSARY_AGENTS[@]}"; do
    if [ -f "$agent_script" ]; then
        # Construct log file path
        log_file="$LOG_DIR/${agent_script%.py}.log"
        echo "Starting $agent_script, logging to $log_file"
        # Run the agent script in the background using the venv Python
        # Redirect stdout and stderr to the log file
        "$PYTHON_EXEC" "$agent_script" > "$log_file" 2>&1 &
        # Save the PID
        pid=$!
        echo $pid >> "$PID_FILE"
        echo "  PID: $pid"
    else
        echo "Warning: Necessary agent script not found: $agent_script"
    fi
done

echo "All agents started in the background."
echo "Check individual log files in the '$LOG_DIR' directory for output/errors."
echo "PIDs saved to $PID_FILE"
echo "To stop all agents, run: kill \$(cat $PID_FILE)" 