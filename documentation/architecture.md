# V2G Architecture

## Hardware Setup

```puml
@startuml
rectangle Laptop as l
rectangle "PCAN-USB-PRO" as pcan

rectangle "Raspberry Pi Zero WH" as rpi {
    rectangle "CAN hat" as can_hat
    rectangle "ODB-II hat" as obd_hat
    can_hat - obd_hat
}
rectangle Car {
    rectangle "OBD-II Port" as obd
    rectangle ECU_0
    rectangle ECU_1
    rectangle ECU_2
    rectangle "Gateway ECU" as gw
}


l - pcan
pcan -- obd
obd_hat -l- obd
obd - gw
gw -- ECU_0
gw -- ECU_1
gw -- ECU_2

@enduml
```

## Software Architecture
```puml
@startuml

package v2g_controller {
    [main] as m
    [car_detector] as d
    [car_connector] as c
    [configuration_helper] as ch

    () run as r
    () install_bt as i
    () requirements.txt as req

    i .> r: autostart
    r -> m: execute
    r ..> req: install if missing

    m -> d: (1) detect_vehicle
    d --> ch: uses
    m --> ch: (2) load_configuration
    m --> c: (3)  run
    c ..> gamepads: update_gamepad_state
    ch ..> vehicle_configurations
}

node gamepads {
    [hidpi]
    i ..> hidpi: install
    [vgamepad-wrapper]

}

package vehicle_configurations {
    [id3]
    [tesla_model_3]
    [glc_220]

}

@enduml
```

```puml
package hidpi {
        (helper_script)
        (sdp_record_gamepad)
        (hid.service)
        (settings.xml)
        [hid] as hh
        [main] as hm
        [service] as hs

        hm -> hs
        hm --> hh
    }

```

## Vehicle Configuration

```puml
@startyaml
vehicle: "ID3_UDS"
oparation_mode: OperationMode.UDS
can_busses:
    - CANBus:
        type: "standard
        bitrate: 500000
steering_max: 0.15
steering_deadzone: 0.1
steering_exponent: 1.0
configurations:
    - SignalConfiguration:
        id: 0
        name: "steering"
        can_signal:
            id: 0x77C
            byte: 5
            length: 2
            mapping: "lambda x: (x[0] << 8) + x[1]"
        type: Type.Steering
	- SignalConfiguration:...
	- ...
polling_messages:
    - PollingMessage:
        arbitration_id: 0x70C
        data: [0x03, 0x22, 0x4F, ...]
        is_extended_id: False
        polling_interval: 0.01
    - PollingMessage:...
    - ...
@endyaml
```