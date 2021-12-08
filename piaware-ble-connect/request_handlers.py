"""This file contains functions to process incoming UART requests and make HTTP
requests to piaware_configurator to configure piaware

"""
import json
import requests
import logging
from piaware_helpers import get_rpi_model_and_serial_number, get_adsb_site_number

logger = logging.getLogger('piaware_ble_connect')

PIAWARE_CONFIGURATOR_HOST = 'http://127.0.0.1:5000/configurator'
SUPPORTED_REQUESTS = [
    'get_device_info',
    'get_device_state',
    'get_wifi_networks',
    'set_wifi_config',
    'piaware_config_read'
]


def http_json_post(url, json_body):
    """Create and send a JSON POST request

        Parameters:
        host (str): Host to send HTTP request to
        json_body (dict): JSON data to include in HTTP POST body

        Returns: JSON response

    """
    request_id = json_body.get("request_id")
    try:
        r = requests.post(url, json=json_body, timeout=20)
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except requests.ConnectionError:
        error = f'Cannot connect to {url}...'
        return {"success": False, "error": error, "request_id": request_id}
    except requests.Timeout:
        error = f'Request to {url} timed out...'
        return {"success": False, "error": error, "request_id": request_id}
    except requests.HTTPError:
        error = f'HTTP Error returned from server: {r.status_code}'
        return {"success": False, "error": error, "request_id": request_id}
    except Exception as e:
        return {"success": False, "error": e, "request_id": request_id}

    # Send success json back to BLE central
    response_json = {"success": True, "request_id": request_id}
    if r.json():
        response_json["response_payload"] = r.json()

    return response_json


def handle_request(host, port, request):
    """ Handles incoming BLE UART data

        Parameters:
        host (str): Host IP of piaware-configurator serving BLE requests
        port (str): Port number of piaware-configurator serving BLE requests
        request (json str): Valid JSON string that requires with
                            request_id and request fields

    """
    # Validate json formatting
    try:
        json_object = json.loads(request)
    except ValueError:
        return {"success": False, "error": "Bad JSON formatting"}

    # Validate request
    try:
        request_id = json_object["request_id"]
        request = json_object["request"]
    except KeyError as e:
        error = f'Missing required field in request: {e}'
        return {"success": False, "error": error}

    if request not in SUPPORTED_REQUESTS:
        logger.error(f'Unsupported BLE request received: {request}')
        error = f'Unsupported request received: {request}'
        return {"success": False, "error": error}

    logger.info(f'BLE request received: {request}')

    # Generate piaware-configurator URL to send POST request to
    piaware_configurator_host_url = f'http://{host}:{port}/configurator'

    response = http_json_post(piaware_configurator_host_url, json_object)

    return response


def get_ble_advertisement_identifier(BLE_host, BLE_port):
    """ Returns an identifier name to use when advertising over BLE.
        Name priority: custom name, site number, Rpi model

        Parameters:
        host (str): Host IP of piaware-configurator serving BLE requests
        port (str): Port number of piaware-configurator serving BLE requests
    """
    raspberry_pi_model, serial_number = get_rpi_model_and_serial_number()
    site_number = get_adsb_site_number()

    if site_number:
        return f"PiAware - Site {site_number}"

    return f"PiAware - {raspberry_pi_model}"


def advertising_should_be_on(piaware_configurator_url):
    ''' Returns whether BLE peripheral should be in an advertising state.

        Currently, if wifi is connected and receiver is claimed, then BLE should be disabled

        Parameters:
        piaware_configurator_url (str): URL of piaware-configurator to request receiver data from
    '''
    request = '{"request": "get_device_state"}'
    response = http_json_post(piaware_configurator_url, json.loads(request))
    if response is None or type(response) is not dict:
        return None

    try:
        is_connected_to_internet = response['response_payload']['is_connected_to_internet']
        is_receiver_claimed = response['response_payload']['is_receiver_claimed']
        return False if is_connected_to_internet and is_receiver_claimed else True

    except KeyError:
        logger.info(f'Could not determine if advertising should be on')

    return True
