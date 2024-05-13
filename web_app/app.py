from flask import Flask, render_template, jsonify
import random

app = Flask(__name__)

# Dummy data generator
def get_data():
    return {
        "angle": random.randint(-90, 90),
        "throttle": random.randint(0, 100)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    return jsonify(get_data())

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
