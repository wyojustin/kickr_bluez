import bluetooth
import antprotocol as antprotol
from threading import Thread, Lock
import json

class KickrTrainer:
    def __init__(self):
        self.bluetooth_lock = Lock()
        self.ant_lock = Lock()
        self.devices_connected = {}
        
    def search_devices(self):
        # Search for Bluetooth devices using hciconfig and hcitool commands
        print("Searching for Bluetooth devices...")
        output = subprocess.check_output(['hciconfig', '--list'])
        bluetooth_devices = [line.split(':')[1].strip() for line in output.decode('utf-8').split('\n') if 'HCID' in line]
        
        # Convert hcitool output to a list of device addresses
        self.bluetooth_devices = []
        for device in bluetooth_devices:
            address, name = device.split(',')
            self.bluetooth_devices.append((address, name))
            
    def connect_to_kickr(self, address):
        # Connect to Kickr trainer using Bluetooth
        print("Connecting to Kickr trainer...")
        
        if isinstance(address, tuple):  # ANT protocol address format: (xx-xxxx)
            ant_client = antprotol.AntClient(address[0])
            
            try:
                ant_client.connect()
                print("Connected to Kickr trainer")
                
                return None
            except Exception as e:
                print(f"Error: {e}")
        
        # Bluetooth connection logic remains the same for now
        
    def connect_to_kickr_ant(self, address):
        # Connect to Kickr trainer using ANT protocol
        with self.ant_lock:
            print("Connecting to Kickr trainer...")
            
            try:
                ant_client = antprotol.AntClient(address)
                
                if not ant_client.connect():
                    raise Exception('Could not connect')
                    
                return ant_client
            except Exception as e:
                print(f"Error: {e}")
        
    def set_power(self, client_socket):
        # Set power on the Kickr trainer using Bluetooth
        with self.bluetooth_lock:
            if isinstance(client_socket, bluetooth.BluetoothSocket):
                data = bytes([0x20])  # Power command ( ANT )
                
                try:
                    client_socket.send(data)
                    print("Power set to maximum")
                    
                except Exception as e:
                    print(f"Error: {e}")
                    
    def read_data(self, ant_client):
        # Read cycling cadence, power, speed, and heart rate from the Kickr trainer using ANT protocol
        with self.ant_lock:
            data = ant_client.read()
            
            if not data:
                return None
            
            response = json.loads(data.decode('utf-8'))
            
            print(f"Cadence: {response['Cadence']}")
            print(f"Power: {response['Power']}W")
            
    def set_kickr_power(self, client_socket):
        # Set power on the Kickr trainer using Bluetooth
        with self.bluetooth_lock:
            if isinstance(client_socket, bluetooth.BluetoothSocket):
                data = bytes([0x21])  # Power command ( ANT )
                
                try:
                    client_socket.send(data)
                    print("Power set to minimum")
                    
                except Exception as e:
                    print(f"Error: {e}")
                    
    def manage_kickr_messages(self, ant_client):
        while True:
            data = ant_client.read()
            
            if not data:
                break
            
            response = json.loads(data.decode('utf-8'))
            
            # Handle ANT protocol messages
            pass
    
    def run(self):
        self.search_devices()
        
        kickr_thread = Thread(target=self.manage_kickr_messages, args=(None,))
        
        while True:
            time.sleep(1)
            
            if 'KickrTrainer' in os.environ and 'KICKR_TRAINER_ADDR' in os.environ:
                address = os.environ['KICKR_TRAINER_ADDR']
                
                kickr_thread.start()
                
                break
