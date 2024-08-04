import can

from v2g_controller.helper import debug, range_map
import v2g_controller.configuration_helper as cfh
from v2g_controller.gamepads.mygamepad.mygamepad import MyGamepad
from v2g_controller.gamepads.abstract_gamepad import Buttons


class CarConnector(can.Listener):
    """
    Class for converting CAN signals into a virtual gamepad.
    """

    def __init__(self, gamepad, vehicle_config: cfh.VehicleConfiguration):
        """
        Initialize the virtual gamepad and variables.
        """
        if gamepad is None:
            self.gamepad = MyGamepad()
        else:
            self.gamepad = gamepad
        self.x_axis = 0.0
        self.y_axis = 0.0
        self.direction = 1
        self.brake = 0.0
        self.last_gear = 0
        self.buttons = {
            Buttons.A: 0,
            Buttons.B: 0,
            Buttons.X: 0,
            Buttons.Y: 0,
        }
        self.vehicle = vehicle_config
        self.counter = 0

    def on_message_received(self, msg: can.Message):
        """
        Callback function to read the CAN messages and update the gamepad state based on the received messages.

        Args:
        msg: The CAN message received.
        """
        
        if self.counter < self.vehicle.read_limiter:
            self.counter +=1
            return
        else:
            self.counter = 0

        for config in self.vehicle.configurations:
            if config.match(msg.arbitration_id):
                # apply UDS identity filter
                if config.ident_filter != []:
                    ident_pos = 2 if config.ident_filter_mf == False else 3
                    if (
                        config.ident_filter[0] != msg.data[ident_pos]
                        or config.ident_filter[1] != msg.data[ident_pos + 1]
                    ):
                        continue
                if config.cf_filter != []:
                    if config.cf_filter[0] != msg.data[0]:
                            continue
                    
                if config.type == cfh.Type.Steering:
                    self.x_axis = self.steering_map(
                        config.value(msg.data),
                        self.vehicle.steering_exponent,
                        -self.vehicle.steering_max,
                        self.vehicle.steering_max,
                        self.vehicle.steering_deadzone,
                    )
                    self.gamepad.update_js_left(self.x_axis, self.y_axis)
                elif config.type == cfh.Type.Speed:
                    self.y_axis = (
                        self.speed_map(config.value(msg.data)) * self.direction
                    )
                    self.gamepad.update_js_left(self.x_axis, self.y_axis)
                elif config.type == cfh.Type.Brake:
                    self.brake = self.brake_map(config.value(msg.data))
                    self.gamepad.update_tg_left(self.brake)
                elif config.type == cfh.Type.Button:
                    value = config.value(msg.data)
                    if self.buttons[config.buttons[0]] != value:
                        self.buttons[config.buttons[0]] = value
                        self.gamepad.update_button(config.buttons[0], value)
                elif config.type == cfh.Type.Gear:
                    if config.value(msg.data) == -2:
                        self.direction = -1
                    elif config.value(msg.data) == -1:
                        if self.last_gear != -1:
                            self.gamepad.update_button(config.buttons[0], 1)
                            self.last_gear = -1
                    elif config.value(msg.data) == 0:
                        if self.last_gear == -1:
                            self.gamepad.update_button(config.buttons[0], 0)
                        elif self.last_gear == 1:
                            self.gamepad.update_button(config.buttons[1], 0)
                        self.last_gear = 0
                    elif config.value(msg.data) == 1:
                        if self.last_gear != 1:
                            self.gamepad.update_button(config.buttons[1], 1)
                            self.last_gear = 1
                            self.direction = 1
        debug(
            f"X: {self.x_axis:6.3f}, Y: {self.y_axis:6.3f}, direction: {self.direction:2d}, Brake: {self.brake:5.3f}, Gear: {self.last_gear:2d}, A: {self.buttons[Buttons.A]}, B: {self.buttons[Buttons.B]}, X: {self.buttons[Buttons.X]}, Y: {self.buttons[Buttons.Y]}   ",
            overwrite=True,
        )

    def steering_map(self, angle_in, exponent, in_min, in_max, deadzone) -> float:
        #debug(f"input angel: {angle_in}")

        value = range_map(angle_in, in_min, in_max, -1.0, 1.0)
        if abs(value) <= deadzone:
            value = 0
        else:
            value = value * (abs(value) ** (exponent - 1))

        return value

    def speed_map(self, value) -> float:
        """
        Maps speed values to vgamepad input
        Args:
            value: The speed value from 0 to 100

        Returns:
            The mapped value from 0.0 to 1.0
        """
        value = float(value) / 100
        return value if value <= 1.0 else 1.0

    def brake_map(self, value) -> float:
        """
        Maps brake values to vgamepad input
        Args:
            value: The brake value from 0 to 100

        Returns:
            The mapped value from 0.0 to 1.0
        """
        value = float(value) / 100
        return value if value <= 1.0 else 1.0
