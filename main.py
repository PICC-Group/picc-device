import pynanovna
import threading
import requests
from flask import Flask, render_template, jsonify, request
from signal_processing import SignalProcessing
from bt_car_control import BTSender
import time
import asyncio
import subprocess

DATA_FILE = False#"../save_plate.csv"
CALIBRATION_FILE = "../cal0514.cal"
VERBOSE = True
PROCESS_SLEEP_TIME = 0.0001
CAR_DEVICE_NAME = "BT05-BLE"

app = Flask(__name__)
latest_data = {"angle": 1, "throttle": 1}
received_data = {}
log_messages = []

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

@app.route("/logs")
def logs():
    return jsonify(log_messages)

def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False)

def log_message(message):
    """Store log message for client retrieval."""
    log_messages.append({'message': message})
    print(message)

# NanoVNA Setup
def setup_nanovna(verbose, calibration_file, data_file, process_sleep_time):
    data_source = pynanovna.NanoVNAWorker(verbose=verbose)
    data_source.calibrate(load_file=calibration_file)  # This needs to be done through a terminal atm.
    data_source.set_sweep(2.9e9, 3.1e9, 1, 101)
    data_stream = data_source.stream_data(data_file)

    signal_processing = SignalProcessing(
        data_stream,
        process_sleep_time=process_sleep_time,
        verbose=verbose,
        interactive_mode=False
    )
    return signal_processing, data_source


# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Instantiate the BTSender class
bt_sender = BTSender(device_name=CAR_DEVICE_NAME)

async def main_loop():
    global received_data
    global log_messages
    while True:
        signal_processing, vna = setup_nanovna(VERBOSE, CALIBRATION_FILE, DATA_FILE, PROCESS_SLEEP_TIME)

        while not signal_processing.reference_setup_done:
            # Clear logs.
            log_messages.clear()

            # Handle any received data and then reset it
            await handle_received_data(received_data, bt_sender, signal_processing)
            received_data.clear()  # Reset received_data to an empty dictionary after handling

            time.sleep(1) #  Increase sleep time to 1 if running a pre recorded file.

        await bt_sender.connect()
        data_processor = signal_processing.process_data_continuously()

        for angle, throttle in data_processor:
            send_data = {'angle': angle, 'throttle': throttle}
            global latest_data
            latest_data = send_data.copy()

            try:
                response = requests.post("http://127.0.0.1:5000/update_data", json=send_data)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                log_message(f"Error sending data to server: {e}")
            
            # Send the data to the RC car
            if bt_sender.is_connected():
                await bt_sender.update_speed(angle, throttle)

            # Clear logs.
            log_messages.clear()

            # Handle any received data and then reset it
            await handle_received_data(received_data, bt_sender, signal_processing)
            received_data.clear()  # Reset received_data to an empty dictionary after handling

            time.sleep(1) #  Increase sleep time to 1 if running a pre recorded file.
        
        # Kill vna.
        vna.kill()
        signal_processing = None


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
    elif "refMeasure" in received_data["button"]:
        stepno = int(received_data["button"][-1])
        log_message(f"Running reference measure step {stepno}.")
        signal_processing.reference_step_n(stepno)
    elif received_data["button"] == "updateCalibrationFile":
        global CALIBRATION_FILE
        log_message(f"Changing calibration file. Old file: {CALIBRATION_FILE}")
        CALIBRATION_FILE = received_data["calibrationFile"]
        log_message(f"Calibration file changed. New file: {CALIBRATION_FILE}")
        log_message("THIS FUNCTION HAS SOME MAJOR PROBLEMS, SYSTEM MAY BE BROKEN.")
        time.sleep(1)

    time.sleep(1)


# Run the main loop
asyncio.run(main_loop())
