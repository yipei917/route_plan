from typing import List
from src.models.grid import Grid
from src.models.vehicle import Vehicle

class Simulator:
    """模拟器类，管理车辆移动和状态更新"""

    def __init__(self):
        self.vehicles: List[Vehicle] = []

    def initialize(self, vehicles: List[Vehicle]):
        self.vehicles = vehicles

    def simulate_step(self) -> bool:
        """模拟一步，更新车辆位置"""

        return True

    def add_vehicle(self, vehicle: Vehicle):
        self.vehicles.append(vehicle)
