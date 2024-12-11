# flask_app.py
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime
from celery import Celery
import numpy as np
import logging
import hashlib
import random
import string
import base64
import cv2
import tasks

flask_app = Flask(__name__,static_folder='static', static_url_path='/engine/static')
socketio = SocketIO(flask_app,path='/engine/socket.io')

# Serve the HTML page with JavaScript for WebSocket communication

# Configure Celery
flask_app.config['CELERY_CONFIG_MODULE'] = 'celery_config'
flask_app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
flask_app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Create Celery instance
celery = Celery(
    flask_app.import_name,
    broker=flask_app.config['CELERY_BROKER_URL'],
    backend=flask_app.config['CELERY_RESULT_BACKEND']
)
celery.conf.update(flask_app.config)

@flask_app.route('/engine')
def index():
    return render_template('v2_demo.html')

@flask_app.route('/engine/eyeCanvas.js')
def eyecanvas():
    # unique_id = tasks.generater_ID()
    #  Generate a random string of letters and digits
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    # Generate a SHA-256 hash of the random string
    random_hash = hashlib.sha256(random_string.encode()).hexdigest()
    return render_template(
        'sdk/eyeCanvas.js',
        domain=request.host,
        unique_id=random_hash)

def base64cv2(img):
    image_data = img.split(',')[1]  # Remove data URI header
    image_array = np.frombuffer(base64.b64decode(image_data), dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return frame

# Handle WebSocket connections

@socketio.on('on_connect', namespace='/engine/socket.io')
def on_connect(data):
    tasks.client_create(
        clientData=data,
        request=request
    )

@socketio.on('disconnect', namespace='/engine/socket.io')
def disconnect():
    tasks.client_remove(request)

@socketio.on('msg_data', namespace='/engine/socket.io')
def on_stream(data):
    logging.info(f'{datetime.now().strftime("%m:%d:%Y:%H:%M:%S")}: Received data: {data}')

    frame = base64cv2(data['image'])
    tasks.client_process_data(frame, data, request, emit, request.sid)

if __name__ == '__main__':
    socketio.run(app=flask_app,host="0.0.0.0",port=5000)
