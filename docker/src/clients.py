from eyeGestures.eyegestures import EyeGestures_v2, EyeGestures_v1
from eyeGestures.calibration_v2 import Calibrator
import numpy as np

class Client:

    def __init__(self,v1=False):
        if not v1:
            self.gestures = EyeGestures_v2(300)
            x = np.arange(0, 1.01, 0.33)
            y = np.arange(0, 1.01, 0.33)

            xx, yy = np.meshgrid(x, y)

            calibration_map = np.column_stack([xx.ravel(), yy.ravel()])
            # self.calibMap = np.array([[0.1,0.1],[0.1,0.9],[0.9,0.9],[0.9,0.1],[0.5,0.5],
                    # [0.5,0.1],[0.5,0.9],[0.9,0.5],[0.1,0.5]])
            np.random.shuffle(calibration_map)
            self.calibMap = calibration_map

            self.gestures.enableCNCalib()
            self.gestures.setFixation(1.0)
            self.gestures.setClassicImpact(2)
            self.gestures.uploadCalibrationMap(self.calibMap)
        else: 
            self.gestures = EyeGestures_v1()
            
        self.users = list()
        self.max_clients = 8 # each client takes from 0.012s to 0.015s to process

    def number(self):
        return len(self.users)

    def process(self,frame,calibrate,data):
        if data['unique_id'] not in self.users:
            self.users.append(data['unique_id'])
            self.gestures.uploadCalibrationMap(self.calibMap,context=data['unique_id'])

        event, calibration = self.gestures.step(frame, calibrate, data['width'], data['height'],context=data['unique_id'])
        return event, calibration

    def remove(self,id):
        try:
            self.users.remove(id)
        except Exception as e:
            print(f"Failed to remove user: {e} id: {id}")

class ClientBuckets:

    def __init__(self):

        self.id2bucket = dict()
        self.clients = []
        self.MAX_BUCKETS = 25

        if len(self.clients) == 0:
            self.clients.append(Client())

    def checkSpace(self,id):
        if id in self.id2bucket.keys():
            return True
        
        if self.clients[len(self.clients) - 1].number() < 9:
            return True
        else:
            if len(self.clients) < self.MAX_BUCKETS:
                return True
        return False
        
    def get(self,id):
        if id not in self.id2bucket.keys():
            if self.clients[len(self.clients) - 1].number() >= self.clients[len(self.clients) - 1].max_clients:
                self.clients.append(Client())
            self.id2bucket[id] = len(self.clients) - 1

        return self.clients[self.id2bucket[id]]

    def remove(self,id):
        if id in self.id2bucket.keys():
            self.clients[self.id2bucket[id]].remove(id)
            del self.id2bucket[id]

            if self.clients[self.id2bucket[id]].number() == 0:
                self.clients.remove(self.clients[self.id2bucket[id]])

        if len(self.clients) == 0:
            self.clients.append(Client())