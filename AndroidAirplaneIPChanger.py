from collections.abc import MutableSequence
from typing import Any, Optional
import subprocess
from pathlib import Path
from dataclasses import dataclass
import time
import json
from typing import Union, Dict
import os
import pprint

ADB_PATH = Path(next(x for x in os.environ['PATH'].split(';') if 'platform-tools' in x)).joinpath('adb.exe')

class AndroidAirplaneIPChanger():
    @dataclass
    class Device:
        device: str
        id: str

    def __init__(self, adb_path: Path):
        """
        Initializes the AndroidAirplaneIPChanger with the given adb path.
        
        :param adb_path: Path to the adb executable.
        :type adb_path: Path
        :raises ValueError: If adb_path does not exist or is not a file.
        """
        if not adb_path.exists() or not adb_path.is_file():
            raise ValueError("ADB doesn't exists")
        self.adb_path = adb_path
        self.current_device: Optional[AndroidAirplaneIPChanger.Device] = None
    
    def list_devices(self) -> MutableSequence[Device]:
        """
        Lists all connected devices by USB.

        :return: A list of Device objects representing the connected devices.
        :rtype: MutableSequence[Device]
        """
        result = subprocess.run([str(self.adb_path.absolute()), "devices", "-l"], stdout=subprocess.PIPE, encoding='utf-8')
        ids: MutableSequence[AndroidAirplaneIPChanger.Device] = []
        for line in result.stdout.removeprefix('List of devices attached\n').splitlines():
            id = line[:line.find(' ')]
            if not id:
                continue
            delimeter_pos = line.find(":")
            device = line[delimeter_pos+1:line.find(" ", delimeter_pos)]
            ids.append(AndroidAirplaneIPChanger.Device(device, id))
        return ids

    def set_device(self, device: Device):
        """
        Sets the current device.

        :param device: The device to set as the current device.
        :type device: Device
        """
        self.current_device = device
        return self

    def get_device(self):
        """
        Gets the current device.

        :return: The current device.
        :rtype: Device
        """
        return self.current_device
    
    def check_airplane_mode(self):
        """
        Checks if airplane mode is enabled on the current device.

        :return: True if airplane mode is enabled, False otherwise.
        :rtype: bool
        :raises ValueError: If no current device is set.
        """
        if self.current_device is None:
            raise ValueError("Need init current device!")
        
        result = subprocess.run([str(self.adb_path.absolute()), '-s', self.current_device.id, 'shell', 'cmd', 'connectivity', 'airplane-mode'], stdout=subprocess.PIPE, encoding='utf-8')
        if result.stdout == 'Enable':
            return True
        return False

    def enable_airplane_mode(self):
        """
        Enables airplane mode on the current device.

        :raises ValueError: If no current device is set.
        """
        if self.current_device is None:
            raise ValueError("Need init current device!")
        
        subprocess.run([str(self.adb_path.absolute()), '-s', self.current_device.id, 
                        'shell', 'cmd', 'connectivity', 'airplane-mode', 'enable'])

    def disable_airplane_mode(self):
        """
        Disables airplane mode on the current device.

        :raises ValueError: If no current device is set.
        """
        if self.current_device is None:
            raise ValueError("Need init current device!")
        
        subprocess.run([str(self.adb_path.absolute()), '-s', self.current_device.id, 
                        'shell', 'cmd', 'connectivity', 'airplane-mode', 'disable'])

    def ping(self):
        """
        Pings www.google.com to check if the internet is working on the current device.

        :return: True if the ping is successful, False otherwise.
        :rtype: bool
        :raises ValueError: If no current device is set.
        """
        if self.current_device is None:
            raise ValueError("Need init current device!")
        
        result = subprocess.run([str(self.adb_path.absolute()), '-s', self.current_device.id,
                         'shell', 'ping', '-c', '4', '-w', '10', 'www.google.com'])

        if result.returncode == 0:
            return True
        return False

    def get_current_ip(self, location: bool=False) -> str | Dict[str, Any]:
        """
        Gets the current IP address of the current device by HTTP request to ipify.
        
        :param location: If True, returns the full IP location information as a dictionary.
                         If False, returns just the IP address as a string.
        :return: The current IP address as a string or IP location address as a dictionary in JSON format.
        :rtype: Union[str, dict]
        :raises ValueError: If no current device is set.
        """
        if self.current_device is None:
            raise ValueError("Need init current device!")

        ip_json = json.loads(subprocess.run([str(self.adb_path.absolute()), '-s', self.current_device.id,
                                'shell', 'curl', '-s', 'ip-api.com/json/'], stdout=subprocess.PIPE, encoding='utf-8').stdout)
        if location:
            return ip_json

        return ip_json['query']
    
    def set_default_device(self):
        """
        Sets the first connected device as the current device.

        :raises ValueError: If no devices are connected.
        """
        devices = self.list_devices()
        if not devices:
            raise ValueError("Devices not connected!")
        self.current_device = devices[0]
        return self

    def change_ip(self):
        """
        Changes the IP address of the current device by toggling airplane mode.

        :return: True if the IP address was changed, False otherwise.
        :rtype: bool
        :raises RuntimeError: If the internet is not working on the device.
        :raises ValueError: If no current device is set.
        """
        if not self.ping():
            raise RuntimeError("Internet on mobile don't work!")
        prev_ip = self.get_current_ip()

        self.enable_airplane_mode()
        time.sleep(5)
        self.disable_airplane_mode()
        time.sleep(10) #waiting for mobile get internet connection

        if not self.ping():
            raise RuntimeError("Internet on mobile don't work!")
        if self.get_current_ip() == prev_ip:
            return False
        return True

    def port_forward(self, port_from, port_to):
        if self.current_device is None:
            raise ValueError("Need init current device!")
        
        result = subprocess.run([str(self.adb_path.absolute()), '-s', self.current_device.id,
                         'forward', f'tcp:{port_from}', f'tcp:{port_to}'])
    
if __name__ == '__main__':
    import datetime
    changer = AndroidAirplaneIPChanger(ADB_PATH)
    changer.set_default_device()
    while True:
        current_android_ip = changer.get_current_ip(location=True)
        print(f"Current android IP:")
        pprint.pprint(current_android_ip)
        input(f"Do you want change your IP? (Press ENTER or exit from programm)")
        if changer.change_ip():
            print(f"\033[32mIP changed succesfull\033[0m {datetime.datetime.now().time()}")
        else:
            print(f"\033[31mIP didn't changed\033[0m {datetime.datetime.now().time()}")