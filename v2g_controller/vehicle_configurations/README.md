# Vehicle Configuration Guide

To configure a new vehicle, first, make sure you have access to a CAN bus with the required information. 

Copy the ID.3 configuration `id3.py` and rename your copy in a meaningful way, i.e. `your_vehicle.py`. Make sure the new file is located in the `vehicle_configurations` folder.

Configuration files are python files. That makes it more easy and flexible to specify signal mappings.

## Header
At the beginning of the file, the required python files and classes are imported. No changes should be required here.
```python
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
```

## Internal Mode Configuration

If you do not want to configure the internal mode, but UDS mode only, this section can be deleted (up to the line with the comment ``# *** UDS mode configuration ***``).

Otherwise, here you can configure the internal mode. 
### General Configuration
```python
# *** Internal mode configuration ***
config_internal = VehicleConfiguration(
    vehicle="ID3_INTERNAL", # Name of the vehicle configuration
    operation_mode=OperationMode.Internal, # This config is for Internal mode
    can_buses=[CANBus("fd", 500000, 2000000), CANBus("standard", 500000)],
    steering_max=0.15, # Limits the used steering angle
    steering_deadzone=0.1, # More tolerance for 0 degree steering
    steering_exponent=1.0, # Exponential steering behavior
    auto_detect_ids=[], # List of IDs that are used for automatic vehicle identification. Disabled for this vehicle if left empty.
    [...]
```
- Replace ``ID3_INTERNAL` with an identifier for your vehicle. This name will be used to reference the config, i.e. if you would run `./run VEHICLE_NAME`.
- Specify the required required CAN buses as follows: <br>
  CAN: ``CANBus("standard", <bitrate>)``<br>
  CAN FD: ``CANBus("fd", <bitrate>, <data rate>)``<br>
  Replace `<bitrate>` and `<data rate>` with the corresponding values.
  The CANBus Python class is defined in [configuration_helper.py](../configuration_helper.py).
- `steering_max`<br>
  With this parameter, the maximal steering angle can be fine-tuned. For example, in the ID.3, the steering wheel can be turned two times in either direction. Doing so is way to slow for gaming. We usually use roughly $1/3$ of a wheel turn for maximum steering.
  A value of `0.15` means that 15% of the maximum angle will already result in maximum steering force.
  *We recommend to define the signals first before changing this parameter*
- `steering_deadzone`<br>
  It is often difficult to position the steering wheel exactly at 0 degree. This parameter is used to add some tolerance here as a constant left or right movement is quite annoying in menus.
  *We recommend to define the signals first before changing this parameter*
- `steering_exponent`<br>
  For configuring an exponential steering curve. Leave at `1.0` if in doubt.
- `auto_detect_ids`<br>
  Provide a list of CAN IDs that are used for automatic vehicle identification. The presence of the IDs should uniquely identify the vehicle out of all configured vehicles. If left empty, auto-detection is disabled for this vehicle.

Next, the signals have to be configured. In general, signals require a CAN message ID, a Bit position and length, and a mapping from the signal value to the expected range.

You can use the `range_map` function as an helper. 
```python
range_map(<input_value>, <input_min>, <input_max>, <output_min>, <output_max>)
```

### Steering
```python
        SignalConfiguration(
            id=0, # reference, no change required
            name="steering", # identifies the signal, no change required
            can_signal=CANSignal(
                id=0xFC, # CAN message ID
                byte=24, # Bit position (counting starts at 1!)
                length=2, # Signal length (in Bytes)
                mapping=( # from signal value to [-1.0,1.0]
                    lambda x: range_map(
                        -1 * x[0] if x[0] > 0x00 else x[1], -255, 255, -1.0, 1.0
                    )
                ),
            ),
            type=Type.Steering, # Used as steering signal, range [-1.0,1.0], no change required
        ),
```
In this example, the first byte of the signal encodes steering to the left while the second bytes encodes steering to the right. We map steering to a value from `-1.0` to `1.0`. The steering direction is represented by the sign. If the first byte is non-zero (steering to the left), we multiply its value by `-1`, else, we use the second byte. Next we have to specify the minimum and maximum of the input range. Here, this is `-255` (complete steering to left) and `255` complete steering to right. The output range should be left at `[-1.0, 1.0]`.

### Pedals (Speed, Brake)
```python
        SignalConfiguration(
            1, # reference, no change required
            "speed", # identifies signal, no change required
            CANSignal(
                0x77D, # CAN message ID
                5, # Bit position (start counting at 1)
                1, # Length in Byte
                # mapping from signal value to [0,100]
                mapping=(lambda x: int((100 * (x[0] - 0x25)) / 0xB5))
            ),
            type=Type.Speed, # Speed pedal, range [0,100], no change required
        ),
```

### Gear shift (optional)
```python
        SignalConfiguration(
            id=3, # reference, no change required
            name="gear",  # identifies signal, no change required
            can_signal=CANSignal(
                0xB5, # CAN message ID
                6, # Bit position (start counting at 1)
                1, # Length in Byte
                # Configure your own gear change matcher function
                mapping=(lambda x: gear_change_matcher(x[0]))
            ),
            type=Type.Gear,  # Gear type, no change required
            buttons=[Buttons.DOWN, Buttons.UP], # Button mapping for XBOX controller emulation
        ),
```

### Buttons (Nitro, Fire, X, Y, ...)
```python
        SignalConfiguration(
            id=4, # reference, no change required
            name="nitro", # identifies signal
            can_signal=CANSignal(
                0x658, # CAN message ID
                2, # Bit position (start counting at 1)
                1, # Length in Byte
                # mapping from signal value to 0 (not pressed) or 1 (pressed)
                mapping=(lambda x: 1 if x[0] == 0x70 else 0)
            ),
            type=Type.Button, # Button, value 0 or 1, no change required
            buttons=[Buttons.A], # Button mapping for XBOX controller emulation
        ),
```

## UDS Mode Configuration

UDS mode is similar to internal mode, but requires some additional settings:

### Polling Intervals

In UDS mode, the information is periodically queried from the vehicle. The polling intervals are configurable. ``POLLING_INTERVAL_FAST`` is used for signals that require high resolution, such as steering, and ``POLLING_INTERVAL_SLOW`` for queries were lower resolution is sufficient, such as buttons.
```python
# *** UDS mode configuration ***
POLLING_INTERVAL_FAST = 0.03 # in seconds
POLLING_INTERVAL_SLOW = 0.3 # in seconds
```

### General Configuration
Same as for internal mode.
```python
config_uds = VehicleConfiguration(
    vehicle="ID3_UDS", # Name of the vehicle configuration
    operation_mode=OperationMode.UDS, # This config is for UDS mode
    can_buses=[CANBus("standard", 500000)],
    auto_detect_ids=[0x77c, 0x77d, 0x7a5,0x776], # List of IDs that are used for automatic vehicle identification. 
    steering_max=0.15, # Limits the used steering angle
    steering_deadzone=0.1, # More tolerance for 0 degree steering
    steering_exponent=1.0,  # (No) Exponential steering behavior
    [...]
```

### Signal Configuration
Compared to internal mode, additional `ident_filter`s are used to enable filtering for individual UDS services and data identifiers (DIDs).

```python
            ident_filter=[0x62, 0x47] # ReadDataByIdentifier reply (0x62), DID 0x47
```
Currently, we assume that the data is included in the first ISO-TP packet of the message.

### Polling messages
To request the data from the vehicle, UDS requests are sent periodically to the vehicle (using the  `ReadDataByIdentifier` service). A list of these request messages has to be provided.

```python
polling_messages=[
        PollingMessage(
            arbitration_id=0x70C, # CAN message ID
            data=[0x03, 0x22, 0x4F, 0xE4, 0x55, 0x55, 0x55, 0x55], # Complete CAN message data
            is_extended_id=False, # True if extended ID is used
            polling_interval=POLLING_INTERVAL_FAST, # Slow or fast interval. Use ``POLLING_INTERVAL_SLOW`` for low resolution, and ``POLLING_INTERVAL_FAST`` for high resolution.

        [...]
```