#!/usr/bin/env python3
"""
integrated_test.py

This script runs an integrated test of three agents:
  - Coach
  - Rider
  - WirelessBridge

Each agent is run in its own thread with its own MQTT client.
They interact via MQTT messages on the common broker (hostname) using the APP_ID namespace.
"""

import time
import threading
import logging
import paho.mqtt.client as mqtt

# Import agent classes.
from coach import Coach
from rider import Rider
from wireless_bridge import WirelessBridge
from mqtt_service.constants import APP_ID, hostname

# Configure logging.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IntegratedTest")

# ----- Define functions to run each agent -----
def run_coach():
    logger.info("Starting Coach agent...")
    coach = Coach(coach_client)
    time.sleep(2)
    coach.request_device_list()
    time.sleep(2)
    # Start a training plan.
    coach.start_plan()
    # Let the training plan run for a while, then stop it.
    time.sleep(20)
    coach.stop_plan()
    logger.info("Coach agent finished.")

def run_rider():
    logger.info("Starting Rider agent...")
    rider = Rider(rider_client)
    time.sleep(3)
    rider.request_device_list()
    time.sleep(1)
    rider.pair_device("trainer_123", "rider_001")
    time.sleep(1)
    rider.set_ftp("trainer_123", 300)
    time.sleep(1)
    rider.request_training_plan()
    # Let the rider run and process incoming messages.
    time.sleep(25)
    logger.info("Rider agent finished.")

def run_wireless_bridge():
    logger.info("Starting WirelessBridge agent...")
    wb = WirelessBridge(wb_client)
    wb.start()
    # Let the WirelessBridge simulate polling & measured power for a while.
    time.sleep(30)
    wb.stop()
    logger.info("WirelessBridge agent finished.")

# ----- Create separate MQTT client instances for each agent -----
coach_client = mqtt.Client(client_id="coach", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
rider_client = mqtt.Client(client_id="rider", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
wb_client = mqtt.Client(client_id="wireless_bridge", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

# Connect and subscribe each client.
for client in [coach_client, rider_client, wb_client]:
    client.connect(hostname)
    client.subscribe(f"{APP_ID}/#")
    client.loop_start()

# ----- Start each agent in its own thread -----
coach_thread = threading.Thread(target=run_coach)
rider_thread = threading.Thread(target=run_rider)
wb_thread = threading.Thread(target=run_wireless_bridge)

coach_thread.start()
rider_thread.start()
wb_thread.start()

# Wait for all threads to complete.
coach_thread.join()
rider_thread.join()
wb_thread.join()

# ----- Clean up MQTT clients -----
for client in [coach_client, rider_client, wb_client]:
    client.loop_stop()
    client.disconnect()

logger.info("Integrated test complete.")
