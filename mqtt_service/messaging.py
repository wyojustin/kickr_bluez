'''
Create messaging service for controlling a power based cycle trainer
'''
import time
import json
import numpy as np
import paho.mqtt.client as mqtt
import logging

from constants import hostname

# Set up logging for the module.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

APP_ID = 'UniqueAppID_for_training_sessions'
logging.info(f'hostname:{hostname}, APP_ID:{APP_ID}')
class MQTT_MessageType:
    def __init__(self, client, topic, arg_names=()):
        """
        Initializes the MQTT message type.

        Parameters:
            client (mqtt.Client): An instance of the MQTT client that will be used for publishing.
            topic (str): The base topic name.
            arg_names (tuple or str): A tuple of argument names required for the message.
                                      If a single string is provided, it is converted to a tuple.
        """
        self.client = client
        if isinstance(arg_names, str):
            arg_names = (arg_names,)
        # Use hierarchical topic naming with slashes.
        self.topic = f'{APP_ID}/{topic}'
        self.arg_names = arg_names

    def publish(self, **kw):
        # Validate that all required arguments are provided.
        for name in self.arg_names:
            if name not in kw:
                raise ValueError(f"Missing required argument: {name}")
        # Optionally validate that no unexpected arguments are provided.
        for key in kw:
            if key not in self.arg_names:
                raise ValueError(f"Unexpected argument: {key}")
        
        # Add a timestamp to the message.
        kw['time'] = np.datetime64('now', 's').astype(str)
        
        # Serialize the payload.
        payload = json.dumps(kw)
        
        # Publish using the stored MQTT client.
        result = self.client.publish(self.topic, payload)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logging.error(f"Failed to publish message to {self.topic}: {mqtt.error_string(result.rc)}")
        else:
            logging.info(f"Published message to {self.topic}: {payload}")

# Message type definitions now require the client instance.
def ListDevices(client):
    return MQTT_MessageType(client, 'list_devices')

def DeviceList(client):
    return MQTT_MessageType(client, 'device_list', arg_names='device_list')

def PairDevice(client):
    """Pair a trainer with a rider dashboard.
       If uuid_rider_dashboard is None, it unpairs the trainer.
    """
    return MQTT_MessageType(client, 'pair_trainer_rider', arg_names=('uuid_trainer', 'uuid_rider'))

def GetPlan(client):
    return MQTT_MessageType(client, 'get_plan')

def SendPlan(client):
    return MQTT_MessageType(client, 'list_plan', arg_names='training_plan')

def SetFTP(client):
    return MQTT_MessageType(client, 'set_ftp', arg_names=('uuid_trainer', 'ftp'))

def StartPlan(client):
    return MQTT_MessageType(client, 'start_plan')

def StopPlan(client):
    return MQTT_MessageType(client, 'stop_plan')

def SetTargetPower(client):
    return MQTT_MessageType(client, 'set_target_power', arg_names=('uuid_trainer', 'target_power'))
    
def SetMeasuredPower(client):
    return MQTT_MessageType(client, 'set_measured_power', arg_names=('uuid_trainer', 'measured_power'))

# Callback function for received messages.
def on_message(client, userdata, msg):
    logging.info(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

def main():
    # Create a single MQTT client instance using MQTTv311 and Callback API version 2 to avoid deprecation warnings.
    client = mqtt.Client(
        client_id="",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    
    # Set up the message callback.
    client.on_message = on_message

    try:
        # Connect to the MQTT broker.
        client.connect(hostname)
    except Exception as e:
        logging.error(f"Failed to connect to MQTT broker at {hostname}: {e}")
        return

    # Subscribe to all topics for this application using the hierarchical topic structure.
    subscribe_topic = f"{APP_ID}/#"
    result, mid = client.subscribe(subscribe_topic)
    if result != mqtt.MQTT_ERR_SUCCESS:
        logging.error(f"Failed to subscribe to topic {subscribe_topic}: {mqtt.error_string(result)}")
    else:
        logging.info(f"Subscribed to topic {subscribe_topic}")

    # Start the network loop in a separate thread.
    client.loop_start()

    # Example usage: publishing a 'ListDevices' message.
    list_devices_msg = ListDevices(client)
    list_devices_msg.publish()  # No additional arguments required.

    # Example usage: publishing a 'PairDevice' message.
    pair_device_msg = PairDevice(client)
    pair_device_msg.publish(uuid_trainer='trainer_123', uuid_rider='rider_456')

    # Allow some time to process and receive messages.
    time.sleep(5)

    # Clean up: stop the loop and disconnect.
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()
