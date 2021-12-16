""" This file contains helper functions to interact with systemd services using Python's D-Bus library

"""
import dbus
import logging
import subprocess

from constants import DBUS_SYSTEMD_IFACE, DBUS_SYSTEMD_OBJECT_PATH, DBUS_SYSTEMD_MANAGER_IFACE, DBUS_PROP_IFACE, DBUS_SYSTEMD_UNIT_IFCE

logger = logging.getLogger('piaware_ble_connect')


def is_service_active(system_bus, manager, service_name):
    service = system_bus.get_object(DBUS_SYSTEMD_IFACE, object_path=manager.GetUnit(service_name))
    interface = dbus.Interface(service, dbus_interface=DBUS_PROP_IFACE)

    active_state = interface.Get(DBUS_SYSTEMD_UNIT_IFCE, 'ActiveState')

    logger.debug(f'{service_name} is {active_state}')
    return True if active_state == 'active' else False


def stop_systemd_service(service_name):
    system_bus = dbus.SystemBus()

    # Get systemd manager interface
    systemd_dbus_interface = system_bus.get_object(DBUS_SYSTEMD_IFACE, DBUS_SYSTEMD_OBJECT_PATH)
    systemd_dbus_manager = dbus.Interface(systemd_dbus_interface, DBUS_SYSTEMD_MANAGER_IFACE)

    if is_service_active(system_bus, systemd_dbus_manager, service_name):
        logger.debug(f'Stopping {service_name}')

        #
        # Using dbus to stop systemd service might be a better solution here, but need to figure out
        # how to get around permission errors. Use subprocess with appropriate sudo rules for now
        # 
        # systemd_dbus_manager.StopUnit(service_name, "replace")

        cmd = ["sudo", "systemctl", "stop", service_name]
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def shutdown_ble_services():
    logger.info(f'Stopping PiAware Bluetooth LE services for piaware configuration')

    stop_systemd_service('piaware-wifi-scan.service')
    stop_systemd_service('piaware-configurator.service')
    stop_systemd_service('piaware-ble-connect.service')
