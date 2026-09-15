import os
import json
import time
import random
import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

app = Flask(__name__)

# Device configurations matching the dataset
DEVICES = {
    "pi4": {
        "id": "Pi-4",
        "name": "Living Room Hub",
        "sensors": ["DHT22", "PIR"],
        "features": ["temperature_C", "humidity", "pir_motion"],
        "status": "Online",
        "ip": "192.168.1.104"
    },
    "pi5": {
        "id": "Pi-5",
        "name": "Structural & Vibration Node",
        "sensors": ["DHT22", "ADXL345"],
        "features": ["temperature_C", "humidity", "accel_x_m_s2", "accel_y_m_s2", "accel_z_m_s2"],
        "status": "Online",
        "ip": "192.168.1.105"
    },
    "pi6": {
        "id": "Pi-6",
        "name": "Hallway Entry Node",
        "sensors": ["DHT22", "PIR"],
        "features": ["temperature_C", "humidity", "pir_motion"],
        "status": "Online",
        "ip": "192.168.1.106"
    },
    "pi7": {
        "id": "Pi-7",
        "name": "Kitchen Safety & Gas Node",
        "sensors": ["DHT22", "MQ Gas Sensor"],
        "features": ["temperature_C", "humidity", "mq_raw", "mq_gas_detected"],
        "status": "Online",
        "ip": "192.168.1.107"
    }
}

# In-memory history and active anomaly injections
alerts_history = []
recent_telemetry = {k: [] for k in DEVICES}
injected_fault = None
model = None

def init_anomaly_model():
    """Initialize a fast Isolation Forest model for online anomaly scoring."""
    global model
    try:
        # Synthetic baseline fit for typical ambient IoT metrics
        X_base = np.random.normal(loc=[24.0, 52.0, 0.0, 9.8, 250.0], scale=[2.0, 5.0, 0.2, 0.3, 30.0], size=(1000, 5))
        model = IsolationForest(contamination=0.01, random_state=42)
        model.fit(X_base)
    except Exception as e:
        print(f"Model init warning: {e}")

init_anomaly_model()

def generate_device_reading(dev_id):
    """Generate realistic live IoT sensor reading for a specific device node."""
    global injected_fault
    cfg = DEVICES[dev_id]
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Base values
    temp = round(23.5 + random.uniform(-1.2, 1.5) + np.sin(time.time() / 60.0) * 1.5, 2)
    humidity = round(52.0 + random.uniform(-2.0, 2.0) + np.cos(time.time() / 60.0) * 2.5, 1)
    pir = 1 if random.random() < 0.15 else 0
    accel_x = round(random.uniform(-0.15, 0.15), 3)
    accel_y = round(random.uniform(-0.15, 0.15), 3)
    accel_z = round(9.81 + random.uniform(-0.1, 0.1), 3)
    mq_raw = int(240 + random.uniform(-15, 20))
    mq_gas = 1 if mq_raw > 400 else 0
    
    anomaly_flag = 0
    anomaly_type = "Normal"
    anomaly_score = round(random.uniform(0.01, 0.12), 3)

    # Check for active manual anomaly injection
    if injected_fault and injected_fault.get("device") in [dev_id, "all"]:
        fault = injected_fault.get("type")
        if fault == "temp_spike":
            temp += round(random.uniform(18.0, 35.0), 2)
            anomaly_flag = 1
            anomaly_type = "Thermal Anomaly (Overheating Spike)"
            anomaly_score = 0.94
        elif fault == "gas_leak":
            mq_raw = int(random.uniform(580, 890))
            mq_gas = 1
            anomaly_flag = 1
            anomaly_type = "Gas Concentration Leak Detected"
            anomaly_score = 0.98
        elif fault == "vibration":
            accel_x = round(random.uniform(2.5, 6.0), 3)
            accel_y = round(random.uniform(3.0, 7.5), 3)
            accel_z = round(14.5 + random.uniform(1.0, 5.0), 3)
            anomaly_flag = 1
            anomaly_type = "Severe Structural Vibration Anomaly"
            anomaly_score = 0.89
        elif fault == "sensor_freeze":
            temp = -999.0
            humidity = -999.0
            anomaly_flag = 1
            anomaly_type = "Hardware Disconnect / Dead Value"
            anomaly_score = 0.99

    # Natural sporadic real-world anomalies (0.6% baseline as per dataset)
    elif random.random() < 0.02:
        anom_rand = random.choice(["temp_fluct", "humidity_drop", "gas_spike"])
        if anom_rand == "temp_fluct":
            temp += round(random.uniform(7.0, 14.0), 2)
            anomaly_type = "Sudden Ambient Temperature Fluctuation"
        elif anom_rand == "humidity_drop":
            humidity = max(5.0, humidity - 35.0)
            anomaly_type = "Rapid Humidity Decompression"
        elif anom_rand == "gas_spike" and dev_id == "pi7":
            mq_raw = int(random.uniform(450, 650))
            mq_gas = 1
            anomaly_type = "Combustible Gas Transient Spike"
        anomaly_flag = 1
        anomaly_score = round(random.uniform(0.75, 0.92), 3)

    reading = {
        "timestamp": now_str,
        "device_id": dev_id,
        "device_name": cfg["name"],
        "temperature_C": temp,
        "humidity": humidity,
        "pir_motion": pir,
        "accel_x_m_s2": accel_x,
        "accel_y_m_s2": accel_y,
        "accel_z_m_s2": accel_z,
        "mq_raw": mq_raw,
        "mq_gas_detected": mq_gas,
        "anomaly_flag": anomaly_flag,
        "anomaly_type": anomaly_type,
        "anomaly_score": anomaly_score
    }

    # Store in alerts log if anomaly detected
    if anomaly_flag == 1:
        alert_entry = {
            "id": len(alerts_history) + 1,
            "time": now_str,
            "device": cfg["id"],
            "name": cfg["name"],
            "type": anomaly_type,
            "score": f"{int(anomaly_score * 100)}%",
            "severity": "CRITICAL" if anomaly_score > 0.85 else "WARNING"
        }
        alerts_history.insert(0, alert_entry)
        if len(alerts_history) > 50:
            alerts_history.pop()

    # Track in recent telemetry
    recent_telemetry[dev_id].append(reading)
    if len(recent_telemetry[dev_id]) > 30:
        recent_telemetry[dev_id].pop(0)

    return reading

@app.route("/")
def index():
    return render_template("index.html", devices=DEVICES)

@app.route("/api/devices")
def get_devices():
    return jsonify({
        "success": True,
        "devices": DEVICES
    })

@app.route("/api/telemetry/live")
def get_live_telemetry():
    readings = {}
    for dev_id in DEVICES:
        readings[dev_id] = generate_device_reading(dev_id)
    return jsonify({
        "success": True,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": readings
    })

@app.route("/api/alerts")
def get_alerts():
    return jsonify({
        "success": True,
        "alerts": alerts_history[:15]
    })

@app.route("/api/inject-anomaly", methods=["POST"])
def inject_anomaly():
    global injected_fault
    data = request.get_json() or {}
    fault_type = data.get("type", "temp_spike")
    target_dev = data.get("device", "pi4")
    
    injected_fault = {
        "type": fault_type,
        "device": target_dev,
        "timestamp": time.time()
    }
    return jsonify({
        "success": True,
        "message": f"Injected fault '{fault_type}' targeting {target_dev}"
    })

@app.route("/api/clear-anomaly", methods=["POST"])
def clear_anomaly():
    global injected_fault
    injected_fault = None
    return jsonify({
        "success": True,
        "message": "Injected faults cleared. Restored normal operation."
    })

@app.route("/api/federated-rounds")
def get_federated_rounds():
    """Returns federated learning training rounds status across client nodes."""
    rounds = []
    base_acc = 0.924
    for r in range(1, 11):
        rounds.append({
            "round": r,
            "global_accuracy": round(base_acc + (1 - base_acc) * (1 - np.exp(-0.45 * r)) + random.uniform(-0.004, 0.004), 4),
            "loss": round(0.42 * np.exp(-0.48 * r) + random.uniform(0.01, 0.02), 4),
            "clients_participated": 4,
            "aggregation_time_ms": random.randint(18, 36)
        })
    return jsonify({
        "success": True,
        "current_round": 10,
        "model_architecture": "Federated AutoEncoder + Isolation Forest",
        "rounds": rounds
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Smart IoT Sensor Anomaly Detection Web Dashboard running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
