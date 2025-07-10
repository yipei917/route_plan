from typing import List
from src.models.grid import Grid
from src.models.task import TaskManager
from src.models.constraints import ConstraintManager
from src.models.vehicle import Vehicle
from src.utils.visualizer import GridVisualizer
from src.algorithms.a_star import AStarPlanner

class Scheduler:
    """调度器类，管理任务分配和路径规划"""

    def __init__(self, num_vehicles: int, width: int = 11, height: int = 11):
        self.grid = Grid(width, height)
        self.task_manager = TaskManager()
        self.constraint_manager = ConstraintManager()
        self.path_planner = AStarPlanner(self.grid, self.constraint_manager)
        self.vehicles: List[Vehicle] = []
        self.num_vehicles = num_vehicles
        self.grid_visualizer = GridVisualizer(self.grid)

    def initialize(self) -> None:
        """初始化地图、车辆、模拟器和约束"""

        