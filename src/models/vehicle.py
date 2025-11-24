from typing import Optional, Tuple, List
from dataclasses import dataclass, field

# 车辆类型常量
VEHICLE_TYPE_EMPTY = "empty"
VEHICLE_TYPE_LOADED = "loaded"

@dataclass
class Vehicle:
    """
    车辆数据模型
    
    用于路径规划的车辆状态表示，包含车辆的位置、负载状态和规划路径信息。
    """
    id: str                                                   # 车辆标识
    vehicle_type: str                                         # 车辆类型：VEHICLE_TYPE_EMPTY 或 VEHICLE_TYPE_LOADED
    current_position: Tuple[int, int]                        # 当前位置 (x, y)
    target_position: Optional[Tuple[int, int]] = None        # 目标位置 (x, y)
    full_planned_path: List[Tuple[int, int]] = field(default_factory=list)       # 完整规划路径
    current_execution_path: List[Tuple[int, int]] = field(default_factory=list)  # 当前执行路径
    current_path_index: int = 0                              # 当前路径索引

    def is_empty(self) -> bool:
        """
        判断车辆是否为空载状态
        
        Returns:
            bool: 如果车辆为空载返回 True，否则返回 False
        """
        return self.vehicle_type == VEHICLE_TYPE_EMPTY

    def set_full_planned_path(self, path: List[Tuple[int, int]]) -> None:
        """
        设置完整规划路径
        
        Args:
            path: 路径节点列表 [(x1, y1), (x2, y2), ...]
        """
        self.full_planned_path = path if path else []

    def get_full_planned_path(self) -> List[Tuple[int, int]]:
        """
        获取完整规划路径
        
        Returns:
            路径节点列表
        """
        return self.full_planned_path

    def set_current_execution_path(self, path: List[Tuple[int, int]]) -> None:
        """
        设置当前执行路径
        
        Args:
            path: 路径节点列表
        """
        if not path:
            self.current_execution_path = []
            self.current_path_index = 0
            return
        
        self.current_execution_path = path
        self.current_path_index = 0

    def get_next_position(self) -> Optional[Tuple[int, int]]:
        """
        获取下一个位置
        
        Returns:
            下一个位置坐标，如果已到达路径终点则返回 None
        """
        if self.current_path_index + 1 >= len(self.current_execution_path):
            return None
        return self.current_execution_path[self.current_path_index + 1] if self.current_execution_path else None

    def set_target_position(self, target: Tuple[int, int]) -> None:
        """
        设置目标位置
        
        Args:
            target: 目标坐标 (x, y)
        """
        self.target_position = target

    def get_target_position(self) -> Optional[Tuple[int, int]]:
        """
        获取目标位置
        
        Returns:
            目标坐标，如果未设置则返回 None
        """
        return self.target_position

    def update_position(self, new_position: Tuple[int, int]) -> None:
        """
        更新车辆位置
        
        Args:
            new_position: 新位置坐标 (x, y)
        """
        self.current_position = new_position

    def clear_path(self) -> None:
        """清除所有路径信息"""
        self.full_planned_path = []
        self.current_execution_path = []
        self.current_path_index = 0
