from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from src.models.grid import Grid
from src.models.vehicle import Vehicle
from src.models.constraints import ConstraintManager

class PathPlanner(ABC):
    """路径规划器基类"""
    def __init__(self, grid: Grid, constraint_manager: ConstraintManager):
        self.grid = grid
        self.constraint_manager = constraint_manager

    @abstractmethod
    def find_path(
        self,
        vehicle: Vehicle,
        start: Tuple[int, int],
        goal: Tuple[int, int]
    ) -> Optional[List[Tuple[int, int]]]:
        """寻找从起点到终点的路径"""
        pass

    def is_valid_position(self, position: Tuple[int, int], vehicle: Vehicle) -> bool:
        """检查位置是否有效"""
        # 检查是否在网格范围内
        if not (0 <= position[0] < self.grid.width and 0 <= position[1] < self.grid.height):
            return False

        # 检查是否满足所有约束条件
        return self.constraint_manager.check_all_constraints(self.grid, vehicle, position)

    def get_valid_neighbors(
        self,
        position: Tuple[int, int],
        vehicle: Vehicle
    ) -> List[Tuple[int, int]]:
        """获取有效的相邻位置"""
        neighbors = self.grid.get_neighbors(position[0], position[1], vehicle.is_empty())
        return [n for n in neighbors if self.is_valid_position(n, vehicle)]

    def calculate_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """计算两点之间的距离（曼哈顿距离）"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def reconstruct_path(
        self,
        came_from: dict,
        current: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """重建路径"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return list(reversed(path)) 