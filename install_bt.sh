#!/usr/bin/env bash

# Run commands relative to script directory
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

echo "*** Installing dependencies ***"
sudo apt update
sudo apt upgrade -y
sudo apt-get install pi-bluetooth bluez bluez-tools bluez-firmware python3-bluez python3-dev python3-pip python3-dbus python3-venv libevdev-dev python3-libevdev can-utils -y
sudo pip3 install evdev
sudo pip3 install -r requirements.txt

echo "*** Setting up Bluetooth ***"
sudo ln -s /etc/bluetooth /usr/local/etc/bluetooth
match='\[General\]'
insert="Name = V2G Gamepad $(uname -n)\nClass = 0x000508"
file='/usr/local/etc/bluetooth/main.conf'

sudo sed -i "s/$match/$match\n$insert/" $file

echo "*** Modify Bluez service ***"
match='ExecStart=/usr/libexec/bluetooth/bluetoothd'
replace='ExecStart=/usr/libexec/bluetooth/bluetoothd --nodetach --compat --debug -p time'
file='/etc/systemd/system/dbus-org.bluez.service'
sudo sed -i "s@$match@$replace@" $file

cd v2g_controller/gamepads/HIDpi/
if [ "$1" ]; then
    echo "*** Installing for Vehicle $1 ***"
    match='AUTO'
    replace="$1"
    file='hid.service'
    sudo sed -i "s@$match@$replace@" $file
fi

echo "*** Changing address in settings.xml ***"
match='b8:27:eb:eb:7a:f9'
replace="$(sudo bluetoothctl show | head -n 1 | awk 'BEGIN { FS = "[ =]" } { print $2 }')"
file='settings.xml'
sed -i "s@$match@$replace@" $file

echo "*** Enable HID service ***"
sudo cp hid.service /etc/systemd/system/
sudo systemctl enable hid.service 
sudo systemctl daemon-reload

echo "*** Installing CAN Hat ***"
# Waveshare 2-CH CAN FD Hat
#sudo sh -c 'echo "dtparam=spi=on\ndtoverlay=spi1-3cs\ndtoverlay=mcp251xfd,spi0-0,interrupt=25\ndtoverlay=mcp251xfd,spi1-0,interrupt=24" >> /boot/config.txt'
# Waveshare RS485 CAN Hat
sudo sh -c 'echo "dtparam=spi=on\ndtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000" >> /boot/config.txt'

echo "*** Adding helper.sh to autostart ***"
match='# By default this script does nothing.'
insert='/home/pi/v2g/v2g_controller/gamepads/HIDpi/helper.sh \&'
file='/etc/rc.local'
sudo sed -i "s@$match@$match\n$insert\n@" $file

echo "*** Done, Please reboot ***"
