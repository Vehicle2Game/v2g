from v2g_controller.gamepads.HIDpi.hidpi.service import BTHIDService
import os
import sys

from gi.repository import GObject as gobject
from dbus.mainloop.glib import DBusGMainLoop

def start(args = None, start_func = None):
    if not os.geteuid() == 0:
        sys.exit("Bluetooth mode requires root")

    DBusGMainLoop(set_as_default=True)
    mainloop = gobject.MainLoop()
    myservice = BTHIDService(mainloop)
    
    # Run v2g controller is provided
    if start_func is not None:
        start_func(args, myservice.device)
    
    mainloop.run()