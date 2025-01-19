import bluetooth

def get_devices():
    output = bluethooth.hci_info()
    
    devices = [line.split(':')[1].strip() for line in output.decode('utf-8').split('\n') if 'HCID' in line]
    
    return devices


def main():
	print(get_device())

if __name__ == "__main__":
    main()


