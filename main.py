import pynanovna
import threading
import requests
from signal_processing import SignalProcessing
from flask import Flask, render_template, jsonify, request
from bt_car_control import BTSender
import time
import asyncio

DATA_FILE = False#"../save_plate.csv"
CALIBRATION_FILE = "../cal0514.cal"
VERBOSE = False
PROCESS_SLEEP_TIME = 0.0001
CAR_DEVICE_NAME = "BT05-BLE"  # Replace with your car's Bluetooth device name

# Flask application setup
app = Flask(__name__)

latest_data = {"angle": 1, "throttle": 1}  # Initialize with default values
received_data = {}  # Dictionary to store received data

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    return jsonify(latest_data)

@app.route("/update_data", methods=["POST"])
def update_data():
    global latest_data
    data = request.get_json()
    latest_data = data
    return jsonify({"status": "success"})

@app.route("/receive_data", methods=["POST"])
def receive_data():
    global received_data
    data = request.get_json()
    received_data = data
    print("Received data from web:", received_data)
    return jsonify({"status": "success", "data": received_data})

def run_flask():
    app.run(debug=False, use_reloader=False)

# NanoVNA Setup
data_source = pynanovna.NanoVNAWorker(verbose=VERBOSE)
data_source.calibrate(load_file=CALIBRATION_FILE)  # This needs to be done through a terminal atm.
data_source.set_sweep(2.9e9, 3.1e9, 1, 101)
data_stream = data_source.stream_data(DATA_FILE)

signal_processing = SignalProcessing(
    data_stream,
    process_sleep_time=PROCESS_SLEEP_TIME,
    verbose=VERBOSE,
)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Instantiate the BTSender class
bt_sender = BTSender(device_name=CAR_DEVICE_NAME)

async def main_loop():
    await bt_sender.connect()
    data_processor = signal_processing.process_data_continuously()
    
    for angle, throttle in data_processor:
        send_data = {'angle': angle, 'throttle': throttle}
        latest_data = send_data.copy()
        try:
            response = requests.post("http://127.0.0.1:5000/update_data", json=send_data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending data to server: {e}")
        
        # Send the data to the RC car
        if not bt_sender.is_connected():
            print("Car not connected!")
            print("Trying to connect car...")
            await bt_sender.connect()
            time.sleep(5)
            
        await bt_sender.update_speed(angle, throttle)
        
        print("Still in loop", received_data)
        time.sleep(1)

# Run the main loop
asyncio.run(main_loop())
