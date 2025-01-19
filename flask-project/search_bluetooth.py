import sys
sys.path.append('/home/iamroot/.local/lib/python3.12/site-packages')

import asyncio
from bleak import BleakScanner

async def search_kickr():
    # Discover all BLE devices
    devices = await BleakScanner.discover()

    # Print all discovered devices
    for device in devices:
        print(f"Name: {device.name}, Address: {device.address}")

    # Filter to find the Wahoo KICKR
    wahoo_kickr = next((device for device in devices if 'KICKR' in device.name), None)

    if wahoo_kickr:
        print(f"Wahoo KICKR found! MAC Address: {wahoo_kickr.address}")
    else:
        print("Wahoo KICKR not found!")

if __name__ == "__main__":
    asyncio.run(search_kickr())

