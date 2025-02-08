#!/usr/bin/env python3
"""
coach.py

This module implements a Coach interface for the indoor cycling training system.
It generates the following messages:
    - ListDevices
    - PairDevice
    - SendPlan
    - SetFTP
    - StartPlan
    - SetTargetPower
    - SetTargetCadence
    - StopPlan

It also handles the following incoming messages:
    - DeviceList
    - GetPlan
    - MeasuredPower
    - MeasuredCadence

The training plan consists of a list of tuples, where each tuple has four elements:
    (start_time_offset, target_power, target_cadence, description)
Example:
    (0, 50, 90, "Warmup"),
    (60*2, 100, 80, "Interval"),
    (60*3, 50, 80, "Rest"),
    (60*4, 100, 80, "Interval"),
    (60*5, 50, 80, "Rest"),
    (60*6, 100, 80, "Interval"),
    (60*7, 50, 80, "Rest"),
    (60*10, 50, 85, "Cooldown"),
    (60*12, 0, 85, "stop")  # End of session.
"""

import time
import json
import logging
import threading

import paho.mqtt.client as mqtt

# Import the messaging factory functions from the mqtt_service sub-package.
from .messaging import (
    ListDevices,
    PairDevice,
    SendPlan,
    SetFTP,
    StartPlan,
    SetTargetPower,
    SetTargetCadence,
    StopPlan,
    DeviceList,
    GetPlan,
)
from .constants import APP_ID, hostname

# Configure logging.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Coach")


class Coach:
    def __init__(self, mqtt_client, training_plan=None):
        """
        Initializes the Coach.

        Parameters:
            mqtt_client (mqtt.Client): An instance of the MQTT client to use.
            training_plan (list of tuples, optional): A training plan consisting of a list
                of tuples with the format (start_time_offset, target_power, target_cadence, description).
                If not provided, a default training plan is used.
        """
        self.client = mqtt_client
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create messaging objects for outgoing commands.
        self.list_devices_msg = ListDevices(self.client)
        self.pair_device_msg = PairDevice(self.client)
        self.send_plan_msg = SendPlan(self.client)
        self.set_ftp_msg = SetFTP(self.client)
        self.start_plan_msg = StartPlan(self.client)
        # New broadcast-style SetTargetPower message (only requires target_power).
        self.set_target_power_msg = SetTargetPower(self.client)
        self.set_target_cadence_msg = SetTargetCadence(self.client)
        self.stop_plan_msg = StopPlan(self.client)

        # Register callbacks for incoming messages.
        self._register_response_callbacks()

        # Maintain pairings: key: uuid_trainer, value: uuid_rider.
        self.pairings = {}

        # Use provided training plan or default.
        if training_plan is None:
            self.training_plan = [
                (0, 50, 90, "Warmup"),
                (60 * 2, 100, 80, "Interval"),
                (60 * 3, 50, 80, "Rest"),
                (60 * 4, 100, 80, "Interval"),
                (60 * 5, 50, 80, "Rest"),
                (60 * 6, 100, 80, "Interval"),
                (60 * 7, 50, 80, "Rest"),
                (60 * 10, 50, 85, "Cooldown"),
                (60 * 12, 0, 85, "stop"),  # End of session.
            ]
        else:
            self.training_plan = training_plan

        self.plan_thread = None
        self._plan_running = False

    def _register_response_callbacks(self):
        """
        Registers MQTT callbacks for incoming messages:
            - DeviceList: response for the ListDevices command.
            - GetPlan: a request for a training plan.
            - MeasuredPower: messages reporting measured power from trainers.
        """
        subscribe_topic = f"{APP_ID}/#"
        result, mid = self.client.subscribe(subscribe_topic)
        if result != mqtt.MQTT_ERR_SUCCESS:
            logger.error(f"Failed to subscribe to topic {subscribe_topic}: {mqtt.error_string(result)}")
        else:
            logger.info(f"Subscribed to topic {subscribe_topic}")
        

        topic_device_list = f"{APP_ID}/device_list"
        self.client.message_callback_add(topic_device_list, self._handle_device_list)

        topic_get_plan = f"{APP_ID}/get_plan"
        self.client.message_callback_add(topic_get_plan, self._handle_get_plan)

        topic_measured_power = f"{APP_ID}/set_measured_power"
        topic_measured_cadence = f"{APP_ID}/set_measured_cadence"
        self.client.message_callback_add(topic_measured_power, self._handle_measured_power)
        self.client.message_callback_add(topic_measured_cadence, self._handle_measured_cadence)
        self.client.loop_start()
        self.logger.info(
            "Coach registered response callbacks for device_list, get_plan, measured_power and measured_cadence."
        )
        
    # ----- Methods to generate outgoing messages -----
    def request_device_list(self):
        """Generates a ListDevices message to request the list of devices."""
        self.logger.info("Coach: Requesting device list.")
        self.list_devices_msg.publish()

    def pair_device(self, uuid_trainer, uuid_rider):
        """
        Generates a PairDevice message to pair a trainer with a rider,
        and stores the pairing.
        """
        self.logger.info(f"Coach: Pairing trainer {uuid_trainer} with rider {uuid_rider}.")
        self.pair_device_msg.publish(uuid_trainer=uuid_trainer, uuid_rider=uuid_rider)
        self.pairings[uuid_trainer] = uuid_rider
        
    def send_training_plan(self, training_plan):
        """
        Generates a SendPlan message with the provided training plan.
        The training_plan should be a list of tuples:
            (start_time_offset, target_power, target_cadence, description)
        """
        self.logger.info("Coach: Sending training plan.")
        self.send_plan_msg.publish(training_plan=training_plan)

    def set_ftp(self, uuid_trainer, ftp):
        """Generates a SetFTP message for a given trainer."""
        self.logger.info(f"Coach: Setting FTP for trainer {uuid_trainer} to {ftp}.")
        self.set_ftp_msg.publish(uuid_trainer=uuid_trainer, ftp=ftp)

    def start_plan(self):
        """
        Generates a StartPlan message and then begins executing the training plan
        for all paired devices (broadcast).
        """
        self.logger.info("Coach: Starting training plan.")
        self.start_plan_msg.publish()

        if not self.pairings:
            self.logger.warning("No paired devices found. Training plan will be broadcast to all devices.")

        self._plan_running = True
        if self.plan_thread is None or not self.plan_thread.is_alive():
            self.plan_thread = threading.Thread(target=self.run_training_plan, daemon=True)
            self.plan_thread.start()

    def run_training_plan(self):
        """
        Executes the training plan (broadcast to all paired devices).
        For each segment in the plan, sends a SetTargetPower message at the correct time offset.
        The loop checks periodically if a stop has been requested.
        After the plan is complete, sends a StopPlan message.
        """
        self.logger.info("Coach: Executing training plan (broadcast to all paired devices).")
        previous_offset = 0

        for segment in self.training_plan:
            if not self._plan_running:
                self.logger.info("Coach: Training plan interrupted.")
                return

            offset, target_power, target_cadence, description = segment
            delay = offset - previous_offset
            if delay > 0:
                slept = 0
                while slept < delay and self._plan_running:
                    time.sleep(1)
                    slept += 1
                if not self._plan_running:
                    self.logger.info("Coach: Training plan interrupted during delay.")
                    return

            self.logger.info(f"Coach: Segment '{description}': Broadcasting target power {target_power}%.")
            self.set_target_power(target_power)
            self.set_target_cadence(target_cadence)
            previous_offset = offset

        self.logger.info("Coach: Training plan complete. Sending stop plan command.")
        self.stop_plan()

    def set_target_power(self, target_power_percent):
        """
        Generates a SetTargetPower message (broadcast to all paired devices).
        target_power_percent is interpreted as a percentage.
        """
        self.logger.info(f"Coach: Broadcasting target power: {target_power_percent}%.")
        self.set_target_power_msg.publish(target_power=target_power_percent)

    def set_target_cadence(self, target_cadence):
        """
        Generates a SetTargetCadence message (broadcast to all paired devices).
        target_cadence_percent is interpreted as a percentage.
        """
        self.logger.info(f"Coach: Broadcasting target cadence: {target_cadence}.")
        self.set_target_cadence_msg.publish(target_cadence=target_cadence)

    def stop_plan(self):
        """
        Generates a StopPlan message to stop the training plan and interrupts
        any currently running training plan thread.
        """
        self.logger.info("Coach: Stopping training plan.")
        self.stop_plan_msg.publish()
        self._plan_running = False
        if self.plan_thread and self.plan_thread.is_alive():
            self.plan_thread.join(timeout=1)
            self.logger.info("Coach: Training plan thread has been stopped.")

    # ----- Callback Handlers for incoming messages -----
    def _handle_device_list(self, client, userdata, msg):
        """Handles a DeviceList response message."""
        try:
            payload = json.loads(msg.payload.decode())
            devices = payload.get("device_list", [])
            self.logger.info(f"Coach received device list: {devices}")
        except Exception as e:
            self.logger.error(f"Error processing device list: {e}")

    def _handle_get_plan(self, client, userdata, msg):
        """
        Handles a GetPlan request.
        When a trainer requests a training plan, the coach responds by sending the training plan.
        """
        self.logger.info("Coach received a GetPlan request.")
        self.send_training_plan(self.training_plan)

    def _handle_measured_power(self, client, userdata, msg):
        """
        Handles a MeasuredPower message (e.g., from a trainer).
        Logs the measured power for a given trainer.
        """
        try:
            payload = json.loads(msg.payload.decode())
            uuid_trainer = payload.get("uuid_trainer")
            measured_power = payload.get("measured_power")
            self.logger.info(f"Coach received measured power from trainer {uuid_trainer}: {measured_power} watts")
        except Exception as e:
            self.logger.error(f"Error processing measured power message: {e}")

    def _handle_measured_cadence(self, client, userdata, msg):
        """
        Handles a MeasuredPower message (e.g., from a trainer).
        Logs the measured power for a given trainer.
        """
        try:
            payload = json.loads(msg.payload.decode())
            uuid_trainer = payload.get("uuid_trainer")
            measured_cadence = payload.get("measured_cadence")
            self.logger.info(f"Coach received measured power from trainer {uuid_trainer}: {measured_cadence} RPM")
        except Exception as e:
            self.logger.error(f"Error processing measured cadence message: {e}")


