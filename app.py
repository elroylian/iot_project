from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import requests

app = Flask(__name__)
socketio = SocketIO(app)


# Initialize empty data
labels = ['January', 'February', 'March', 'April', 'May', 'June']
data = [0, 10, 15, 8, 22, 18]

@app.route('/')
def homepage():
    return render_template('home/index.html', labels=labels, data=data)

@app.route('/ttn')
def ttn():
    return render_template('home/message.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    global data, labels
    if request.method == 'POST':
        try:
            new_data = request.json.get('data')
            if new_data is not None:
                data.append(new_data)
                labels.append('New Month')
                socketio.emit('chart_updated', {'data': data, 'labels': labels})
                return jsonify(success=True, new_data=new_data)
            else:
                return jsonify(success=False, error='Data field is missing or empty'), 400
        except Exception as e:
            return jsonify(success=False, error=str(e)), 500
    else:
        return jsonify(success=False, error='Only POST requests are allowed'), 405

from flask import request, jsonify

@app.route('/message/<farm_id>', methods=['POST'])
def message(farm_id):
    if request.method == 'POST':
        try:
            # Get the JSON data from the request
            json_data = request.json
            
            # Check if the 'uplink_message' key exists in the JSON data
            if 'uplink_message' in json_data:
                # If it exists, extract the 'decoded_payload' from 'uplink_message'
                decoded_payload = json_data['uplink_message'].get('decoded_payload', {})
                
                # Extract the 'message' from 'decoded_payload'
                message = decoded_payload.get('message')
                
                # Extract the RSSI value
                rssi = json_data['uplink_message'].get('rx_metadata', [{}])[0].get('rssi')
                
                # Split the message by newline character '\n'
                message_lines = message.split('\n')
                
                # Log the message lines and RSSI
                print('Message lines:', message_lines)
                print('RSSI:', rssi)
                
                # Emit the message and RSSI via socketio
                socketio.emit('message_updated', {'message': message_lines, 'rssi': rssi, 'farm_id': farm_id})
                
                return jsonify(success=True)
            else:
                return jsonify(success=False, error='Uplink message not found'), 400
        except Exception as e:
            return jsonify(success=False, error=str(e)), 500
    else:
        return jsonify(success=False, error='Only POST requests are allowed'), 405


if __name__ == '__main__':
    app.debug = True
    socketio.run(app, host='0.0.0.0', port=5000,allow_unsafe_werkzeug=True)
