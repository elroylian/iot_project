from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_mysqldb import MySQL

from flask_cors import CORS
import re
from datetime import datetime
import os


# Load environment variables from .env file


app = Flask(__name__)
socketio = SocketIO(app)


# Set the timezone to Asia/Singapore
app.config['TZ'] = 'Asia/Singapore'

app.config["MYSQL_DB"] = os.getenv("MYSQL_DB")
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")

mysql = MySQL(app)

CORS(app)

# Declare cursor as a global variable
# cursor = None

# Attempt to establish the connection within the application context
with app.app_context():
    try:
        # Attempt to establish the connection
        cursor = mysql.connection.cursor()
        print("Connected to the database successfully!")
    except Exception as e:
        print(f"Error connecting to the database: {e}")


# @app.route('/')
# def homepage():
#     return render_template('home/index.html', labels=labels, data=data)

@app.route('/')
def index():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT DISTINCT mac_address FROM sensor_data")
        data = cursor.fetchall()
        mac_addresses = [row[0] for row in data]  # Extracting MAC addresses from the fetched data
        # cursor.execute("SELECT timestamp, temperature, humidity, rssi FROM sensor_data WHERE mac_address = %s ORDER BY timestamp ASC", (mac_address,))
        print(data)
        return render_template('home/index.html', mac_address=mac_addresses)
    except Exception as e:
        return render_template('error/error.html', error=e)
    
@app.route('/settings')
def settings():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT DISTINCT mac_address FROM sensor_data")
        data = cursor.fetchall()
        mac_addresses = [row[0] for row in data]  # Extracting MAC addresses from the fetched data
        return render_template('home/settings.html', mac_addresses=mac_addresses)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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


@app.route('/get-latest-data', methods=['POST'])
def get_latest_data():
    try:
        mac_address = request.json.get('mac_address')
        if mac_address:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT timestamp, temperature, humidity, rssi FROM sensor_data WHERE mac_address = %s ORDER BY timestamp DESC LIMIT 1", (mac_address,))
            data = cursor.fetchone()
            return jsonify({'success': True, 'data': data, 'mac_address': mac_address})
        else:
            return jsonify({'success': False, 'error': 'MAC address not provided'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/get-all-data')
# def get_all_data():

#     try:
#         def generate():
#             cursor = mysql.connection.cursor()
#             cursor.execute("SELECT mac_address, timestamp, temperature, humidity, rssi FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
#             data = cursor.fetchall()
#             json_data = json.dumps(data)
#             yield f"data:{json_data}\n\n"
#         response = Response(stream_with_context(generate()), mimetype="text/event-stream")
#         return response
#         # return jsonify({'success': True, 'data': data})
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/update-data', methods=['POST','GET'])
def get_all_data():
    if request.method == 'GET':
        try:
            # Get the JSON data from the request
            # json_data = request.json

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT mac_address, timestamp, temperature, humidity, rssi FROM sensor_data ORDER BY timestamp DESC LIMIT 2")
            data = cursor.fetchall()
            socketio.emit('data_update', {'data': data})
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        try:
            mac_address = request.json.get('mac_address')

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT timestamp, temperature, humidity, rssi FROM sensor_data WHERE mac_address = %s ORDER BY timestamp DESC LIMIT 1", (mac_address,))
            data = cursor.fetchone()

            if data:
                # Extract specific fields from the fetched data
                timestamp, temperature, humidity, rssi = data
                # app.logger.critical(timestamp, temperature, humidity, rssi)
                # Emit the extracted data to the socket
                socketio.emit('data_update_'+mac_address, {'timestamp': timestamp, 'temperature': temperature, 'humidity': humidity, 'rssi': rssi})
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'No data found for the specified MAC address'}), 404

        except KeyError:
            return jsonify({'success': False, 'error': 'Missing "mac_address" field in the request'}), 400

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


# Handle the POST request to push data from TTN
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

                # Get the current time and convert it to string in 'YYYY-MM-DD HH:MM:SS' format
                # current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                current_time = datetime.now().strftime('%d-%m-%y %H:%M:%S')

                mac_addresses = []

                for plant in message_lines:
                    measurements = re.findall(r'M ([\w:]+) - T: (\d+\.\d+) C, H: (\d+\.\d+)', plant)
                    # print('MAC:', measurements[0][0], 'Temperature:', measurements[0][1], 'Humidity:', measurements[0][2])
                    mac_addresses.append(measurements[0][0])
                    # Insert the data into the database
                    try:
                        app.logger.critical(measurements)
                        cursor = mysql.connection.cursor()
                        cursor.execute("INSERT INTO sensor_data (mac_address, temperature, humidity, rssi, timestamp) VALUES (%s, %s, %s,%s,%s)", (measurements[0][0], float(measurements[0][1]), float(measurements[0][2]), int(rssi), current_time))
                        mysql.connection.commit()
                    except Exception as e:
                        return jsonify(success=False,error="Error inserting data into the database:"+str(e)), 500
                     
                

                # Emit the message and RSSI via socketio
                # socketio.emit('message_updated', {'message': message_lines, 'rssi': rssi})
                
                return jsonify(success=True)
            else:
                return jsonify(success=False, error='Uplink message not found'), 400
        except Exception as e:
            app.logger.error(f"Error inserting data into the database: {e}")
            return jsonify(success=False, error=str(e)), 500
    else:
        return jsonify(success=False, error='Only POST requests are allowed'), 405

@app.errorhandler(404)
def page_not_found(error):
    # Render a custom 404 page
    return render_template('error/404.html'), 404    



if __name__ == '__main__':
    app.debug = False
    socketio.run(app, host='0.0.0.0', port=5000)
