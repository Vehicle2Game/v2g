#!/usr/bin/env python3
# v2g_controller

# This program converts EV signals into a virtual gamepad
import can
import time
import platform
import sys


import v2g_controller.configuration_helper as cfh
from v2g_controller.helper import debug
import v2g_controller.helper as h
from v2g_controller.car_connector import CarConnector
import v2g_controller.car_detector as car_detector

from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module
import subprocess



def init_can_bus(port, bus_type, bitrate, data_bitrate=None):
    if platform.system() == "Linux":
        channel_prefix = "can"
        channel = f"{channel_prefix}{port}"
        if bus_type == "standard":
            debug(f"Using standard CAN bus on channel {channel}, checking interface state:" )
            try:
                subprocess.run(["grep", "down", f"/sys/class/net/{channel}/operstate"], check=True)
                debug("CAN interface is down, attempting to bring up")
                subprocess.run(["sudo", "ip", "link", "set" ,f"{channel}", "up", "type", "can", "bitrate", f"{bitrate}"], check=False)
            except subprocess.CalledProcessError:
                pass
            can_bus = can.Bus(
                interface="socketcan",
                channel=channel,
                bitrate=bitrate,
            )
        elif bus_type == "fd":
            debug(f"Using CAN FD bus on channel {channel}, checking interface state:" )
            try:
                subprocess.run(["grep", "down", f"/sys/class/net/{channel}/operstate"], check=True)
                debug("CAN interface is down, attempting to bring up")
                subprocess.run(["sudo", "ip", "link", "set" ,f"{channel}", "up", "type", "can", "bitrate", f"{bitrate}", "fd", "on", "dbitrate", f"{data_bitrate}"], check=False)
            except subprocess.CalledProcessError:
                pass
            can_bus = can.Bus(
                interface="socketcan",
                channel=channel,
                bitrate=bitrate,
                data_bitrate=data_bitrate,
                fd=True,
            )
        else:
            debug("Invalid CAN bus type supplied for Linux")
            return None
    elif platform.system() == "Windows":
        if port == 0:
            channel = "PCAN_USBBUS1"
        elif port == 1:
            channel = "PCAN_USBBUS2"
        else:
            debug("Invalid CAN bus port supplied for Windows")
            return None
        if bus_type == "standard":
            debug(f"Using standard CAN bus on channel {channel}" )
            can_bus = can.Bus(
                interface="pcan",
                channel=channel,
                bitrate=bitrate,
            )
        elif buy_type == "fd":
            debug(f"Using CAN FD bus on channel {channel}" )
            can_bus = can.Bus(
                interface="pcan",
                channel=channel,
                fd=True,
                f_clock_mhz=80,
                nom_brp=10,
                nom_tseg1=12,
                nom_tseg2=3,
                nom_sjw=3,
                data_brp=2,
                data_tseg1=15,
                data_tseg2=4,
                data_sjw=4,
            )
        else:
            debug("Invalid CAN bus type supplied for Windows")
            return None
    else:
        debug("Unsupported operating system")
        return None
    return can_bus

def start(args, gamepad = None):
    if args.debug:
        h.debug_enabled = True
    debug(" *** v2g_controller ***")
    
    # Dynamically import all python files in vehicle_configurations
    debug('Loading vehicle configurations...')
    package_dir = Path(__file__).resolve().parent.joinpath("vehicle_configurations")
    for (_, module_name, _) in iter_modules([package_dir]):
        module = import_module(f"v2g_controller.vehicle_configurations.{module_name}")
        
    debug('Configured vehicles:')
    for vehicle in cfh.vehicle_configurations:
        debug(f" - {vehicle}")
    if args.vehicle == "AUTO":
        args.vehicle = car_detector.detect_vehicle()      
    debug('Selected vehicle:')
    if args.vehicle == "NONE" and args.btcontroller:
        debug("No vehicle detected, defaulting to ID3_UDS")
        args.vehicle = "ID3_UDS"
    debug(f" - {args.vehicle}")
    try:
        vehicle_configuration: cfh.VehicleConfiguration = cfh.vehicle_configurations[args.vehicle]
    except KeyError:
        print("Error: Selected Vehicle is not configured!")
        sys.exit(1)

    if platform.system() == "Linux":
        debug("Running on Linux")
    elif platform.system() == "Windows":
        debug("Running on Windows")
    else:
        debug("Running on Unsupported OS")
    
    # generate filter
    filters = []
    filter_ids = []
    for config in vehicle_configuration.configurations:
        if filter_ids.count(hex(config.can_signal.id)) == 0:
            filter_ids.append(hex(config.can_signal.id))
            filters.append(
                {"can_id": config.can_signal.id, "can_mask": 0x7FF, "extended": False}
            )
        
    
    # init car connector
    car_connector = CarConnector(gamepad=gamepad, vehicle_config=vehicle_configuration)

    can_buses = []
    for i, bus in enumerate(vehicle_configuration.can_buses):
        can_buses.append(init_can_bus(i, bus.type, bus.bitrate, bus.data_bitrate))
    
    # initialize polling
    if vehicle_configuration.operation_mode == cfh.OperationMode.UDS:
        debug(f"Initializing UDS polling ...")
        for polling_msg in vehicle_configuration.polling_messages:
            can_buses[0].send_periodic(polling_msg.message, polling_msg.interval)
            time.sleep(polling_msg.interval / 5)
        
    debug(f"Applying filters for the following IDs: {filter_ids}")
    for bus in can_buses:
        bus.set_filters(filters)
        can.Notifier(bus, [car_connector])

def loop():
    # Keep program running to handle CAN signals
    while True:
        time.sleep(100)
