import datetime
import json
from time import sleep

import paho.mqtt.client as mqtt


class MQTTConnection():
    def __init__(self):
        
        broker = "192.168.2.106"
        port = 1883
        self.published_messages = []



        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.connect(broker, port, 60)
        self.mqtt_client.loop_start()


    def publish_new_config(self, new_config:dict):
        self.published_messages.append(
        self.mqtt_client.publish("ef/efc/config/set", json.dumps(new_config))
        )

    def stop(self):
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
