from v2g_controller.configuration_helper import (
    SignalConfiguration,
    CANSignal,
    CANBus,
    PollingMessage,
    OperationMode,
    Type,
    VehicleConfiguration,
    gear_change_matcher,
    gear_change_matcher_uds,
)
from v2g_controller.helper import range_map
from v2g_controller.gamepads.abstract_gamepad import Buttons


# *** Internal mode configuration ***
config_internal = VehicleConfiguration(
    vehicle="ID3_INTERNAL",
    operation_mode=OperationMode.Internal,
    can_buses=[CANBus("fd", 500000, 2000000), CANBus("standard", 500000)],
    steering_max=0.15,
    steering_deadzone=0.1,
    steering_exponent=1.0,
    configurations=[
        SignalConfiguration(
            id=0,
            name="steering",
            can_signal=CANSignal(
                id=0xFC,
                byte=24,
                length=2,
                mapping=(
                    lambda x: range_map(
                        -1 * x[0] if x[0] > 0x00 else x[1], -255, 255, -1.0, 1.0
                    )
                ),
            ),
            type=Type.Steering,
        ),
        SignalConfiguration(
            id=1,
            name="speed",
            can_signal=CANSignal(
                id=0x14C,
                byte=22,
                length=1,
                mapping=(lambda x: int((100 * (x[0] - 0x25)) / 0xB5)),
            ),
            type=Type.Speed,
        ),
        SignalConfiguration(
            id=2,
            name="brake",
            can_signal=CANSignal(
                0x176, 6, 1, mapping=(lambda x: ((100 * (x[0] - 0x01)) / 0x50))
            ),
            type=Type.Brake,
        ),
        SignalConfiguration(
            id=3,
            name="gear",
            can_signal=CANSignal(
                0xB5, 6, 1, mapping=(lambda x: gear_change_matcher(x[0]))
            ),
            type=Type.Gear,
            buttons=[Buttons.DOWN, Buttons.UP],
        ),
        SignalConfiguration(
            id=4,
            name="nitro",
            can_signal=CANSignal(
                0x658, 2, 1, mapping=(lambda x: 1 if x[0] == 0x70 else 0)
            ),
            type=Type.Button,
            buttons=[Buttons.A],
        ),
        SignalConfiguration(
            id=5,
            name="fire",  # fire = blinker left, this is somewhat suboptimal, as it will always be activated 3 times
            can_signal=CANSignal(
                0x658, 7, 1, mapping=(lambda x: 1 if x[0] == 0x12 else 0)
            ),
            type=Type.Button,
            buttons=[Buttons.B],
        ),
    ],
)


# *** UDS mode configuration ***
POLLING_INTERVAL_FAST = 0.03
POLLING_INTERVAL_SLOW = 0.3

config_uds = VehicleConfiguration(
    vehicle="ID3_UDS",
    operation_mode=OperationMode.UDS,
    can_buses=[CANBus("standard", 500000)],
    auto_detect_ids=[0x77c, 0x77d, 0x7a5,0x776],
    steering_max=0.15,
    steering_deadzone=0.1,
    steering_exponent=1.0,
    configurations=[
        SignalConfiguration(
            id=0,
            name="steering",
            can_signal=CANSignal(
                id=0x77C,
                byte=5,
                length=2,
                mapping=lambda x: -range_map(
                    ((x[0] << 8) + x[1]), 0x0000, 0x2EDF, -1.0, 1.0
                ),
            ),
            type=Type.Steering,
        ),
        SignalConfiguration(
            1,
            "speed",
            CANSignal(
                0x77D, 5, 1, mapping=(lambda x: int((100 * (x[0] - 0x25)) / 0xB5))
            ),
            type=Type.Speed,
        ),
        SignalConfiguration(
            2,
            "brake",
            CANSignal(0x7A5, 7, 2, mapping=(lambda x: (100 * (((x[0] <<8) + ((x[1] - 0x75) if x[1] - 0x75 > 0 else 0)) / 0x5E1)))),
            type=Type.Brake,
            ident_filter=[0x62, 0x47]
        ),
        SignalConfiguration(
            3,
            "gear",
            CANSignal(0x776, 5, 1, mapping=(lambda x: gear_change_matcher_uds(x[0]))),
            type=Type.Gear,
            buttons=[Buttons.DOWN, Buttons.UP],
            ident_filter=[0x4F, 0xE4],
        ),
        SignalConfiguration(
            4,
            "nitro",
            CANSignal(0x776, 5, 1, mapping=(lambda x: 1 if x[0] == 0x01 else 0)),
            type=Type.Button,
            buttons=[Buttons.A],
            ident_filter=[0x1F, 0x02],
        ),
        SignalConfiguration(
            5,
            "fire",
            CANSignal(0x776, 5, 1, mapping=(lambda x: 1 if x[0] == 0x02 else 0)),
            type=Type.Button,
            buttons=[Buttons.B],
            ident_filter=[0x1F, 0x00],
        ),
        SignalConfiguration(
            6,
            "X",
            CANSignal(0x776, 5, 1, mapping=(lambda x: 1 if x[0] == 0x01 else 0)),
            type=Type.Button,
            buttons=[Buttons.X],
            ident_filter=[0x1F, 0x00],
        ),
        SignalConfiguration(
            7,
            "Y",
            CANSignal(0x776, 5, 1, mapping=(lambda x: 1 if x[0] == 0x02 else 0)),
            type=Type.Button,
            buttons=[Buttons.Y],
            ident_filter=[0x1F, 0x02],
        ),
    ],
    polling_messages=[
        PollingMessage(
            arbitration_id=0x70C,
            data=[0x03, 0x22, 0x4F, 0xE4, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False,
            polling_interval=POLLING_INTERVAL_FAST,
        ),
        PollingMessage(
            arbitration_id=0x713,
            data=[0x03, 0x22, 0xF4, 0x49, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False,
            polling_interval=POLLING_INTERVAL_FAST,
        ),
        PollingMessage(
            arbitration_id=0x73B,
            data=[0x03, 0x22, 0x47, 0xD4, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False,
            polling_interval=POLLING_INTERVAL_FAST,
        ),
        PollingMessage(
            arbitration_id=0x712,
            # arbitration_id=0x74E,
            data=[0x03, 0x22, 0x18, 0x12, 0x55, 0x55, 0x55, 0x55],
            # data=[0x03, 0x22, 0x39, 0x0C, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False,
            polling_interval=POLLING_INTERVAL_FAST,
        ),
        PollingMessage(
            arbitration_id=0x70C,
            data=[0x03, 0x22, 0x1F, 0x00, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False,
            polling_interval=POLLING_INTERVAL_SLOW,
        ),
        PollingMessage(
            arbitration_id=0x70C,
            data=[0x03, 0x22, 0x1F, 0x02, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False,
            polling_interval=POLLING_INTERVAL_SLOW,
        ),
        PollingMessage(
            arbitration_id=0x73B,
            data=[0x2, 0x10, 0x03, 0x55, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False,
            polling_interval=POLLING_INTERVAL_SLOW
        )
    ]
)
