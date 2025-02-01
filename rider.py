#!/usr/bin/env python3
"""
rider.py

This module implements a Rider interface for the indoor cycling training system.
The Rider class generates the following MQTT messages:
    - list_devices
    - pair_device
    - get_plan
    - set_ftp

It handles the following incoming MQTT messages:
    - device_list
    - send_plan
    - start_plan
    - stop_plan
    - set_target_power
    - measured_power
"""

import time
import json
import logging
import threading

import paho.mqtt.client as mqtt

# Import the messaging factory functions from the mqtt_service sub-package.
from mqtt_service.messaging import (
    ListDevices,
    PairDevice,
    GetPlan,
    SetFTP,
    # The following are for handling responses:
    DeviceList,
    SendPlan,
    StartPlan,
    StopPlan,
    SetTargetPower,
    SetMeasuredPower,
)
from mqtt_service.constants import APP_ID, hostname

# Configure logging.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Rider")


class Rider:
    def __init__(self, mqtt_client):
        """
        Initializes the Rider.

        Parameters:
            mqtt_client (mqtt.Client): An instance of the MQTT client to use.
        """
        self.client = mqtt_client
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create messaging objects for outgoing commands.
        self.list_devices_msg = ListDevices(self.client)
        self.pair_device_msg = PairDevice(self.client)
        self.get_plan_msg = GetPlan(self.client)
        self.set_ftp_msg = SetFTP(self.client)

        # Register callbacks for incoming responses.
        self._register_response_callbacks()

    def _register_response_callbacks(self):
        """
        Registers MQTT callbacks for incoming messages:
            - device_list: Response to list_devices.
            - send_plan: The training plan sent by the coach.
            - start_plan: Notification that the training plan has started.
            - stop_plan: Notification that the training plan has stopped.
            - set_target_power: Broadcast target power from the coach.
            - measured_power: Measured power reports from a trainer.
        """
        topics = {
            "device_list": self._handle_device_list,
            "send_plan": self._handle_send_plan,
            "start_plan": self._handle_start_plan,
            "stop_plan": self._handle_stop_plan,
            "set_target_power": self._handle_set_target_power,
            "set_measured_power": self._handle_measured_power,
        }

        for topic_suffix, callback in topics.items():
            topic = f"{APP_ID}/{topic_suffix}"
            self.client.message_callback_add(topic, callback)
            self.logger.info(f"Rider registered callback for topic: {topic}")

    # ----- Methods to generate outgoing messages -----
    def request_device_list(self):
        """Sends a ListDevices message to request the list of available devices."""
        self.logger.info("Rider: Requesting device list.")
        self.list_devices_msg.publish()

    def pair_device(self, uuid_trainer, uuid_rider):
        """
        Sends a PairDevice message to request pairing between a trainer and a rider.
        
        Parameters:
            uuid_trainer (str): The trainer's unique identifier.
            uuid_rider (str): The rider's unique identifier.
        """
        self.logger.info(f"Rider: Requesting pairing of trainer {uuid_trainer} with rider {uuid_rider}.")
        self.pair_device_msg.publish(uuid_trainer=uuid_trainer, uuid_rider=uuid_rider)

    def request_training_plan(self):
        """Sends a GetPlan message to request a training plan."""
        self.logger.info("Rider: Requesting training plan.")
        self.get_plan_msg.publish()

    def set_ftp(self, uuid_trainer, ftp):
        """
        Sends a SetFTP message to set the FTP value.
        
        Parameters:
            uuid_trainer (str): The trainer's unique identifier.
            ftp (int): The FTP value.
        """
        self.logger.info(f"Rider: Setting FTP for trainer {uuid_trainer} to {ftp}.")
        self.set_ftp_msg.publish(uuid_trainer=uuid_trainer, ftp=ftp)

    # ----- Callback Handlers for incoming messages -----
    def _handle_device_list(self, client, userdata, msg):
        """Handles an incoming DeviceList message."""
        try:
            payload = json.loads(msg.payload.decode())
            devices = payload.get("device_list", [])
            self.logger.info(f"Rider received device list: {devices}")
        except Exception as e:
            self.logger.error(f"Error processing device list: {e}")

    def _handle_send_plan(self, client, userdata, msg):
        """Handles an incoming SendPlan message containing the training plan."""
        try:
            payload = json.loads(msg.payload.decode())
            plan = payload.get("training_plan", [])
            self.logger.info(f"Rider received training plan: {plan}")
        except Exception as e:
            self.logger.error(f"Error processing training plan: {e}")

    def _handle_start_plan(self, client, userdata, msg):
        """Handles an incoming StartPlan message indicating the training plan has started."""
        self.logger.info("Rider received start_plan message.")

    def _handle_stop_plan(self, client, userdata, msg):
        """Handles an incoming StopPlan message indicating the training plan has stopped."""
        self.logger.info("Rider received stop_plan message.")

    def _handle_set_target_power(self, client, userdata, msg):
        """Handles an incoming SetTargetPower message broadcasting target power."""
        try:
            payload = json.loads(msg.payload.decode())
            target_power = payload.get("target_power")
            self.logger.info(f"Rider received broadcast target power: {target_power}%")
        except Exception as e:
            self.logger.error(f"Error processing set_target_power message: {e}")

    def _handle_measured_power(self, client, userdata, msg):
        """Handles an incoming MeasuredPower message with measured power information."""
        try:
            payload = json.loads(msg.payload.decode())
            uuid_trainer = payload.get("uuid_trainer")
            measured_power = payload.get("measured_power")
            self.logger.info(f"Rider received measured power from trainer {uuid_trainer}: {measured_power} watts")
        except Exception as e:
            self.logger.error(f"Error processing measured power message: {e}")


# ----- Main method for testing Rider functionality -----
if __name__ == "__main__":
    # Create an MQTT client (using Callback API version 2 to avoid deprecation warnings).
    client = mqtt.Client(
        client_id="",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )

    # Global fallback callback for topics without a specific registered callback.
    def on_message(client, userdata, msg):
        logger.info(f"Global on_message: Topic {msg.topic} -> {msg.payload.decode()}")

    client.on_message = on_message

    # Connect to the MQTT broker.
    client.connect(hostname)
    # Subscribe to all topics under APP_ID.
    subscribe_topic = f"{APP_ID}/#"
    client.subscribe(subscribe_topic)
    client.loop_start()

    # Create an instance of Rider.
    rider = Rider(client)

    # For testing, wait a few seconds to allow subscriptions to take effect.
    time.sleep(2)

    # --- Generate outgoing messages ---
    rider.request_device_list()
    time.sleep(1)

    rider.pair_device("trainer_123", "rider_999")
    time.sleep(1)

    rider.set_ftp("trainer_123", 250)
    time.sleep(1)

    rider.request_training_plan()
    time.sleep(1)

    # Let the Rider run for a while to process any incoming messages.
    time.sleep(10)

    client.loop_stop()
    client.disconnect()
