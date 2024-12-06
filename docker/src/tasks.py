from clients import ClientBuckets
from datetime import datetime
# from celery import Celery
import logging
import time

# app = Celery('tasks', broker='redis://localhost:6379/0')
sids_to_keys = dict() # backup
buckets = ClientBuckets()

clients2eid = dict()
clients = []

# @app.task
def client_remove(request):   
    try:
        unique_id = sids_to_keys[request.sid]
        buckets.remove(unique_id)
    except Exception as e:
        print(f"Exception: {e}")
    pass
    
# Handle WebSocket connections
# @app.task
def client_create(clientData, request):
    KEY = "unique_id"
    sids_to_keys[request.sid] = clientData[KEY]

# Handle WebSocket connections
# @app.task
def client_process_data(frame, data, request, emit, sid):
    logging.info(f'{datetime.now().strftime("%m:%d:%Y:%H:%M:%S")}: Processing data from {data["unique_id"]} {data}')
    # drop if messages are late 10ms
    if (int(time.time()) - data["timestamp"]) > 10:
        return
    # Flip the frame horizontally
    try:
        client = buckets.get(data["unique_id"])
        event, calibration = client.process(frame,
                                        data['calibrate'],
                                        data)
        if event is None:
            emit('rsp', {"x" : 0, "y" : 0, "c_x" : 0, "c_y" : 0})
            return

        payload = {"x" : event.point[0],
                   "y" : event.point[1],
                "c_x" : calibration.point[0],
                "c_y" : calibration.point[1],
                "radius" : calibration.acceptance_radius}
        emit('rsp',payload)
    except Exception as e:
        emit('rsp', {"x" : 0, "y" : 0, "c_x" : 0, "c_y" : 0}, namespace='/v2_beta_testing')
