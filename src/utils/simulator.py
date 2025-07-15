from typing import List
from src.models.vehicle import VEHICLE_STATUS_WAITING, VEHICLE_STATUS_MOVING, Vehicle

class Simulator:
    """模拟器类，管理车辆移动和状态更新"""

    def __init__(self):
        self.vehicles: List[Vehicle] = []

    def simulate_step(self):
        """模拟一步，更新车辆位置"""
        active_vehicles = [v for v in self.vehicles if v.status in (VEHICLE_STATUS_WAITING, VEHICLE_STATUS_MOVING)]
        
        if len(active_vehicles) == 0:
            return False
        
        for v in active_vehicles:
            next_pos = v.get_next_position()
            if next_pos:
                v.current_path_index += 1
                v.update_position(next_pos)
                
        return True

    def add_vehicle(self, vehicle: Vehicle):
        self.vehicles.append(vehicle)
