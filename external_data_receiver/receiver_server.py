import os
import json
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Configuration
OUTPUT_FILE = 'received_game_data.json'
RECEIVER_PORT = 9000 # Choose a port not used by agents (e.g., 9000)

@app.route('/submit_game_data', methods=['POST', 'GET'])
def submit_game_data():
    if request.method == 'GET':
        print("!!! Received GET request instead of POST !!!")
        # Return a custom message or even the 404, but the print statement is key
        return jsonify({"success": False, "error": "Expected POST, received GET"}), 405 # 405 is Method Not Allowed

    """Receives data via POST and saves it to a JSON file."""
    # Check if the request content type is JSON
    if not request.is_json:
        print("Received non-JSON request")
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    # Get the JSON data
    data = request.get_json()
    print(f"Received data: {json.dumps(data)}") # Log received data

    # Add a timestamp to the received data
    data['_received_timestamp'] = datetime.now().isoformat()

    # Save the data to the file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Data successfully saved to {OUTPUT_FILE}")
        # Send success response back to Lens Studio
        return jsonify({"success": True, "message": "Data received and saved."}), 200
    except IOError as e:
        print(f"Error saving data to {OUTPUT_FILE}: {e}")
        return jsonify({"success": False, "error": f"Failed to save data: {e}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"success": False, "error": f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
    # --- IMPORTANT: Replace <YOUR_ACTUAL_LOCAL_IP> with your computer's real local network IP address --- 
    local_ip_address = "10.200.0.58" 
    # ---------------------------------------------------------------------------------------------
    # Correctly check if the placeholder hasn't been replaced
    if local_ip_address == "<YOUR_ACTUAL_LOCAL_IP>":
        print("\n*** ERROR: Please edit receiver_server.py and replace '<YOUR_ACTUAL_LOCAL_IP>' with your actual local IP address! ***\n")
        exit(1)

    print(f"Starting receiver server on http://{local_ip_address}:{RECEIVER_PORT}...")
    print(f"Listening for POST requests on /submit_game_data")
    print(f"Data will be saved to {os.path.abspath(OUTPUT_FILE)}")
    # Listen explicitly on the local network IP
    app.run(host=local_ip_address, port=RECEIVER_PORT, debug=False) # Turn off debug for production/testing 