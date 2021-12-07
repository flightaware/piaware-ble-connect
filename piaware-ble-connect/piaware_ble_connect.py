#!/usr/bin/env python3

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import json
import logging
import argparse
from threading import Thread
import time
import sys

import constants
from bluez import Application, Advertisement, Service, Characteristic
from bluez import find_adapter
from request_handlers import handle_request, get_ble_advertisement_identifier, advertising_should_be_on

UART_SERVICE_UUID = 'ac8602af-0226-4889-b925-d751bdf70001'
UART_RX_CHARACTERISTIC_UUID = 'ac8602af-0226-4889-b925-d751bdf70002'
UART_TX_CHARACTERISTIC_UUID = 'ac8602af-0226-4889-b925-d751bdf70003'
ADVERTISING_NAME = 'PiAware'

# Shared globals
tx_characteristic = None
BLE_host = None
BLE_port = None

logger = logging.getLogger('piaware_ble_connect')

class TxCharacteristic(Characteristic):
    """ GATT characteristic for transmitting data to connected BLE device

    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_TX_CHARACTERISTIC_UUID,
                                ['notify'], service)
        self.notifying = False

    def send_tx(self, s):
        if not self.notifying:
            return
        logger.debug(f'Tx (response): {s}')
        s_bytes = json.dumps(s)
        s_bytes += chr(19)

        value = []
        for c in s_bytes:
            value.append(dbus.Byte(c.encode('utf-8')))
            # If payload exceeds MTU, send it in pieces
            if len(value) >= 182:
                self.PropertiesChanged(constants.GATT_CHRC_IFACE, {'Value': value}, [])
                value.clear()

        if len(value) > 0:
                self.PropertiesChanged(constants.GATT_CHRC_IFACE, {'Value': value}, [])

    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True

    def StopNotify(self):
        if not self.notifying:
            return
        self.notifying = False


class RxCharacteristic(Characteristic):
    """ GATT characteristic for receiving data from connected BLE device.
        This data will be forwarded to piaware-configurator for processing
        and return response back to connected BLE device.

    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_RX_CHARACTERISTIC_UUID,
                                ['write'], service)

    def WriteValue(self, value, options):
        global tx_characteristic

        request = bytearray(value).decode('utf-8')
        logger.debug(f'Rx (request): {request}')

        response = handle_request(BLE_host, BLE_port, request)
        if response is None:
            response = {'success': False}

        # Send a response back via the TxCharacteristic
        tx_characteristic.send_tx(response)


class UartService(Service):
    ''' UART Service class with TX and RX GATT characteristics

    '''
    def __init__(self, bus, index):
        global tx_characteristic
        Service.__init__(self, bus, index, UART_SERVICE_UUID, True)
        tx_characteristic = TxCharacteristic(bus, 0, self)
        self.add_characteristic(tx_characteristic)
        self.add_characteristic(RxCharacteristic(bus, 1, self))


class UartApplication(Application):
    ''' UART Application class with UART GATT service

    '''
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(UartService(bus, 0))


class UartAdvertisement(Advertisement):
    ''' UART Advertisement class

        Handles initialization of BLE Advertisement
    '''
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid(UART_SERVICE_UUID)
        advertisement_name = get_ble_advertisement_identifier(BLE_host, BLE_port)
        if not advertisement_name:
            advertisement_name = ADVERTISING_NAME
        self.add_local_name(advertisement_name)
        self.include_tx_power = True


def init_logger(args):
    """ Initializes application logger. Configurable via --log-level program arg

    """
    loglevel_mapping = [
        ('info', logging.INFO),
        ('debug', logging.DEBUG),
        ('warning', logging.WARNING),
        ('error', logging.ERROR),
        ('critical', logging.CRITICAL),
    ]

    for config_loglevel, loglevel in loglevel_mapping:
        if args.log_level == config_loglevel:
            logger.setLevel(loglevel)
            break

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')

    ch = logging.StreamHandler()
    ch.setLevel(loglevel)
    ch.setFormatter(formatter)

    logger.addHandler(ch)

    logger.info(f'Logging level set to {config_loglevel}')


def parse_args():
    """ Parse command-line arguments

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error', 'critical'], default='info',
        help='Log level for program output'
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host IP of piaware-configurator handling BLE requests'
    )
    parser.add_argument(
        '--port',
        default='5000',
        help='Port number of piaware-configurator handling BLE requests'
    )

    return parser.parse_args()


class BLE_Peripheral():
    ''' Bluetooth Low Energy Peripheral that implements UART service

    '''
    def __init__(self):
        self.mainloop = None
        self.is_advertising = False
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self.bus = dbus.SystemBus()
        self.adapter = find_adapter(self.bus)
        if not self.adapter:
            logger.critical('BLE adapter not found')
            return

        # Create a GATT Manager dbus.Interface object
        self.service_manager = dbus.Interface(
                                    self.bus.get_object(constants.BLUEZ_SERVICE_NAME, self.adapter),
                                    constants.GATT_MANAGER_IFACE
                                    )

        # Create a Advertising Manager dbus.Interface object
        self.ad_manager = dbus.Interface(
                                    self.bus.get_object(constants.BLUEZ_SERVICE_NAME, self.adapter),
                                    constants.LE_ADVERTISING_MANAGER_IFACE
                                    )

        # Create a UART Application object that handles setting up UART service
        # and characteristics
        self.uart_app = UartApplication(self.bus)

        # Create a UART Advertisement object
        self.advertisement = UartAdvertisement(self.bus, 0)

    def run(self):
        ''' Start BLE Peripheral mainloop

        '''
        if self.mainloop:
            return

        self.mainloop = GLib.MainLoop()
        try:
            self.mainloop.run()
        except Exception as e:
            logger.info(f'Exception occured in mainloop {e}')
            self.stop_advertising()
            self.unregister_application()
            self.mainloop.quit()
            self.mainloop = None

    def register_application(self):
        ''' Registers application with Bluez

        '''
        try:
            self.service_manager.RegisterApplication(self.uart_app.get_path(), {},
                                                reply_handler=self.register_application_callback,
                                                error_handler=self.register_application_error_callback)
        except dbus.exceptions.DBusException:
            logger.error("Error registering application")
            return

        logger.debug("GATT application registered")

    def unregister_application(self):
        ''' Unregister application with Bluez

        '''
        if self.is_advertising:
            self.stop_advertising()
        try:
            self.service_manager.UnregisterApplication(self.uart_app.get_path())
        except dbus.exceptions.DBusException:
            logger.error("Error unregistering application")
            return

        logger.info("BLE GATT server stopped")

    def start_advertising(self):
        ''' Start advertising mode which makes BLE peripheral discoverable

        '''
        logger.debug(f'Enabling BLE Peripheral advertisement mode')
        if self.is_advertising:
            logger.debug(f'BLE Peripheral advertising is already enabled')
            return

        self.ad_manager.RegisterAdvertisement(self.advertisement.get_path(), {},
                                                reply_handler=self.register_adv_callback,
                                                error_handler=self.register_adv_error_callback)
        self.is_advertising = True

    def stop_advertising(self):
        ''' Stop advertising mode

        '''
        logger.debug(f'Disabling BLE Peripheral advertisement mode')
        if not self.is_advertising:
            logger.debug(f'BLE Peripheral advertising already disabled')
            return

        try:
            self.ad_manager.UnregisterAdvertisement(self.advertisement.get_path(),
                                                  reply_handler=self.unregister_adv_callback,
                                                  error_handler=self.unregister_adv_error_callback)
        except dbus.exceptions.DBusException:
            logger.error(f'Error disabling BLE Peripheral advertising')

        self.is_advertising = False

    def is_advertising(self):
        return self.is_advertising

    def register_adv_callback(self):
        logger.info('BLE Peripheral advertising ON')

    def register_adv_error_callback(self, error):
        logger.critical(f'Failed to enable Advertisement mode: {error}')

    def register_application_callback(self):
        logger.info('BLE GATT server started')

    def register_application_error_callback(self, error):
        logger.critical(f'Failed to register application: {error}')
        self.mainloop.quit()

    def unregister_adv_callback(self):
        logger.info('BLE Peripheral advertising OFF')

    def unregister_adv_error_callback(self, error):
        logger.critical(f'Failed to disable Advertisement mode: {error}')


class BLE_Service():
    ''' Bluetooth Low Energy service for piaware configuration.

        The service creates creates a BLE Peripheral that advertises and
        handles requests from connected BLE Central devices. It also spawns
        a thread to enable/disable advertising mode depending on the PiAware
        state.
    '''
    def __init__(self, host, port):
        self.piaware_configurator_url = f'http://{host}:{port}/configurator'
        self.ble_peripheral = None
        self.advertising_monitor = None

    def start_service(self):
        logger.info(f'Starting Bluetooth Low Energy service for piaware configuration')
        self.ble_peripheral = BLE_Peripheral()
        self.ble_peripheral.register_application()

        monitor = Thread(target=self.start_advertising_monitor, args=(), daemon=True)
        monitor.start()

        self.ble_peripheral.run()

    def start_advertising_monitor(self):
        ''' Separate thread to auto-detect whether advertising mode should be enabled or disabled

        '''
        ble_timeout_minutes = 5
        time.sleep(60)
        logger.info(f'Starting advertising monitor')
        while True:
            # BLE advertising timeout reached. Disable BLE
            if ble_timeout_minutes == 0:
                logger.info(f'Bluetooth discovery enabled timeout reached. Disabling Bluetooth discovery mode.')
                self.ble_peripheral.stop_advertising()
                sys.exit()

            is_advertising = self.ble_peripheral.is_advertising
            should_advertising_be_on = advertising_should_be_on(self.piaware_configurator_url)

            # Advertising ON but should be off now. Disable BLE advertising
            if is_advertising == True and should_advertising_be_on == False:
                logger.info(f'PiAware has been connected and claimed. Disabling Bluetooth discovery mode.')
                self.ble_peripheral.stop_advertising()
                sys.exit()

            # Advertising OFF and should be OFF. Do nothing
            elif is_advertising == False and should_advertising_be_on == False:
                logger.info(f'Bluetooth discovery mode is disabled')
                sys.exit()

            # Advertising OFF and should be ON. Enable BLE advertising
            elif is_advertising == False and should_advertising_be_on == True:
                logger.info(f'PiAware is not connected to FlightAware and/or unclaimed. Enabling BLE discovery mode.')
                self.ble_peripheral.start_advertising()

            time.sleep(60)
            ble_timeout_minutes -= 1


    def stop_service(self):
        logger.info(f'Stopping Bluetooth Low Energy service for piaware configuration')
        self.ble_peripheral.stop_advertising()
        self.ble_peripheral.unregister_application()
        sys.exit(0)

def main():
    global BLE_host
    global BLE_port

    args = parse_args()
    init_logger(args)

    BLE_host = args.host
    BLE_port = args.port

    ble_service = BLE_Service(BLE_host, BLE_port)
    try:
        ble_service.start_service()
    except KeyboardInterrupt:
        ble_service.stop_service()
        logger.info(f'Keyboard exit')


if __name__ == '__main__':
    main()
