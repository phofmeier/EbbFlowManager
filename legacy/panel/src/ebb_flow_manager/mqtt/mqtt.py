import json
import logging

import paho.mqtt.client as mqtt


class MQTTConnection:
    """Connection to an MQTT broker."""

    def __init__(self, config: dict):
        """Initialize and connect to the MQTT broker

        Args:
            config (dict): configuration of the client.
        """
        self.logger = logging.getLogger(__name__)
        self.config = config

        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.connect(self.config["broker"], self.config["port"], 60)
        self.mqtt_client.loop_start()

    def publish_new_config(self, new_config: dict):
        """Publish a new configuration dict to the controller.

        Args:
            new_config (dict): new configuration to publish.
        """
        self.logger.info(
            f"Publish new configuration: {new_config}"
            f"on topic {self.config["new_config_publish_topic"]}"
        )
        self.mqtt_client.publish(
            self.config["new_config_publish_topic"], json.dumps(new_config)
        )

    def stop(self):
        """Stop the client."""
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
