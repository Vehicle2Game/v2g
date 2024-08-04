import vgamepad as vg
import time

from v2g_controller.gamepads.abstract_gamepad import AbstractGamePad, Buttons
# requires vgamepad to be installed
# on linux, run sudo chmod +0666 /dev/uinput 
# to temporarily enable input permissions 

class MyGamepad(AbstractGamePad):
    def __init__(self):
        self.gamepad = vg.VX360Gamepad()
        
        
    def click_button(self, id, latency=0):
        """
        Press and release button
        id: Buttons enum
        latency: time in seconds to hold button
        """
        
        #self.gamepad.press_button(button=id)
        self.gamepad.press_button(button=id)
        self.gamepad.update()
        time.sleep(latency)
        self.gamepad.release_button(button=id)
        self.gamepad.update()
    
    def update_button(self, id, state):
        """
        Set button state
        id: Buttons enum
        state: 0 or 1
        """
        if state == 1:
            self.gamepad.press_button(button=id)
        else:
            self.gamepad.release_button(button=id)
        self.gamepad.update()

    def update_js_left(self, x, y):
        """
        Set left gamepad position
        x: -1.0 to 1.0
        y: -1.0 to 1.0
        """
        self.gamepad.left_joystick_float(x_value_float=x, y_value_float=y)
        self.gamepad.update()

    def update_js_right(self, x, y):
        """
        Set right joystick position
        x: -1.0 to 1.0
        y: -1.0 to 1.0
        """
        self.gamepad.right_joystick_float(x_value_float=x, y_value_float=y)
        self.gamepad.update()
        
    def update_tg_left(self, value):
        """
        Set left trigger position
        value: 0.0 to 1.0
        """
        self.gamepad.left_trigger_float(value_float=value)
        self.gamepad.update()
        
    def update_tg_right(self, value):
        """
        Set right trigger position
        value: 0.0 to 1.0
        """
        self.gamepad.right_trigger_float(value_float=value)
        self.gamepad.update()