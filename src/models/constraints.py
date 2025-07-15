from typing import List, Tuple, Dict
from .vehicle import Vehicle

class ConstraintManager:
    """约束管理器 - 管理车辆路径冲突检测和坐标锁定"""

    def __init__(self):
        self.position_locks: Dict[Tuple[int, int], str] = {}

    def add_path_constraint(self, vehicle: Vehicle, path: List[Tuple[int, int]]) -> None:
        """添加限制路径，锁定路径中的每个坐标"""

        print(f"\n=== 为车辆 {vehicle.id} 添加路径约束 ===")
        print(f"路径: {' -> '.join(str(p) for p in path)}")
        
        # 如果车辆已有锁定的坐标，先清除
        if vehicle.id in self.position_locks:
            self.remove_path_constraint(vehicle)
        
        # 锁定新路径中的所有坐标
        for position in path:
            self.position_locks[position] = vehicle.id

    def remove_path_constraint(self, vehicle: Vehicle) -> None:
        """删除车辆的所有约束信息"""
        
        # 获取车辆锁定的所有坐标
        locked_positions = [pos for pos, vid in self.position_locks.items() if vid == vehicle.id]
        
        # 从位置锁定表中删除这些坐标
        for position in locked_positions:
            del self.position_locks[position]

    def check_path_conflicts(self, path: List[Tuple[int, int]]) -> List[str]:
        """检测路径冲突"""

        # 检查路径中是否有冲突
        conflicting_vehicles = []
        for position in path:
            if position in self.position_locks:
                conflicting_vehicles.append(self.position_locks[position])
        
        return conflicting_vehicles


    

