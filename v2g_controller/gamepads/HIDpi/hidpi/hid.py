# import binascii
import sys
import struct
from v2g_controller.gamepads.abstract_gamepad import AbstractGamePad, Buttons

# Class that represents a general HID device state
class HumanInterfaceDevice(object):
    MY_DEV_NAME = "Generic HID"
    SDP_RECORD_PATH = sys.path[0] + "/v2g_controller/gamepads/HIDpi/sdp/"  #file path of the sdp record to laod
    UUID = "00001124-0000-1000-8000-00805f9b34fb"  #HumanInterfaceDeviceServiceClass UUID

    def __init__(self, report_function):
        self.report_function = report_function

        self.state = bytearray(b'')
        self.state.extend(struct.pack("B", 0xA1)) # this is an input report

    def get_state(self):
        return self.state

    def send_report(self):
        self.report_function(self.state)

    def get_name(self):
        return self.MY_DEV_NAME

    def get_sdp_record_path(self):
        return self.SDP_RECORD_PATH

    def get_uuid(self):
        return self.UUID


# Class that represents the Gamepad state
class BTGamepad(HumanInterfaceDevice, AbstractGamePad):

    def __init__(self, report_function):
        super().__init__(report_function)

        self.MY_DEV_NAME = "V2G Gamepad"
        self.SDP_RECORD_PATH = sys.path[0] + "/v2g_controller/gamepads/HIDpi/sdp/sdp_record_gamepad.xml"

        # Define the Gamepad state
        self.state.extend(struct.pack("b", 0x00))  # X-axis between -127 and 127
        self.state.extend(struct.pack("b", 0x00))  # Y-axis between -127 and 127
        # self.state.extend(struct.pack("b", 0x00))  # Z-axis between -127 and 127
        self.state.extend(struct.pack("B", 0x00))  # unsigned char representing 3 buttons, rest of bits are constants
        
        self.mybuttons = {Buttons.A : 0, Buttons.B : 0, Buttons.X : 0, Buttons.Y : 0}

        self.x = 0.0
        self.y = 0.0
        self.y_zero = False
        self.z = 0.0

    def _update_btn_state(self):
        # vorne oben unten
        self.state[3] = struct.pack("B", self.mybuttons[Buttons.A] + 2 * self.mybuttons[Buttons.B] + 8 * self.mybuttons[Buttons.X] + 16 *self.mybuttons[Buttons.Y])[0]
    
    def _update_x_axis_state(self):
        self.state[1] = struct.pack("b", int(self.x * 127.0))[0]

    def _update_y_axis_state(self):
        self.state[2] = struct.pack("b", int(self.y * 127.0))[0]

    # def _update_Z_axis_state(self):
    #    self.state[3] = struct.pack("b", int(self.z * 127.0))[0]
   
    def update_button(self, id, state):
        """
        Set button state
        id: Buttons enum
        state: 0 or 1
        """
        self.mybuttons[id] = state
        self._update_btn_state()
        self.send_report()

    def update_js_left(self, x, y):
        """
        Set left Gamepad position
        x: -1.0 to 1.0
        y: -1.0 to 1.0
        """
        self.x = x
        if y != 0:
            self.y = -y
            self.y_zero = False
        elif not self.y_zero:
            self.y = -y
            self.y_zero = True
            
        self._update_x_axis_state()
        self._update_y_axis_state()
        self.send_report()

    def update_js_right(self, x, y):
        """
        Not implemented
        """
        pass
        
    def update_tg_left(self, value):
        """
        Set left trigger position
        value: 0.0 to 1.0
        """
        self.y = value
        #self.y = y
        self._update_y_axis_state()
        #self._update_y_axis_state()
        self.send_report()
        
    def update_tg_right(self, value):
        """
        Set right trigger position
        value: 0.0 to 1.0
        """
        pass
    
    def click_button(self, id, latency=0):
        """
        Not implemented
        """
        pass