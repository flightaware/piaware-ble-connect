# piaware-ble-connect

piaware-ble-connect is a Bluetooth Low Energy (BLE) service that runs on PiAware 7+ SD card images. This service allows you to connect to your receiver and configure WiFi from the [FlightAware website](https://flightaware.com/adsb/piaware/build/configure) on a supported Web browser or the FlightAware iOS app. It makes requests to [piaware-configurator](https://github.com/flightaware/piaware-configurator) to configure the WiFi settings.

## Details
- piaware-ble-connect will allow your PiAware to be discoverable over BLE if 1) your PiAware cannot connect to the Internet AND 2) your
PiAware is unclaimed. If these two conditions are met, BLE discovery is disabled. It will remain disabled on all subsequent reboots unless PiAware cannot connect to the Internet for some reason, in which case BLE pairing will be re-enabled to allow for reconfiguration.

- piaware-ble-connect will remain active for a maximum of 15 minutes before shutting down. You must reboot to re-enable the BLE services.

- To disable BLE setup completely, you can set the “allow-ble-setup” piaware-config setting to “no” and reboot.


## allow-ble-setup
This piaware-config setting allows you to enable/disable the piaware-ble-connect service at boot up. 

`auto` - Default setting on new SD cards. If set to `auto` and WiFi has not been configured, piaware-ble-connect will be enabled to allow for configuration. If set to `auto` and WiFi has been configured via other means (e.g piaware-config), BLE will be disabled. You should continue to use the method you previously used to set WiFi. If WiFi has been set up via BLE, `allow-ble-setup` will be set to yes to allow future configuration.

`yes` - BLE will always be enabled and check whether PiAware needs to be discoverable for configuration over BLE

`no` - Disables piaware-ble-connect service


