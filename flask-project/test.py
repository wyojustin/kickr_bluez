import sys
sys.path.append('/home/iamroot/.local/lib/python3.12/site-packages')

from bluepy3 import btle

class KickrDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        print(f"Notification from handle: {cHandle}, data: {data.hex()}")

def connect_to_kickr(device_address):
    try:
        print(f"Connecting to {device_address}")
        dev = btle.Peripheral(device_address)
        dev.setDelegate(KickrDelegate())

        # Discover services and characteristics
        services = dev.getServices()
        for service in services:
            print(f"Service UUID: {service.uuid}")
            for char in service.getCharacteristics():
                print(f"  Characteristic UUID: {char.uuid}")

        # Subscribe to notifications
        power_char = dev.getCharacteristics(uuid="00002a63-0000-1000-8000-00805f9b34fb")[0]
        cadence_char = dev.getCharacteristics(uuid="00002a5b-0000-1000-8000-00805f9b34fb")[0]
        speed_char = dev.getCharacteristics(uuid="00002a5d-0000-1000-8000-00805f9b34fb")[0]

        dev.writeCharacteristic(power_char.getHandle() + 1, b'\x01\x00')
        dev.writeCharacteristic(cadence_char.getHandle() + 1, b'\x01\x00')
        dev.writeCharacteristic(speed_char.getHandle() + 1, b'\x01\x00')

        while True:
            if dev.waitForNotifications(1.0):
                continue

            print("Waiting for notifications...")

        dev.disconnect()
        print("Disconnected successfully.")
     
    except btle.BTLEException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Replace with your KICKR trainer's MAC address
    device_address = "dc:ac:b5:95:ab:1f"
    device_address = "e8:fe:60:9b:ac:1c"
    connect_to_kickr(device_address)
