from typing import List, Tuple, Optional, Dict, Set
from src.models.grid import Grid
from src.models.vehicle import Vehicle
from src.models.constraints import ConstraintManager
import heapq

class AStarPlanner:
    def __init__(self, grid: Grid, constraint_manager: ConstraintManager):
        self.grid = grid
        self.constraint_manager = constraint_manager

    @staticmethod
    def calculate_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """曼哈顿距离"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    @staticmethod
    def reconstruct_path(came_from: dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """重建路径"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return list(reversed(path))

    def is_valid_position(self, position: Tuple[int, int], vehicle: Vehicle) -> bool:
        """检查位置是否有效"""
        if not (0 <= position[0] < self.grid.width and 0 <= position[1] < self.grid.height):
            return False
        return self.constraint_manager.check_all_constraints(self.grid, vehicle, position)

    def get_valid_neighbors(self, position: Tuple[int, int], vehicle: Vehicle) -> List[Tuple[int, int]]:
        """获取有效的相邻位置"""
        neighbors = self.grid.get_neighbors(position[0], position[1], vehicle.is_empty())
        return [n for n in neighbors if self.is_valid_position(n, vehicle)]

    def find_path(
        self,
        vehicle: Vehicle,
        start: Tuple[int, int],
        goal: Tuple[int, int]
    ) -> Optional[List[Tuple[int, int]]]:
        """A*算法寻找路径"""
        open_set: List[Tuple[float, int, Tuple[int, int]]] = []
        closed_set: Set[Tuple[int, int]] = set()
        counter = 0

        g_score: Dict[Tuple[int, int], float] = {start: 0}
        f_score: Dict[Tuple[int, int], float] = {start: self.calculate_distance(start, goal)}
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}

        heapq.heappush(open_set, (f_score[start], counter, start))
        counter += 1

        while open_set:
            _, _, current = heapq.heappop(open_set)
            if current == goal:
                return self.reconstruct_path(came_from, current)
            closed_set.add(current)
            for neighbor in self.get_valid_neighbors(current, vehicle):
                if neighbor in closed_set:
                    continue
                tentative_g = g_score[current] + self.calculate_distance(current, neighbor)
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.calculate_distance(neighbor, goal)
                    if not any(neighbor == pos for _, _, pos in open_set):
                        heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))
                        counter += 1
        return None