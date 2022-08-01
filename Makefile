install:
	cp -r piaware-ble-connect /usr/lib/
	cp debian/piaware-ble-connect.service /lib/systemd/system/
	cp sudoers/piaware-ble-connect /etc/sudoers.d/
