from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_mysqldb import MySQL
from flask_cors import CORS
import requests
import re
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

app.config["MYSQL_DB"] = "iot_project"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root"
app.config["MYSQL_HOST"] = "localhost"

mysql = MySQL(app)

CORS(app)

try:
    # Attempt to establish the connection
    connection = mysql.connection.cursor()
except Exception as e:
    print(f"Error connecting to the database: {e}")

# Initialize empty data and labels
labels = ['January', 'February', 'March', 'April', 'May', 'June']
data = [0, 10, 15, 8, 22, 18]

# @app.route('/')
# def homepage():
#     return render_template('home/index.html', labels=labels, data=data)

@app.route('/')
def ttn():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT DISTINCT mac_address FROM sensor_data")
        data = cursor.fetchall()
        mac_addresses = [row[0] for row in data]  # Extracting MAC addresses from the fetched data
        # cursor.execute("SELECT timestamp, temperature, humidity, rssi FROM sensor_data WHERE mac_address = %s ORDER BY timestamp ASC", (mac_address,))
        print(data)
        return render_template('home/message.html', mac_address=mac_addresses)
    except Exception as e:
        print(f"Error fetching data from the database: {e}")

@app.route('/get-data', methods=['POST'])
def data():
    try:
        # mac_address = request.args.get('mac_address')
        mac_address = request.json.get('mac_address')
        if mac_address:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT timestamp, temperature, humidity, rssi FROM sensor_data WHERE mac_address = %s ORDER BY timestamp ASC", (mac_address,))
            data = cursor.fetchall()
            return jsonify({'success': True, 'data': data, 'mac_address': mac_address})
        else:
            return jsonify({'success': False, 'error': 'MAC address not provided'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@socketio.on('request_data')
def handle_request_data(data):
    try:
        # Extract the MAC address from the request
        mac_address = data.get('mac_address')
        
        # Check if the MAC address is provided
        if mac_address:
            # Fetch data from the database by MAC address and order it by timestamp
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT timestamp, temperature, humidity, rssi FROM sensor_data WHERE mac_address = %s ORDER BY timestamp ASC", (mac_address,))
            data = cursor.fetchall()
            emit('data_response', {'success': True, 'data': data})
        else:
            emit('data_response', {'success': False, 'error': 'MAC address not provided'})
    except Exception as e:
        emit('data_response', {'success': False, 'error': str(e)}) 

# @app.route('/webhook', methods=['POST'])
# def webhook():
#     global data, labels
#     if request.method == 'POST':
#         try:
#             new_data = request.json.get('data')
#             if new_data is not None:
#                 data.append(new_data)
#                 labels.append('New Month')
#                 socketio.emit('chart_updated', {'data': data, 'labels': labels})
#                 return jsonify(success=True, new_data=new_data)
#             else:
#                 return jsonify(success=False, error='Data field is missing or empty'), 400
#         except Exception as e:
#             return jsonify(success=False, error=str(e)), 500
#     else:
#         return jsonify(success=False, error='Only POST requests are allowed'), 405

@app.route('/push', methods=['POST'])
def push():
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
                message_lines.remove('')  # Remove empty lines
                # Log the message lines and RSSI
                print('Message lines:', message_lines)
                print('Size',len(message_lines))
                socketio.emit('update_chart')

                # Get the current time and convert it to string in 'YYYY-MM-DD HH:MM:SS' format
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                mac_addresses = []

                for plant in message_lines:
                    measurements = re.findall(r'M ([\w:]+) - T: (\d+\.\d+) C, H: (\d+\.\d+)', plant)
                    print('MAC:', measurements[0][0], 'Temperature:', measurements[0][1], 'Humidity:', measurements[0][2])
                    mac_addresses.append(measurements[0][0])
                    # Insert the data into the database
                    try:
                        cursor = mysql.connection.cursor()
                        cursor.execute("INSERT INTO sensor_data (mac_address, temperature, humidity, rssi, timestamp) VALUES (%s, %s, %s,%s,%s)", (measurements[0][0], float(measurements[0][1]), float(measurements[0][2]), int(rssi), current_time))
                        mysql.connection.commit()
                        # socketio.emit('get_data')
                        # socketio.emit('get_data', { 'mac_address': '4c:75:25:cb:7f:50' })
                    except Exception as e:
                        print(f"Error inserting data into the database: {e}")
                     
                

                # Emit the message and RSSI via socketio
                # socketio.emit('message_updated', {'message': message_lines, 'rssi': rssi})
                
                return jsonify(success=True)
            else:
                return jsonify(success=False, error='Uplink message not found'), 400
        except Exception as e:
            return jsonify(success=False, error=str(e)), 500
    else:
        return jsonify(success=False, error='Only POST requests are allowed'), 405
        



if __name__ == '__main__':
    # app.debug = True
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
