import sys
sys.path.append('/home/iamroot/.local/lib/python3.12/site-packages')

import asyncio
from bleak import BleakScanner, BleakClient

# Bluetooth UUIDs for Power, Cadence, and Speed characteristics
UUID_POWER = "00002a63-0000-1000-8000-00805f9b34fb"
UUID_CADENCE = "00002a5b-0000-1000-8000-00805f9b34fb"
UUID_SPEED = "00002a5b-0000-1000-8000-00805f9b34fb"


async def list_services(address):
    async with BleakClient(address) as client:
        if client.is_connected:
            print(f"Connected to {address}")
            services = await client.get_services()
            for service in services:
                print(f"[Service] {service}")
                for char in service.characteristics:
                    print(f"\t[Characteristic] {char} (Handle: {char.handle})")

async def main():
    devices = await BleakScanner.discover()
    wahoo_kickr = next((device for device in devices if 'KICKR' in device.name), None)
    
    if not wahoo_kickr:
        print("Wahoo KICKR not found!")
        return

    await list_services(wahoo_kickr.address)

if __name__ == "__main__":
    asyncio.run(main())

