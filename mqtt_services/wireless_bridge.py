import time
import threading
import random  # For simulating power readings
import json
import logging
import paho.mqtt.client as mqtt

# Import the messaging functions from the mqtt_service sub-package.
from .messaging import (
    SetMeasuredPower,
    SetMeasuredCadence,
    DeviceList,
    SendFTP
)
# Import APP_ID from the constants module.
from .constants import APP_ID

class WirelessBridge:
    """
    The WirelessBridge class polls all connected trainers via Bluetooth/ANT+ (stubbed out)
    once per second and publishes the current output power levels to the MQTT backbone.
    It also responds to MQTT commands: list_devices, pair_device, set_ftp, and set_target_power.
    """

    def __init__(self, mqtt_client, trainer_ids=None):
        """
        Initializes the WirelessBridge.

        Parameters:
            mqtt_client (mqtt.Client): The MQTT client instance to use for publishing and subscribing.
            trainer_ids (list, optional): A list of trainer UUIDs that are connected to the bridge.
                                          If None, the bridge will attempt to discover trainers.
        """
        self.client = mqtt_client

        # Initialize logger before calling _discover_trainers.
        self.logger = logging.getLogger(self.__class__.__name__)
        # Register command callbacks.
        self._register_command_callbacks()

        # If no trainer_ids are provided, attempt to discover them.
        if trainer_ids is None:
            self.trainer_ids = self._discover_trainers()
        else:
            self.trainer_ids = trainer_ids

        # Create messaging objects once in __init__
        self.set_measured_power_msg = SetMeasuredPower(self.client)
        self.set_measured_cadence_msg = SetMeasuredCadence(self.client)
        self.device_list_msg = DeviceList(self.client)
        self.reply_ftp_msg = SendFTP(self.client)

        self._running = False
        self._thread = None

        # Dictionaries to keep pairing and FTP data.
        self.pairings = {}  # key: uuid_trainer, value: uuid_rider
        self.ftps = {}      # key: uuid_trainer, value: ftp

        self.logger.info(f"Initialized WirelessBridge with trainers: {self.trainer_ids}")

    def _register_command_callbacks(self):
        """
        Registers MQTT callbacks for the following command topics:
            - list_devices
            - pair_device
            - set_ftp
            - set_target_power
        The topics use the hierarchical naming convention: <APP_ID>/<command_topic>.
        """

        subscribe_topic = f"{APP_ID}/#"
        result, mid = self.client.subscribe(subscribe_topic)
        if result != mqtt.MQTT_ERR_SUCCESS:
            self.logger.error(f"Failed to subscribe to topic {subscribe_topic}: {mqtt.error_string(result)}")
        else:
            self.logger.info(f"Subscribed to topic {subscribe_topic}")

        topic_list_devices = f"{APP_ID}/list_devices"
        self.client.message_callback_add(topic_list_devices, self._handle_list_devices)

        topic_pair_device = f"{APP_ID}/pair_device"
        self.client.message_callback_add(topic_pair_device, self._handle_pair_device)

        topic_set_ftp = f"{APP_ID}/set_ftp"
        self.client.message_callback_add(topic_set_ftp, self._handle_set_ftp)

        topic_set_target_power = f"{APP_ID}/set_target_power"
        self.client.message_callback_add(topic_set_target_power, self._handle_set_target_power)
        self.client.loop_start()
        self.logger.info("Registered command callbacks for list_devices, pair_device, set_ftp, and set_target_power.")

    def _discover_trainers(self):
        """
        Stubbed out discovery function for trainers.
        In a production implementation, this method would scan for available trainers via Bluetooth/ANT+.

        Returns:
            list: A list of discovered trainer UUIDs.
        """
        # For demonstration purposes, return a simulated list of trainer IDs.
        simulated_trainers = ["trainer_123", "trainer_456", "trainer_789"]
        self.logger.info("Discovered trainers: " + ", ".join(simulated_trainers))
        return simulated_trainers

    def start(self):
        """Starts the polling loop in a separate thread."""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._poll_trainers, daemon=True)
            self._thread.start()
            self.logger.info("WirelessBridge started polling trainers.")
        else:
            self.logger.warning("WirelessBridge is already running.")

    def stop(self):
        """Stops the polling loop and waits for the thread to finish."""
        if self._running:
            self._running = False
            if self._thread:
                self._thread.join()
            self.logger.info("WirelessBridge stopped polling trainers.")
        else:
            self.logger.warning("WirelessBridge is not running.")

    def _poll_trainers(self):
        """
        Polls all connected trainers once per second.
        For each trainer, obtains the measured power (via a placeholder function)
        and publishes the measurement via the MQTT messaging protocol.
        """
        while self._running:
            for trainer_id in self.trainer_ids:
                measured_power = self._read_trainer_power(trainer_id)
                measured_cadence = self._read_trainer_cadence(trainer_id)
                percent_ftp = int(100 * measured_power / self.ftps.get(trainer_id, 100))
                try:
                    # Use the pre-created SetMeasuredPower message object.
                    self.set_measured_power_msg.publish(
                        uuid_trainer=trainer_id,
                        measured_power=measured_power,
                        percent_ftp=percent_ftp
                    )
                    self.logger.debug(f"Published measured power for {trainer_id}: {measured_power}")
                except Exception as e:
                    self.logger.error(f"Error publishing measured power for {trainer_id}: {e}")
            time.sleep(1)

    def _read_trainer_power(self, trainer_id):
        """
        Placeholder for the Bluetooth/ANT+ function that reads the trainer's output power.
        This function should be replaced with the actual implementation to query the trainer.

        Parameters:
            trainer_id (str): The unique identifier of the trainer.

        Returns:
            int: The simulated measured power.
        """
        # Simulate a measured power reading as a random integer between 100 and 400 watts.
        return random.randint(90, 110)

    def _read_trainer_cadence(self, trainer_id):
        """
        Placeholder for the Bluetooth/ANT+ function that reads the trainer's output cadence.
        This function should be replaced with the actual implementation to query the trainer.

        Parameters:
            trainer_id (str): The unique identifier of the trainer.

        Returns:
            int: The simulated measured cadence.
        """
        # Simulate a measured cadence reading as a random integer between 85 and 95 RPM.
        return random.randint(80, 95)

    # ---------------------------
    # MQTT Command Handler Methods
    # ---------------------------
    def _handle_list_devices(self, client, userdata, msg):
        """
        Responds to a list_devices command.
        Publishes the list of discovered trainer IDs using the DeviceList messaging interface.
        """
        self.logger.info("Received list_devices command")
        try:
            self.device_list_msg.publish(device_list=self.trainer_ids)
            self.logger.info("Responded with device list")
        except Exception as e:
            self.logger.error(f"Error responding to list_devices: {e}")

    def _handle_pair_device(self, client, userdata, msg):
        """
        Responds to a pair_device command.
        Expects a payload containing 'uuid_trainer' and 'uuid_rider'.
        """
        self.logger.info("Received pair_device command")
        try:
            data = json.loads(msg.payload.decode())
            uuid_trainer = data.get("uuid_trainer")
            uuid_rider = data.get("uuid_rider")
            self.logger.info(f"Pairing trainer {uuid_trainer} with rider {uuid_rider}")
            # Save the pairing locally.
            self.pairings[uuid_trainer] = uuid_rider
        except Exception as e:
            self.logger.error(f"Error handling pair_device command: {e}")

    def _handle_set_ftp(self, client, userdata, msg):
        """
        Responds to a set_ftp command.
        Expects a payload containing 'uuid_trainer' and 'ftp'.
        """
        self.logger.info("Received set_ftp command")
        try:
            data = json.loads(msg.payload.decode())
            uuid_trainer = data.get("uuid_trainer")
            ftp = data.get("ftp")
            self.logger.info(f"Setting FTP for trainer {uuid_trainer} to {ftp}")
            # Save the FTP value.
            self.ftps[uuid_trainer] = ftp
        except Exception as e:
            self.logger.error(f"Error handling set_ftp command: {e}")

    def _handle_request_ftp(self, client, userdata, msg):
        """
        Responds to a request_ftp command.
        Expects a payload containing 'uuid_trainer'.
        """
        self.logger.info("Received request_ftp command")
        try:
            data = json.loads(msg.payload.decode())
            uuid_trainer = data.get("uuid_trainer")
            self.logger.info(f"Got an FTP request for trainer {uuid_trainer}")
            # send the FTP value.
            ftp = self.ftps.get(uuid_trainer, 100)
            self.send_ftp(ftp)
        except Exception as e:
            self.logger.error(f"Error handling set_ftp command: {e}")

    def _handle_set_target_power(self, client, userdata, msg):
        """
        Responds to a set_target_power command.
        Expects a payload containing 'uuid_trainer' and 'target_power' (as a percent).
        """
        self.logger.info("Received set_target_power command")
        try:
            data = json.loads(msg.payload.decode())
            target_power = data.get("target_power")
            if uuid_trainer is None or target_power is None:
                self.logger.error("set_target_power payload missing required fields.")
                return

            self.logger.info(f"Setting target power to {target_power}%")
            if False:
                for uuid_trainer in self.ftps:
                    ftp = self.ftps[uuid_trainer]
                    # Compute the target watts: interpret target_power as a percent.
                    watts = ftp * target_power / 100
            # Call our helper method to process the target power command.
            self._set_target_power(uuid_trainer, target_power)
        except Exception as e:
            self.logger.error(f"Error handling set_target_power command: {e}")

    def _set_target_power(self, uuid_trainer, watts):
        """
        Helper method to log the target power setting.
        (The actual target power publishing is not re-broadcast to avoid recursion.)
        """
        self.logger.info(f"Setting target power for trainer {uuid_trainer} to {watts} watts")
        # You could add code here to perform further actions if required.

