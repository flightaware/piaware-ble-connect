import logging
import json

logger = logging.getLogger('piaware_ble_connect')


def get_rpi_model_and_serial_number():
    """ Returns Raspberry Pi Model and CPU serial number

    """
    rpi_model_mapping = {
                         "RPi Zero W": ["9000c1"],
                         "RPi Zero": ["900092", "900093", "920093"],
                         "RPi 3B": ["a02082", "a22082", "a32082"],
                         "RPi 3B+": ["a020d3"],
                         "RPi 4": ["a03111", "b03111", "c03111"]
                        }

    pi_model = "Raspberry Pi"
    serial_number = None
    try:
        with open("/proc/cpuinfo", "r") as cpuinfo:
            lines = cpuinfo.read().splitlines()
            for line in lines:
                data = line.split(':')
                if len(data) == 2:
                    attribute = data[0].strip()
                    value = data[1].strip()

                    # Use rpi model mapping to find the Pi Model from the revision number
                    if attribute == 'Revision':
                        revision_number = value
                        model = [k for k, v in rpi_model_mapping.items() if revision_number in v]
                        if model:
                            pi_model = model[0]
                        continue

                    # Extract last 6 characters of serial number for future use on identifier
                    if attribute == 'Serial':
                        serial_number = value[-6:].upper()
                        continue

            return pi_model, serial_number

    except Exception:
        logger.error(f"Error retreiving Raspberry Pi Model or Serial Number")

    return "Raspberry Pi", None


def get_adsb_site_number():
    """ Returns ADS-B site number from status.json if present

    """
    site_number = None

    try:
        with open("/var/run/piaware/status.json", "r") as status_json:
            data = json.load(status_json)
            site_url = data['site_url']
            if "#stats-" in site_url:
                split_site_url = site_url.split("#stats-")
            elif "/stats/site/" in site_url:
                split_site_url = site_url.split("/stats/site/")
            else:
                return None

            if len(split_site_url) == 2:
                site_number = split_site_url[1]
    except KeyError:
        logger.info(f"No site number found in status.json. Receiver unclaimed or not yet connected to FlightAware.")
    except Exception:
        logger.error(f"Error retrieving ADS-B receiver Site number")

    return site_number
