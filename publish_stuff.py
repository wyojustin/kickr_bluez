from mqtt_services import messaging
from mqtt_services.constants import *
import paho.mqtt.client as mqtt


client = mqtt.Client(client_id="coach", protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.connect(hostname)

dl_msg = messaging.DeviceList(client)
mp_msg = messaging.SetMeasuredPower(client)
tp_msg = messaging.SetTargetPower(client)
tc_msg = messaging.SetTargetCadence(client)
mc_msg = messaging.SetMeasuredCadence(client)

start_plan_msg = messaging.StartPlan(client)
start_plan_msg.publish()
tp_msg.publish(target_power=100)

if False:
    set_ftp_msg = messaging.SetFTP(client)
    dl_msg.publish(**{"device_list": ["trainer_123", "trainer_456", "trainer_789"]})
    set_ftp_msg.publish(uuid_trainer="trainer_123", ftp=200)
    tp_msg.publish(target_power=100)
    mp_msg.publish(uuid_trainer="trainer_123", measured_power=200, percent_ftp=100)
    tc_msg.publish(target_cadence=85)
    mc_msg.publish(uuid_trainer = "trainer_123", measured_cadence=55)
    mc_msg.publish(uuid_trainer = "trainer_123", measured_cadence=86)


