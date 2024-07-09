import pynanovna
import threading
import requests
from signal_processing import SignalProcessing
from flask import Flask, render_template, jsonify, request
from bt_car_control import BTSender
import time
import asyncio
from flask_socketio import SocketIO, emit
import subprocess

DATA_FILE = "../save_plate.csv"
CALIBRATION_FILE = "../cal0514.cal"
VERBOSE = True
PROCESS_SLEEP_TIME = 0.0001
CAR_DEVICE_NAME = "BT05-BLE"  # Replace with your car's Bluetooth device name

# Flask application setup
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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
    return jsonify({"status": "success", "data": received_data})

def run_flask():
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False)


# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# NanoVNA Setup
data_source = pynanovna.NanoVNAWorker(verbose=VERBOSE)
data_source.calibrate(load_file=CALIBRATION_FILE)  # This needs to be done through a terminal atm.
data_source.set_sweep(2.9e9, 3.1e9, 1, 101)
data_stream = data_source.stream_data(DATA_FILE)

signal_processing = SignalProcessing(
    data_stream,
    process_sleep_time=PROCESS_SLEEP_TIME,
    verbose=VERBOSE,
    interactive_mode=False
)

# Instantiate the BTSender class
bt_sender = BTSender(device_name=CAR_DEVICE_NAME)

async def main_loop():
    while True:
        await bt_sender.connect()
        data_processor = signal_processing.process_data_continuously()
        update_processor = False

        for angle, throttle in data_processor:
            send_data = {'angle': angle, 'throttle': throttle}
            latest_data = send_data.copy()

            try:
                response = requests.post("http://127.0.0.1:5000/update_data", json=send_data)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                log_message(f"Error sending data to server: {e}")
            
            # Send the data to the RC car        
            await bt_sender.update_speed(angle, throttle)

            # Handle any received data and then reset it
            update_processor = await handle_received_data(received_data, bt_sender, signal_processing)
            received_data.clear()  # Reset received_data to an empty dictionary after handling
            if update_processor:
                break

            time.sleep(1) # Uncomment this row if running from prerecorded file.

def log_message(message):
    """Send log message to connected clients."""
    socketio.emit('log_message', {'message': message})
    print(message)

async def handle_received_data(received_data, bt_sender, signal_processing):
    if received_data == {}:
        return False

    if received_data["button"] == "updateAngleButton":
        try:
            min_threshold = int(received_data["angleThresholdMin"])
            max_threshold = int(received_data["angleThresholdMax"])
            max_angle = int(received_data["angleMax"])
            if min_threshold != 0:
                bt_sender.angle_min_threshold = min_threshold
            if max_threshold != 0:
                bt_sender.angle_max_threshold = max_threshold
            if max_angle != 0:
                bt_sender.max_steering_angle = max_angle
            log_message("Updating car angle thresholds.")
        except ValueError:
            log_message("Could not update the car angle thresholds, are they valid?")
    elif received_data["button"] == "updateSpeedButton":
        try:
            min_speed = int(received_data["speedMin"])
            max_speed = int(received_data["speedMax"])
            if min_threshold != 0:
                bt_sender.min_motor_speed= min_speed
            if max_threshold != 0:
                bt_sender.max_motor_speed = max_speed
            log_message("Updating car speed thresholds.")
        except ValueError:
            log_message("Could not update the car speed thresholds, are they valid?")
    elif received_data["button"] == "rebootButton":
        log_message("Rebooting the system.")
        subprocess.run(['sudo', 'reboot', 'now'], check=True)
    elif received_data["button"] == "shutdownButton":
        log_message("Shutting down the system. Goodbye.")
        subprocess.run(['sudo', 'shutdown', 'now'], check=True)
    elif received_data["button"] == "connectCar":
        log_message("Trying to connect to the car.")
        if not bt_sender.is_connected():
            log_message("Car not connected!")
            log_message("Trying to connect car...")
            await bt_sender.connect()
    elif received_data["button"] == "refMeasure0":
        log_message("Running reference measure CLEAR.")
        signal_processing.reference_step0()
    elif received_data["button"] == "refMeasureSetup":
        log_message("Running reference setup.")
        signal_processing.setup(False)
        time.sleep(1)
        return True #  Makes the for loop restart with a new processor.
    elif "refMeasure" in received_data["button"]:
        stepno = int(received_data["button"][-1])
        log_message(f"Running reference measure step {stepno}.")
        signal_processing.reference_step_n(stepno)

    time.sleep(1)
    log_message("Done.")
    return False

# Run the main loop
asyncio.run(main_loop())
