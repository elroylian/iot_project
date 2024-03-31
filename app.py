from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize empty data
labels = ['January', 'February', 'March', 'April', 'May', 'June']
data = [0, 10, 15, 8, 22, 18]

@app.route('/')
def homepage():
    return render_template('home/index.html', labels=labels, data=data)

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

@app.route('/message', methods=['POST'])
def message():
    if request.method == 'POST':
        try:
            message = request.json.get('message')
            if message is not None:
                socketio.emit('message', {'message': message})
                print('Message:', message)
                return jsonify(success=True, message=message)
            else:
                return jsonify(success=False, error='Message field is missing or empty'), 400
        except Exception as e:
            return jsonify(success=False, error=str(e)), 500
    else:
        return jsonify(success=False, error='Only POST requests are allowed'), 405

if __name__ == '__main__':
    app.debug = True
    socketio.run(app, host='0.0.0.0', port=5000,allow_unsafe_werkzeug=True)
