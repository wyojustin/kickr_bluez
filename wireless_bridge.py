import time
import threading
import random  # For simulating power readings
import json
import logging

# Import the messaging functions from the mqtt_service sub-package.
from mqtt_service.messaging import (
    SetMeasuredPower,
    DeviceList,
)
# Import APP_ID from the constants module.
from mqtt_service.constants import APP_ID

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
        self.device_list_msg = DeviceList(self.client)

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
        topic_list_devices = f"{APP_ID}/list_devices"
        self.client.message_callback_add(topic_list_devices, self._handle_list_devices)

        topic_pair_device = f"{APP_ID}/pair_device"
        self.client.message_callback_add(topic_pair_device, self._handle_pair_device)

        topic_set_ftp = f"{APP_ID}/set_ftp"
        self.client.message_callback_add(topic_set_ftp, self._handle_set_ftp)

        topic_set_target_power = f"{APP_ID}/set_target_power"
        self.client.message_callback_add(topic_set_target_power, self._handle_set_target_power)

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
                try:
                    # Use the pre-created SetMeasuredPower message object.
                    self.set_measured_power_msg.publish(
                        uuid_trainer=trainer_id,
                        measured_power=measured_power
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
        return random.randint(100, 400)

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

    def _handle_set_target_power(self, client, userdata, msg):
        """
        Responds to a set_target_power command.
        Expects a payload containing 'uuid_trainer' and 'target_power' (as a percent).
        """
        self.logger.info("Received set_target_power command")
        try:
            data = json.loads(msg.payload.decode())
            uuid_trainer = data.get("uuid_trainer")
            target_power = data.get("target_power")
            if uuid_trainer is None or target_power is None:
                self.logger.error("set_target_power payload missing required fields.")
                return

            self.logger.info(f"Setting target power for trainer {uuid_trainer} to {target_power}%")
            # Use the stored FTP value if available; default to 100 if not.
            ftp = self.ftps.get(uuid_trainer, 100)
            # Compute the target watts: interpret target_power as a percent.
            watts = ftp * target_power / 100
            # Call our helper method to process the target power command.
            self._set_target_power(uuid_trainer, watts)
        except Exception as e:
            self.logger.error(f"Error handling set_target_power command: {e}")

    def _set_target_power(self, uuid_trainer, watts):
        """
        Helper method to log the target power setting.
        (The actual target power publishing is not re-broadcast to avoid recursion.)
        """
        self.logger.info(f"Setting target power for trainer {uuid_trainer} to {watts} watts")
        # You could add code here to perform further actions if required.

# ---------------------------
# Example usage:
# ---------------------------
if __name__ == "__main__":
    import paho.mqtt.client as mqtt
    # Import constants from the mqtt_service package.
    from mqtt_service.constants import hostname, APP_ID

    # Set up basic logging.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logging.info(f"hostname: {hostname}, APP_ID: {APP_ID}")

    # Create an MQTT client (using Callback API version 2 to avoid deprecation warnings).
    client = mqtt.Client(
        client_id="",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )

    # Global fallback callback for topics without a specific registered callback.
    def on_message(client, userdata, msg):
        logging.info(f"Global on_message: Received message on topic {msg.topic}: {msg.payload.decode()}")

    client.on_message = on_message

    # Connect to the MQTT broker.
    client.connect(hostname)
    # Subscribe to all topics under the APP_ID.
    subscribe_topic = f"{APP_ID}/#"
    client.subscribe(subscribe_topic)
    client.loop_start()

    # Create and start the WirelessBridge.
    bridge = WirelessBridge(client)
    bridge.start()

    # Give the bridge some time to start polling.
    time.sleep(2)

    # --- Publish test commands to trigger the callbacks ---
    # Test list_devices command.
    client.publish(f"{APP_ID}/list_devices", "{}")
    time.sleep(1)

    # Test pair_device command.
    pair_payload = json.dumps({"uuid_trainer": "trainer_123", "uuid_rider": "rider_456"})
    client.publish(f"{APP_ID}/pair_device", pair_payload)
    time.sleep(1)

    # Test set_ftp command.
    ftp_payload = json.dumps({"uuid_trainer": "trainer_789", "ftp": 300})
    client.publish(f"{APP_ID}/set_ftp", ftp_payload)
    time.sleep(1)

    # Test set_target_power command with target_power as a percent.
    target_power_payload = json.dumps({"uuid_trainer": "trainer_123", "target_power": 90})
    client.publish(f"{APP_ID}/set_target_power", target_power_payload)
    time.sleep(2)

    try:
        # Let the bridge continue running for a few more seconds to observe polling.
        time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop()
        client.loop_stop()
        client.disconnect()
