from enum import IntFlag
import vgamepad as vg

class Buttons(IntFlag):
    """
    Possible XUSB report buttons.
    """
    UP = vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP
    DOWN = vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN
    LEFT = vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT
    RIGHT = vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT
    START = vg.XUSB_BUTTON.XUSB_GAMEPAD_START
    BACK = vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK
    LEFT_THUMB = vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB
    RIGHT_THUMB = vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB
    LEFT_SHOULDER = vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER
    RIGHT_SHOULDER = vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER
    GUIDE = vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE
    A = vg.XUSB_BUTTON.XUSB_GAMEPAD_A
    B = vg.XUSB_BUTTON.XUSB_GAMEPAD_B
    X = vg.XUSB_BUTTON.XUSB_GAMEPAD_X
    Y = vg.XUSB_BUTTON.XUSB_GAMEPAD_Y

from abc import ABC, abstractmethod
class AbstractGamePad(ABC):

    def __init__(self):
        self.gamepad = None
    
    @abstractmethod
    def click_button(self, id, latency=0):
        """
        Press and release button
        id: Buttons enum
        latency: time in seconds to hold button
        """
        pass
    
    @abstractmethod
    def update_button(self, id, state):
        """
        Set button state
        id: Buttons enum
        state: 0 or 1
        """
        pass

    @abstractmethod
    def update_js_left(self, x, y):
        """
        Set left gamepad position
        x: -1.0 to 1.0
        y: -1.0 to 1.0
        """
        pass

    @abstractmethod
    def update_js_right(self, x, y):
        """
        Set right gamepad position
        x: -1.0 to 1.0
        y: -1.0 to 1.0
        """
        pass

    @abstractmethod    
    def update_tg_left(self, value):
        """
        Set left trigger position
        value: 0.0 to 1.0
        """
        pass

    @abstractmethod    
    def update_tg_right(self, value):
        """
        Set right trigger position
        value: 0.0 to 1.0
        """
        pass