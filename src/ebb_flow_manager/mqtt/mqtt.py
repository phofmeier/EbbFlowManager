import json

import paho.mqtt.client as mqtt


class MQTTConnection:
    def __init__(self, config: dict):
        self.config = config

        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.connect(self.config["broker"], self.config["port"], 60)
        self.mqtt_client.loop_start()

    def publish_new_config(self, new_config: dict):
        self.mqtt_client.publish(
            self.config["new_config_publish_topic"], json.dumps(new_config)
        )

    def stop(self):
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
