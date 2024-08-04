#from HIDpi.hidpi.__main__ import start as hidpi_main
import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from v2g_controller import main as v2g_main

import argparse

if __name__ == '__main__':
    # Parsing command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("vehicle", type=str, help="The vehicle configuration to use. Use \"AUTO\" to automatically detect the vehicle.")
    parser.add_argument("-d", "--debug", action='store_true', help="Enables debug information.")
    parser.add_argument("-bt", "--btcontroller", action='store_true', help="Enables Bluetooth controller mode.")
    args = parser.parse_args()
    
    print("""
__     ______   ____ 
\ \   / /___ \ / ___|
 \ \ / /  __) | |  _ 
  \ V /  / __/| |_| |
   \_/  |_____|\____|
           """)

    if args.btcontroller:
        import v2g_controller.gamepads.HIDpi.hidpi.main as hidpi_main
        print("Bluetooth controller mode selected.")
        hidpi_main.start(args, v2g_main.start)
    else:
        print("Virtual controller mode selected.")
        v2g_main.start(args)
        v2g_main.loop()