from enum import Enum
from v2g_controller.helper import debug
from can import Message


class OperationMode(Enum):
    UDS = 0
    Internal = 1


class Type(Enum):
    Steering = 0
    Speed = 1
    Brake = 2
    Gear = 3
    Button = 4

class CANBus():
    def __init__(self, type, bitrate, data_bitrate=None):
        self.type = type
        self.bitrate = bitrate
        self.data_bitrate = data_bitrate

class CANSignal:
    """
    Initialize the object with the given id, byte, length, and mapping function.
    Attributes:
        id (int): CAN message ID
        byte (int): Byte position of signal
        length (int): The length of the signal in bytes.
        mapping (function, optional): A function to map the bythe data to the signal value,
                                      defaults to the identity function.
    """

    def __init__(self, id, byte, length, mapping=(lambda x: x)):
        self.id = id
        self.byte = byte
        self.length = length  # in byte
        self.mapping = mapping


def gear_change_matcher(val):
    if val == 0x40:
        # neutral
        return 0
    elif val == 0x50:
        # gear up
        return 1
    elif val == 0x60:
        # gear down
        return -1
    elif val == 0x70:
        # reverse
        return -2


def gear_change_matcher_uds(val):
    if val == 0x04:
        # neutral
        return 0
    elif val == 0x05:
        # completely up
        return 1
    elif val == 0x06:
        # gear up
        return 1
    elif val == 0x09:
        # gear down
        return -1
    elif val == 0x07:
        # reverse
        return -2

def tesla_gear_change_matcher(val):
    if val == 0x03:
        # neutral
        return 0
    elif val == 0x04:
        # drive (D)
        return 1
    elif val == 0x02:
        # reverse
        return -2


class PollingMessage:
    def __init__(
        self, arbitration_id: int, data, is_extended_id=False, polling_interval=0.03
    ):
        self.message = Message(
            arbitration_id=arbitration_id, data=data, is_extended_id=is_extended_id
        )
        self.interval = polling_interval


class SignalConfiguration:
    """
    Represents a configuration for the V2G controller.

    Parameters:
    id: The identifier of the configuration.
    name: The name of the configuration.
    can_signal: The CANSignal object associated with the configuration.
    type: The Type object associated with the type of the configuration.
    enabled: A boolean indicating whether the configuration is enabled (default True).
    buttons: Array of vgamepad.Buttons,
             only required for Type.Button (1 button required)
             and Type.Gear (two buttons required, gear_down and gear_up)
             (default []).
    ident_filter: UDS only: Configuration will only be applied
                  if can_data[2:3] == ident_filter
                  disabled on default
                  (default []).

    Attributes:
    id: The identifier of the configuration.
    name: The name of the configuration.
    enabled: A boolean indicating whether the configuration is enabled.
    type: The Type object associated with the type of the configuration.
    can_signal: The CANSignal associated with the configuration.
    buttons: Array of vgamepad.Buttons,
             only required for Type.Button (1 button required)
             and Type.Gear (two buttons required, gear_down and gear_up)
             (default []).
    ident_filter: UDS only: Configuration will only be applied
                  if can_data[2:3] == ident_filter
                  disabled on default
                  (default []).

    Methods:
    can_id(): Returns the CAN ID of can_signal.
    match(can_id): Checks if the provided CAN ID matches the configuration's CAN ID.
    value(payload): Interprets a can message payload and returns the mapped value.

    """

    def __init__(
        self,
        id,
        name,
        can_signal: CANSignal,
        type: Type,
        enabled=True,
        buttons=[],
        ident_filter:list[int]=[],
        ident_filter_mf:bool=False,
        cf_filter:list[int]=[],
    ):
        self.id = id
        self.name = name
        self.enabled = enabled
        self.type = type
        self.can_signal = can_signal
        self.buttons = buttons
        self.ident_filter = ident_filter
        self.ident_filter_mf = ident_filter_mf
        self.cf_filter = cf_filter

    def can_id(self):
        return self.can_signal.id

    def match(self, can_id):
        return self.can_signal.id == can_id

    def value(self, payload):
        #if self.name == "brake":
        #    debug(
        #        f"Value for {self.name} = {bytes(payload[self.can_signal.byte-1: self.can_signal.byte+self.can_signal.length-1]).hex()}")
        return self.can_signal.mapping(
            payload[
                self.can_signal.byte
                - 1 : self.can_signal.byte
                + self.can_signal.length
                - 1
            ]
        )


vehicle_configurations = {}


class VehicleConfiguration:
    def __init__(
        self,
        vehicle,
        operation_mode: OperationMode,
        can_buses: dict,
        steering_max: float,
        steering_deadzone: float,
        steering_exponent: float,
        configurations: list[SignalConfiguration],
        polling_interval_fast=None,
        polling_interval_slow=None,
        polling_messages=list[PollingMessage],
        auto_detect_ids=[],
        read_limiter=0
    ):
        self.vehicle = vehicle
        self.operation_mode = operation_mode
        self.can_buses = can_buses
        self.steering_max = steering_max
        self.steering_deadzone = steering_deadzone
        self.steering_exponent = steering_exponent
        self.auto_detect_ids = auto_detect_ids
        self.configurations = configurations
        self.polling_messages = polling_messages
        self.read_limiter = read_limiter
        if not self.polling_messages and self.operation_mode == OperationMode.UDS:
            print("Error: UDS-mode requires to specify the polling messages!")
            exit(-1)
        else:
            vehicle_configurations[self.vehicle] = self
