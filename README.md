# Default using
This doesn't take into account giving out internet via USB modem, as I use PdaNet.
```
device = AndroidAirplaneIPChanger(Path('adb.exe'))
device.set_default_device()
print(device.get_current_ip())
device.change_ip()
print(device.get_current_ip())
```
