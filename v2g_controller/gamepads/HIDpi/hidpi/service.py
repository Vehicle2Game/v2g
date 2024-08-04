from __future__ import absolute_import, print_function

import sys
import socket

import dbus
import dbus.service
import dbus.mainloop.glib

from gi.repository import GObject as gobject

import v2g_controller.gamepads.HIDpi.hidpi.hid
import v2g_controller.gamepads.HIDpi.hidpi as hidpi

import xml.etree.ElementTree as ET

global mainloop

#Define a Bluez exception for our Bluez Agent
class Rejected(dbus.DBusException):
    _dbus_error_name = "org.bluez.Error.Rejected"

#Define a Bluez Agent
class FixedPinAgent(dbus.service.Object):
    SYSTEM_BUS = None
    PIN = None

    def __init__(self, bus, path, pin):
        dbus.service.Object.__init__(self, bus, path)
        self.SYSTEM_BUS = bus
        self.PIN = pin

    def set_trusted(self, path):
        props = dbus.Interface(self.SYSTEM_BUS.get_object("org.bluez", path), "org.freedesktop.DBus.Properties")
        props.Set("org.bluez.Device1", "Trusted", True)

    # Bluez release call
    # Let Profile exit gracefully instead
    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Release(self):
        print("Release")

    # Bluez Authorization call
    # Authomatically authorizes all services
    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        return

    # Bluez Request pin call
    # Returns the fixed pin
    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        self.set_trusted(device)
        return self.PIN

    # Bluez Request passkey call
    # Returns the fixed pin
    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        self.set_trusted(device)
        return dbus.UInt32(self.PIN)

    @dbus.service.method("org.bluez.Agent1", in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        print("DisplayPasskey (%s, %06u entered %u)" % (device, passkey, entered))

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        print("DisplayPinCode (%s, %s)" % (device, pincode))

    # Bluez Confirmation call
    # Checks our pin
    @dbus.service.method("org.bluez.Agent1", in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        if (passkey == self.PIN):
            self.set_trusted(device)
            return
        raise Rejected("Passkey doesn't match")

    # Bluez Authorization call
    # Authomatically authorizes all devices
    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Cancel(self):
        print("Cancel")


# Define a generic Bluez Profile object for our HID device
class BluezHIDProfile(dbus.service.Object):
    MY_ADDRESS = None  # Physical address of the Bluetooth adapter
    CONTROL_PORT = 17  # HID control port as specified in SDP > Protocol Descriptor List > L2CAP > HID Control Port
    INTERRUPT_PORT = 19  # HID interrupt port as specified in SDP > Additional Protocol Descriptor List > L2CAP > HID Interrupt Port

    control_socket = None
    interrupt_socket = None

    control_channel = None
    interrupt_channel = None


    def __init__(self, bus, path, physical_address):
        # Register this Bluez Profile on the DBUS
        dbus.service.Object.__init__(self, bus, path)

        self.MY_ADDRESS = physical_address

        # Manually set up sockets
        # Bluez doesn't handle this automatically for HID profiles
        # (Probably because Bluez only returns a single communication channel and HID requires two always)
        self.control_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_L2CAP)
        self.interrupt_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_L2CAP)

        self.control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.interrupt_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.interrupt_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        self.control_socket.bind((self.MY_ADDRESS, self.CONTROL_PORT))
        self.interrupt_socket.bind((self.MY_ADDRESS, self.INTERRUPT_PORT))

        # Maximum of one connection (HID virtual cable = True)
        self.control_socket.listen(1)
        self.interrupt_socket.listen(1)

        # Watch for connections on socket by adding an IO watch that calls an accept function
        self.listen(self.control_socket, self.accept_control)
        self.listen(self.interrupt_socket, self.accept_interrupt)

    # Bluez release call is used for the HID profile.
    # Close connections and exit gracefully
    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Release(self):
        gobject.source_remove(self.interrupt_socket.fileno())
        gobject.source_remove(self.control_socket.fileno())

        gobject.source_remove(self.interrupt_channel.fileno())
        gobject.source_remove(self.control_channel.fileno())

        self.interrupt_channel.close()
        self.control_channel.close()

        self.interrupt_socket.close()
        self.control_socket.close()

        print("Release")
        mainloop.exit()
        exit(0);

    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Cancel(self):
        print("Cancel")

    # Not used for HID profiles by Bluez
    @dbus.service.method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, file_descriptor, properties):
        print("NewConnection(%s, %d)." % (path, self.file_descriptor))

    # Not used for HID profiles by Bluez
    @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")
    def RequestDisconnection(self, path):
        print("RequestDisconnection(%s)." % (path))

    # Start watching for connections on socket by adding an IO watch
    def listen(self, socket, func):
        gobject.io_add_watch(socket.fileno(), gobject.IO_IN | gobject.IO_PRI, func)

    # Accept a connection from the control socket and create a channel
    # Start watching for IO input and errors by adding an IO watch
    def accept_control(self, source, cond):
        self.control_channel, cinfo = self.control_socket.accept()
        gobject.io_add_watch(self.control_channel.fileno(), gobject.IO_ERR | gobject.IO_HUP, self.close_control)
        gobject.io_add_watch(self.control_channel.fileno(), gobject.IO_IN | gobject.IO_PRI, self.callback, self.control_channel)
        return False  # Stop watching, we only accept one connection

    # Accept a connection from the interrupt socket and create a channel
    # Start watching for IO input and errors by adding an IO watch
    def accept_interrupt(self, source, cond):
        self.interrupt_channel, cinfo = self.interrupt_socket.accept()
        gobject.io_add_watch(self.interrupt_channel.fileno(), gobject.IO_ERR | gobject.IO_HUP, self.close_interrupt)
        gobject.io_add_watch(self.interrupt_channel.fileno(), gobject.IO_IN | gobject.IO_PRI, self.callback, self.interrupt_channel)
        return False

    # Receive messages from the HID host
    # When protocol messages are expected from the HID host, they are received here
    # Read and silently discard messages
    def callback(self, source, conditions, channel):
        status = True
        try:
            data = channel.recv(1024)
        except:
            status = False  # The channel was closed or experienced an error, remove IO watch
        return status

    # Close the control channel and start listening for new connections using the control socket
    # This is called when the control channel experiences an error or was closed by the HID host
    def close_control(self, source, condition):
        try:
            gobject.source_remove(source)  # Remove any remaining watch
            self.control_channel.close()
            self.control_channel = None

            self.listen(self.control_socket, self.accept_control)
        except:
            print("Close failed")
        return False

    # Close the interrupt channel and start listening for new connections using the interrupt socket
    # This is called when the interrupt channel experiences an error or was closed by the HID host
    def close_interrupt(self, source, condition):
        try:
            gobject.source_remove(source)  # Remove any remaining watch
            self.interrupt_channel.close()
            self.interrupt_channel = None

            self.listen(self.interrupt_socket, self.accept_interrupt)
        except:
            print("Close failed")
        return False

    # Send an input report given a device state represented by a bytearray
    def send_input_report(self, device_state):
        try:
            if self.interrupt_channel is not None:
                self.interrupt_channel.send(device_state)
        except:
            print("Error while attempting to send report.")
        return True  # Return True to support adding a timeout function

    # Return True if there is a connection on both the control and interrupt channels
    # Return False otherwise
    def is_connected(self):
        return (self.control_channel is not None) and (self.interrupt_channel is not None)


# Create a Bluetooth service to emulate a HID device
class BTHIDService:
    PROFILE_DBUS_PATH = "/nl/rug/ds/heerkog/hid"  #dbus path of the Bluez Profile
    AGENT_DBUS_PATH = "/nl/rug/ds/heerkog/fixedpinagent"  #dbus path of the Bluez Agent
    PROFILE_MANAGER_INTERFACE = None
    AGENT_MANGER_INTERFACE = None
    ADAPTER_INTERFACE = None

    def __init__(self, loop):
        mainloop = loop

        print("Loading settings.")

        tree = ET.parse("v2g_controller/gamepads/HIDpi/settings.xml")
        root = tree.getroot()
        physical_address = root.find("address").text.strip()
        pin = root.find("pin").text.strip()

        print("Configuring adapter.")

        #create our HID device and pass a pointer to the input report function of our profile
        self.device = hidpi.hid.BTGamepad(self.send_input_report)

        #setup profile options
        service_record = self.read_sdp_service_record(self.device.get_sdp_record_path())

        opts = {
            "ServiceRecord": service_record,
            "Name": self.device.get_name(),
            "Role": "server",
            "AutoConnect": True,
            "RequireAuthentication": False,
            "RequireAuthorization": False
        }

        # Retrieve the system bus
        system_bus = dbus.SystemBus()

        # Retrieve the Bluez Bluetooth Adapter interface
        self.ADAPTER_INTERFACE = dbus.Interface(system_bus.get_object("org.bluez", "/org/bluez/hci0"), "org.freedesktop.DBus.Properties")

        # Power the Bluetooth adapter
        self.ADAPTER_INTERFACE.Set('org.bluez.Adapter1', 'Powered', dbus.Boolean(1))

        # Allow the Bluetooth Adapter to pair
        self.ADAPTER_INTERFACE.Set('org.bluez.Adapter1', 'PairableTimeout', dbus.UInt32(0))
        self.ADAPTER_INTERFACE.Set('org.bluez.Adapter1', 'Pairable', dbus.Boolean(1))

        # Allow the Bluetooth Adapter to be discoverable for 30 seconds
        self.ADAPTER_INTERFACE.Set('org.bluez.Adapter1', 'DiscoverableTimeout', dbus.UInt32(180))
        self.ADAPTER_INTERFACE.Set('org.bluez.Adapter1', 'Discoverable', dbus.Boolean(1))

        print("Configuring Bluez Agent.")

        # Retrieve the Bluez Bluetooth Agent Manager interface
        self.AGENT_MANGER_INTERFACE = dbus.Interface(system_bus.get_object("org.bluez", "/org/bluez"), "org.bluez.AgentManager1")

        # Create our Bluez Agent
        self.agent = FixedPinAgent(system_bus, self.AGENT_DBUS_PATH, pin)

        # Register and request Agent
        self.AGENT_MANGER_INTERFACE.RegisterAgent(self.AGENT_DBUS_PATH, "NoInputNoOutput")
        self.AGENT_MANGER_INTERFACE.RequestDefaultAgent(self.AGENT_DBUS_PATH)

        print("Agent registered.")
        print("Configuring Bluez Profile.")

        # Create our Bluez HID Profile
        self.profile = BluezHIDProfile(system_bus, self.PROFILE_DBUS_PATH, physical_address)

        # Retrieve the Bluez Bluetooth Profile Manager interface
        self.PROFILE_MANAGER_INTERFACE = dbus.Interface(system_bus.get_object("org.bluez", "/org/bluez"), "org.bluez.ProfileManager1")

        # Register our Profile with the Bluez Bluetooth Profile Manager
        self.PROFILE_MANAGER_INTERFACE.RegisterProfile(self.PROFILE_DBUS_PATH, self.device.get_uuid(), opts)

        print("Profile registered.")

    # Read and return an SDP record from a file
    def read_sdp_service_record(self, path):
        try:
            fh = open(path, "r")
        except:
            sys.exit("Failed to read SDP record.")

        return fh.read()

    def send_input_report(self, state):
        if self.profile.is_connected():
            self.profile.send_input_report(state)
        else:
            # Allow the Bluetooth Adapter to be discoverable again for 30 seconds
            self.ADAPTER_INTERFACE.Set('org.bluez.Adapter1', 'DiscoverableTimeout', dbus.UInt32(180))
            self.ADAPTER_INTERFACE.Set('org.bluez.Adapter1', 'Discoverable', dbus.Boolean(1))
