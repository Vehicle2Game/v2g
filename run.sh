#!/usr/bin/env bash

# Run commands relative to script directory
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

# Detecting if messages on can bus for vehicle identification
# canbusload can0@500000 | head -n 1 | grep "can0@500000     0       0      0   0"

if [ -z "$1" ]; then
    echo "Vehicle configuration required"
    exit 1
fi

if [ "$2" = "vcan" ]; then
    echo "Using virtual CAN buses ..."
    if [ ! -d /sys/class/net/can0 ]; then
        echo "Generating vcan interface can0"
        sudo ip link add can0 type vcan
        sudo ip link set can0 up
    fi
    if [ ! -d /sys/class/net/can1 ]; then
        echo "Generating vcan interface can1"
        sudo ip link add can1 type vcan
        sudo ip link set can1 up
    fi
fi

echo "Initializing ..."
# Check if at least one can interfaces is available
if [ ! -d /sys/class/net/can0 ]; then
    echo "Interface can0 not found. Is a CAN interface available?"
    exit 1
fi
if [ "$1" != "-bt" ]; then
    echo "Not in BT mode"
    if [ ! "$(stat -c '%a' /dev/uinput)" == "666" ]; then
        echo "Enabling access to uinput"
        sudo chmod +0666 /dev/uinput
    fi

    # Check if venv is available
    if [ ! -d venv ]; then
        echo "venv not found, creating new one + installing requirements"
        python3 -m venv venv
        . venv/bin/activate
        python3 -m pip install --upgrade pip
        python3 -m pip install -r requirements.txt
    else
        echo "using existing venv"
    fi
fi

#echo "Starting V2G Controller..."
if [ "$1" = "-bt" ]; then
    echo "Running in Bluetooth mode as root"
    sudo python3 __main__.py -d $1 $2
else
    venv/bin/python3 __main__.py -d $1
fi

echo "Done."
#wait $pid


