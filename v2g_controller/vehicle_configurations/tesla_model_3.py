from v2g_controller.configuration_helper import (
    SignalConfiguration,
    CANSignal,
    CANBus,
    PollingMessage,
    OperationMode,
    Type,
    VehicleConfiguration,
    tesla_gear_change_matcher,
)
from v2g_controller.helper import range_map
from v2g_controller.gamepads.abstract_gamepad import Buttons


def tm3_brake_helper(x) -> float:
    if x[0] & 0b00000011 == 0:    
        if (x[4] & 0b00001100) > 1:
            tm3_brake_helper.tm3_previous_brake = 100
        else:
            tm3_brake_helper.tm3_previous_brake = 0
    return tm3_brake_helper.tm3_previous_brake
tm3_brake_helper.tm3_previous_brake = 0
    
config_internal = VehicleConfiguration(
    vehicle="TESLA_MODEL_3",
    operation_mode=OperationMode.Internal,
    can_buses=[CANBus("standard", 500000)],
    steering_max=0.08,
    steering_deadzone=0.1,
    steering_exponent=1.0,
    read_limiter=10,
    auto_detect_ids=[0x1d8, 0x261, 0x288, 0x129, 0x545, 0x257, 0x118, 0x3c2],
    configurations=[
        SignalConfiguration(
            id=0,
            name="steering",
            can_signal=CANSignal(
                id=297,
                byte=3, # Bit 16
                length=2, # 14 bits
                #  SG_ SCCM_steeringAngle: 16|14@1+ (0.1,-819.2) [0|0] "deg" X
                mapping=(
                    lambda x: range_map(
                        ((((int(x[1]) & 0b00111111) << 8) + x[0]) * 0.1 - 819.2),
                        -819.2, 819.2, -1.0, 1.0)
                )
            ),
            type=Type.Steering,
        ),
        SignalConfiguration(
            id=1,
            name="speed",
            can_signal=CANSignal(
                id=0x118,
                byte=5, # Bit 32
                length=1,
                mapping=(lambda x: x[0] * 0.4), # Pedal position in %
            ),
            type=Type.Speed,
        ),
        SignalConfiguration(
            id=2,
            name="brake",
            # currentl window left down, does not work well because of signal overloading
            can_signal=CANSignal(
                0x3c2, 1, 5, mapping=(lambda x: tm3_brake_helper(x) )
            ),
            type=Type.Brake,
        ),
        SignalConfiguration(
            id=3,
            name="gear",
            can_signal=CANSignal(
                0x118, 3, 1, mapping=(lambda x: tesla_gear_change_matcher(x[0] >> 5))
            ),
            type=Type.Gear,
            buttons=[Buttons.DOWN, Buttons.UP],
        ),
        SignalConfiguration(
            id=4,
            name="nitro",
            #  SG_ VCFRONT_lowBeamLeftStatus : 28|2@1+ (1,0) [0|3] ""  Receiver
            can_signal=CANSignal(
                0x3f5, 4, 1, mapping=(lambda x: (x[0] & 0b00010000) >> 4)
            ),
            type=Type.Button,
            buttons=[Buttons.A],
        ),
        SignalConfiguration(
            id=5,
            #  SG_ VCFRONT_indicatorLeftRequest : 0|2@1+ (1,0) [0|2] ""  Receiver
            name="fire",  # fire = blinker left
            can_signal=CANSignal(
                0x3f5, 1, 1, mapping=(lambda x: 1 if x[0] == 2 or x[0] == 1 else 0)
            ),
            type=Type.Button,
            buttons=[Buttons.B],
        ),
        SignalConfiguration(
            id=6,
            name="buttonX",
            can_signal=CANSignal(
                0x3f5, 1, 1, mapping=(lambda x: 1 if (x[0] == 4 or x[0] == 8) else 0)
            ),
            type=Type.Button,
            buttons=[Buttons.X],
        ),
    ],
)
