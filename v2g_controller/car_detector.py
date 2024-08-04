import can
import v2g_controller.main as main
from v2g_controller.helper import debug
from v2g_controller.configuration_helper import vehicle_configurations
from v2g_controller.configuration_helper import OperationMode
import time
import v2g_controller.vehicle_configurations.configuration_id3 as id3


import v2g_controller.configuration_helper as cfh

class CarDetector(can.Listener):
    def __init__(self):
        self.vehicle = "NONE"
        self.tesla_ctr = 0
        self.can_ids = dict[int:bool]()

    def on_message_received(self, msg: can.Message):
        self.can_ids[msg.arbitration_id] = True
        
            
    def get_vehicle(self, operation_mode):
        if self.vehicle == "NONE":
            for vehicle in vehicle_configurations:
                if not vehicle_configurations[vehicle].operation_mode == operation_mode:
                    continue
                if vehicle_configurations[vehicle].auto_detect_ids.__len__() < 1:
                    continue
                debug(f"Vehicle: {vehicle_configurations[vehicle].vehicle}")
                match = True  
                for key in vehicle_configurations[vehicle].auto_detect_ids:
                    if not key in self.can_ids:
                        debug(f"Key {hex(key)} not found in can_ids for vehicle {vehicle}")
                        match = False
                if match:
                    self.vehicle = vehicle
                    return self.vehicle
                
        return self.vehicle
    
    def polling_messages(self):
        polling_messages = []
        for vehicle in vehicle_configurations:
            if not vehicle_configurations[vehicle].operation_mode == OperationMode.UDS:
                continue
            polling_messages.extend(vehicle_configurations[vehicle].polling_messages)
        return polling_messages



def detect_vehicle():
    debug("Trying to automatically detect the vehicle...")    
    detector = CarDetector()
    with main.init_can_bus(0, "standard", 500000) as bus:
            notifier = can.Notifier(bus, [detector])
            time.sleep(1)
            if detector.get_vehicle(OperationMode.Internal) == "NONE":
                debug("No vehicle detected for internal mode, trying UDS mode")
                
                try: 
                    for msg in detector.polling_messages():
                        bus.send(msg.message)
                except can.CanOperationError as error:
                    debug("Auto-detection via UDS failed!")
                    debug(error)
                time.sleep(0.5)
                detector.get_vehicle(OperationMode.UDS)
            notifier.stop()
    
    debug(f"Detected vehicle: {detector.vehicle}")
    return detector.vehicle
