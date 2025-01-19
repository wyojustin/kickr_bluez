import sys
sys.path.append('/home/iamroot/.local/lib/python3.12/site-packages')

import asyncio
import struct
from bleak import BleakClient



KICKR_MAC_ADDRESS = "e8:fe:60:9b:ac:1c"
KICKR_MAC_ADDRESS = "E8:FE:60:9B:AC:1C"
UUID_POWER = "00002a63-0000-1000-8000-00805f9b34fb"  # Example UUID for Power

async def handle_power_data(sender: int, data: bytearray):
    # Assuming each element in the data is 2 bytes (16 bits)
    power, cadence, speed = struct.unpack('<HHH', data)
    
    # Assuming speed is in 0.01 m/s units
    speed = speed / 100.0
    
    print(f"Power: {power} watts")
    print(f"Cadence: {cadence} RPM")
    print(f"Speed: {speed} m/s")

async def connect_and_subscribe(address):
    print(f"Attempting to connect to {address}")
    async with BleakClient(address) as client:
        try:
            await client.connect()
            print("Connected to Wahoo KICKR")

            print("Starting notifications...")
            await client.start_notify(UUID_POWER, handle_power_data)
            print("Notifications started")

            await asyncio.sleep(60)  # Increased timeout to 60 seconds

            print("Stopping notifications...")
            await client.stop_notify(UUID_POWER)
            print("Notifications stopped")

        except asyncio.CancelledError:
            print("Service discovery was cancelled. Retrying...")
        except Exception as e:
            print(f"An error occurred: {e}")

async def main():
    await connect_and_subscribe(KICKR_MAC_ADDRESS)

if __name__ == "__main__":
    asyncio.run(main())

