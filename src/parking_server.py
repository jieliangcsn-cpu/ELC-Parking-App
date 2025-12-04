"""
ELC Parking App - Web Server & Admin Interface
Author: Jie Liang
Course: CS2450

This server provides:
1. REST API for parking lot data
2. Web-based admin interface to simulate sensor data
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from desktop app

# Data file to persist parking state
DATA_FILE = "parking_data.json"

# Initialize parking lots data
PARKING_LOTS = {
    "17": {
        "lot_id": "17",
        "name": "Lot 17",
        "total_spaces": 35,
        "permit_type": "Student",
        "drive_time": 2,
        "walk_time": 4,
        "spaces": [False] * 35  # False = empty, True = occupied
    },
    "18": {
        "lot_id": "18",
        "name": "Lot 18",
        "total_spaces": 45,
        "permit_type": "Staff",
        "drive_time": 1,
        "walk_time": 3,
        "spaces": [False] * 45
    },
    "19": {
        "lot_id": "19",
        "name": "Lot 19",
        "total_spaces": 60,
        "permit_type": "Both",
        "drive_time": 2,
        "walk_time": 5,
        "spaces": [False] * 60
    },
    "14": {
        "lot_id": "14",
        "name": "Lot 14",
        "total_spaces": 50,
        "permit_type": "Open",
        "drive_time": 3,
        "walk_time": 7,
        "spaces": [False] * 50
    }
}


def load_data():
    """Load parking data from file if exists"""
    global PARKING_LOTS
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                PARKING_LOTS = json.load(f)
        except:
            pass


def save_data():
    """Save parking data to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(PARKING_LOTS, f, indent=2)


def get_occupied_count(lot_id):
    """Count occupied spaces in a lot"""
    return sum(PARKING_LOTS[lot_id]["spaces"])


def get_available_count(lot_id):
    """Count available spaces in a lot"""
    total = PARKING_LOTS[lot_id]["total_spaces"]
    occupied = get_occupied_count(lot_id)
    return total - occupied


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/lots', methods=['GET'])
def get_all_lots():
    """Get all parking lots with current occupancy"""
    lots_data = []
    for lot_id, lot in PARKING_LOTS.items():
        lots_data.append({
            "lot_id": lot["lot_id"],
            "name": lot["name"],
            "total_spaces": lot["total_spaces"],
            "occupied_spaces": get_occupied_count(lot_id),
            "available_spaces": get_available_count(lot_id),
            "permit_type": lot["permit_type"],
            "drive_time": lot["drive_time"],
            "walk_time": lot["walk_time"],
            "last_update": datetime.now().isoformat()
        })
    return jsonify(lots_data)


@app.route('/api/lot/<lot_id>', methods=['GET'])
def get_lot(lot_id):
    """Get specific lot data"""
    if lot_id not in PARKING_LOTS:
        return jsonify({"error": "Lot not found"}), 404
    
    lot = PARKING_LOTS[lot_id]
    return jsonify({
        "lot_id": lot["lot_id"],
        "name": lot["name"],
        "total_spaces": lot["total_spaces"],
        "occupied_spaces": get_occupied_count(lot_id),
        "available_spaces": get_available_count(lot_id),
        "permit_type": lot["permit_type"],
        "drive_time": lot["drive_time"],
        "walk_time": lot["walk_time"],
        "spaces": lot["spaces"],
        "last_update": datetime.now().isoformat()
    })


@app.route('/api/lot/<lot_id>/toggle/<int:space_index>', methods=['POST'])
def toggle_space(lot_id, space_index):
    """Toggle a parking space occupied/empty"""
    if lot_id not in PARKING_LOTS:
        return jsonify({"error": "Lot not found"}), 404
    
    lot = PARKING_LOTS[lot_id]
    if space_index < 0 or space_index >= lot["total_spaces"]:
        return jsonify({"error": "Invalid space index"}), 400
    
    # Toggle the space
    lot["spaces"][space_index] = not lot["spaces"][space_index]
    save_data()
    
    return jsonify({
        "success": True,
        "lot_id": lot_id,
        "space_index": space_index,
        "occupied": lot["spaces"][space_index],
        "occupied_count": get_occupied_count(lot_id),
        "available_count": get_available_count(lot_id)
    })


@app.route('/api/lot/<lot_id>/reset', methods=['POST'])
def reset_lot(lot_id):
    """Reset all spaces in a lot to empty"""
    if lot_id not in PARKING_LOTS:
        return jsonify({"error": "Lot not found"}), 404
    
    lot = PARKING_LOTS[lot_id]
    lot["spaces"] = [False] * lot["total_spaces"]
    save_data()
    
    return jsonify({
        "success": True,
        "lot_id": lot_id,
        "message": "All spaces cleared"
    })


@app.route('/api/lot/<lot_id>/fill', methods=['POST'])
def fill_lot(lot_id):
    """Fill all spaces in a lot"""
    if lot_id not in PARKING_LOTS:
        return jsonify({"error": "Lot not found"}), 404
    
    lot = PARKING_LOTS[lot_id]
    lot["spaces"] = [True] * lot["total_spaces"]
    save_data()
    
    return jsonify({
        "success": True,
        "lot_id": lot_id,
        "message": "All spaces filled"
    })


@app.route('/api/lot/<lot_id>/random', methods=['POST'])
def randomize_lot(lot_id):
    """Randomize occupancy in a lot"""
    import random
    
    if lot_id not in PARKING_LOTS:
        return jsonify({"error": "Lot not found"}), 404
    
    lot = PARKING_LOTS[lot_id]
    
    # Set realistic occupancy patterns
    if lot_id == "17":  # Student lot - 80-100% full
        occupied_count = random.randint(28, 35)
    elif lot_id == "18":  # Staff lot - 90-100% full
        occupied_count = random.randint(40, 45)
    elif lot_id == "19":  # Mixed lot - 75-100% full
        occupied_count = random.randint(45, 60)
    else:  # Lot 14 - 30-80% full
        occupied_count = random.randint(15, 40)
    
    # Reset and randomly fill
    lot["spaces"] = [False] * lot["total_spaces"]
    occupied_indices = random.sample(range(lot["total_spaces"]), occupied_count)
    for idx in occupied_indices:
        lot["spaces"][idx] = True
    
    save_data()
    
    return jsonify({
        "success": True,
        "lot_id": lot_id,
        "occupied_count": occupied_count,
        "available_count": lot["total_spaces"] - occupied_count
    })


# ============================================================================
# WEB INTERFACE
# ============================================================================

@app.route('/')
def index():
    """Main admin interface"""
    return render_template('admin.html')


@app.route('/admin')
def admin():
    """Admin interface (same as index)"""
    return render_template('admin.html')


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    load_data()
    print("\n" + "="*60)
    print("🚗 ELC Parking App Server Started")
    print("="*60)
    print("\n📊 Admin Interface: http://localhost:5000")
    print("📡 API Endpoint: http://localhost:5000/api/lots")
    print("\n🎯 Use the admin interface to simulate parking occupancy")
    print("🖥️  Run parking_app_client.py to test the client app\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
