import heapq
from typing import List, Tuple, Optional, Dict, Set
from .base import PathPlanner
from src.models.vehicle import Vehicle

class AStarPlanner(PathPlanner):
    """A*路径规划器"""
    def __init__(self, grid, constraint_manager, occupied_grids=None):
        super().__init__(grid, constraint_manager)
        self.occupied_grids = occupied_grids if occupied_grids is not None else set()

    def is_valid_position(self, position, vehicle):
        if self.occupied_grids and position in self.occupied_grids:
            return False
        return super().is_valid_position(position, vehicle)

    def find_path(
        self,
        vehicle: Vehicle,
        start: Tuple[int, int],
        goal: Tuple[int, int]
    ) -> Optional[List[Tuple[int, int]]]:
        """使用A*算法寻找从起点到终点的路径"""
        # 初始化开放列表和关闭列表
        open_set: List[Tuple[float, int, Tuple[int, int]]] = []  # (f_score, counter, position)
        closed_set: Set[Tuple[int, int]] = set()
        counter = 0  # 用于在f_score相同时比较位置

        # 初始化距离字典
        g_score: Dict[Tuple[int, int], float] = {start: 0}  # 从起点到当前点的实际距离
        f_score: Dict[Tuple[int, int], float] = {start: self.calculate_distance(start, goal)}  # 估计的总距离
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}  # 记录路径

        # 将起点加入开放列表
        heapq.heappush(open_set, (f_score[start], counter, start))
        counter += 1

        while open_set:
            # 获取f_score最小的节点
            current_f, _, current = heapq.heappop(open_set)

            # 如果到达目标点，重建并返回路径
            if current == goal:
                return self.reconstruct_path(came_from, current)

            # 将当前节点加入关闭列表
            closed_set.add(current)

            # 遍历相邻节点
            for neighbor in self.get_valid_neighbors(current, vehicle):
                if neighbor in closed_set:
                    continue

                # 计算从起点经过当前节点到相邻节点的距离
                tentative_g_score = g_score[current] + self.calculate_distance(current, neighbor)

                # 如果是新节点或找到更好的路径
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    # 更新路径信息
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.calculate_distance(neighbor, goal)

                    # 将相邻节点加入开放列表
                    if not any(neighbor == pos for _, _, pos in open_set):
                        heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))
                        counter += 1

        # 如果没有找到路径，返回None
        return None

    def calculate_heuristic(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """计算启发式函数值（曼哈顿距离）"""
        return self.calculate_distance(pos1, pos2) 