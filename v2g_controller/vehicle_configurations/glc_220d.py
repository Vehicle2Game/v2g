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


POLLING_INTERVAL_FAST = 0.05
POLLING_INTERVAL_SLOW = 0.3


config_uds = VehicleConfiguration(
    vehicle="GLC_220D",
    operation_mode=OperationMode.UDS,
    can_buses=[CANBus("standard", 500000)],
    steering_max=0.15,
    steering_deadzone=0.1,
    steering_exponent=1.0,
    auto_detect_ids=[0x87,0x133,0xb3,0x1e1,0x3d,0x225,0x2f,0xa1,0xa3,0xae,0x381],
    configurations=[
        SignalConfiguration(
            ## Steering Angle
            # UDS Request Message
            #  can0  745  [3]  22 02 51  - '".Q'
            # UDS Response Message
            # can0  725  [9]  62 02 51 20 25 00 00 00 00  - 'b.Q %....'
            # 0 deg = 20 00
            # nach link lower 
            # 0F BB
            # nach rechts higher
            # 30 CD
            id=0,
            name="steering",
            can_signal=CANSignal(
                id=0x726,
                byte=6,
                length=2,
                mapping=lambda x: range_map(
                    ((x[0] << 8) + x[1]), 0x0fbb, 0x30cd, -1.0, 1.0
                ),
            ),
            type=Type.Steering,
            ident_filter=[0x02, 0x00],
            ident_filter_mf=True,
        ),
        SignalConfiguration(
            1,
            "speed", 
            # Gaspedal
            #   can0       7E0   [8]  03 22 20 15 FF FF FF FF
            #   can0       7E8   [8]  05 62 20 15 03 84 02 00
            #                                      | 3 %
            CANSignal(
                0x7e8, 5, 1, mapping=(lambda x: x[0])
            ),
            type=Type.Speed,
            ident_filter=[0x20, 0x15],
        ),
        SignalConfiguration(
            # can0  7EA  [42]  62 20 02 00 01 00 00 03 00 00 47 00 FF 67 00 00 14 00 FF FF 01 FF FF 01 37 37 36 36 36 36 FD 68 00 FF FF 01 FF FF 01 FF FF 01  - 'b ........G..g..........776666.h..........'
            2,
            "brake",
            CANSignal(0x7ea, 4, 2, mapping=(lambda x: range_map(x[0] << 8) + x[1], 0x14,0x3208,0,100)),
            type=Type.Brake,
            cf_filter=[0x22]
        ),
        SignalConfiguration(
            # lichthupe
            #  can0       726   [8]  10 0B 62 02 03 02 00 00
            4,
            "nitro",
            CANSignal(0x726, 6, 1, mapping=(lambda x: 1 if x[0] == 0x02 else 0)),
            type=Type.Button,
            buttons=[Buttons.A],
            ident_filter=[0x02, 0x03],
            ident_filter_mf=True,
        ),
        SignalConfiguration(
            # Fernlicht
            #  can0       726   [8]  10 0B 62 02 03 01 00 00
            4,
            "nitro",
            CANSignal(0x726, 6, 1, mapping=(lambda x: 1 if x[0] == 0x01 else 0)),
            type=Type.Button,
            buttons=[Buttons.X],
            ident_filter=[0x02, 0x03],
            ident_filter_mf=True,
        ),
        SignalConfiguration(
            # Blinker links
            #   can0       723   [8]  10 0F 62 02 02 00 00 01
            5,
            "fire",
            CANSignal(0x723, 8, 1, mapping=(lambda x: 1 if x[0] == 0x01 else 0)),
            type=Type.Button,
            buttons=[Buttons.B],
            ident_filter=[0x02, 0x02],
            ident_filter_mf=True,
        ),
        SignalConfiguration(
            # Blinker rechts
            #  can0       723   [8]  10 0F 62 02 02 00 00 02
            7,
            "Y",
            CANSignal(0x723, 8, 1, mapping=(lambda x: 1 if x[0] == 0x02 else 0)),
            type=Type.Button,
            buttons=[Buttons.Y],
            ident_filter=[0x02, 0x02],
            ident_filter_mf=True,
        ),
    ],
    polling_messages=[
        PollingMessage(
            arbitration_id=0x746,
            data=[0x03, 0x22, 0x02, 0x00, 0xff, 0xff, 0xff, 0xff],
            is_extended_id=False,
            polling_interval=POLLING_INTERVAL_SLOW,
        ),
        #**
        PollingMessage(
            # Gaspedal
            #   can0       7E0   [8]  03 22 20 15 FF FF FF FF
            #   can0       7E8   [8]  05 62 20 15 03 84 02 00
            #                                      | 3 %
            arbitration_id=0x7e0,
            data=[0x03, 0x22, 0x20, 0x15, 0xff, 0xff, 0xff, 0xff],
            is_extended_id=False,
            polling_interval=POLLING_INTERVAL_FAST,
        ),
        PollingMessage(
            # Mute button, headlight, 
            #   can0       746   [8]  03 22 02 03 FF FF FF FF
            arbitration_id=0x746,
            data=[0x03, 0x22, 0x02, 0x03, 0xff, 0xff, 0xff, 0xff],
            is_extended_id=False,
            polling_interval=POLLING_INTERVAL_SLOW,
        ),
        PollingMessage(
            arbitration_id=0x743,
            #   can0       743   [8]  03 22 02 02 FF FF FF FF
            data=[0x03, 0x22, 0x02, 0x02, 0xff, 0xff, 0xff, 0xff],
            is_extended_id=False,
            polling_interval=POLLING_INTERVAL_SLOW,
        ),
#        PollingMessage(
#            # can0  7E2  [3]  22 20 02  - '" .'
#            arbitration_id=0x7e2,
#            data=[0x03, 0x22, 0x20, 0x02, 0xff, 0xff, 0xff, 0xff],
#            is_extended_id=False,
#            polling_interval=POLLING_INTERVAL_FAST,
#        )
        
    ]
)

# Anfrage
#   can0       743   [8]  03 22 02 02 FF FF FF FF
# Blinker links
#   can0       723   [8]  10 0F 62 02 02 00 00 01
# Blinker rechts
#  can0       723   [8]  10 0F 62 02 02 00 00 02


# Mute button
#  can0       746   [8]  03 22 02 03 FF FF FF FF
# 

# Mute + - buttons
# Request
#   can0       746   [8]  03 22 02 03 FF FF FF FF
# consec frame
#   can0       726   [8]  10 0B 62 02 03 00 00 00
#  can0       726   [8]  21 00 10 04 00 00 DE FE
#                  + (1) - (2) |   | mute Button   

# 
# Fernlicht
#   can0       726   [8]  10 0B 62 02 03 01 00 00
# lichthupe
#  can0       726   [8]  10 0B 62 02 03 02 00 00



# Bremse
# can0  7E2  [3]  22 20 02  - '" .'
# can0  7EA  [42]  62 20 02 00 01 00 00 03 00 00 47 00 FF 67 00 00 14 00 FF FF 01 FF FF 01 37 37 36 36 36 36 FD 68 00 FF FF 01 FF FF 01 FF FF 01  - 'b ........G..g..........776666.h..........'
#                                                                  |
# 00 14 bis 32 08
