from typing import List, Tuple, Dict, Set
from src.models.vehicle import Vehicle
from src.models.grid import GRID_TYPE_MAIN_CHANNEL, MAIN_CHANNEL_STATUS_LEFT, MAIN_CHANNEL_STATUS_RIGHT, MAIN_CHANNEL_STATUS_NULL

class ConstraintManager:
    """
    约束管理器
    
    管理车辆路径的冲突检测、位置锁定和方向锁定。
    用于多车协同场景下的路径冲突预防和解决。
    
    Attributes:
        position_locks: 位置锁定字典 {(x, y): vehicle_id}
        direction_locks: 方向锁定字典 {(x, y): {vehicle_id, ...}}
    """

    def __init__(self):
        """初始化约束管理器"""
        self.position_locks: Dict[Tuple[int, int], str] = {}
        self.direction_locks: Dict[Tuple[int, int], Set[str]] = {}

    def add_path_constraint(self, vehicle: Vehicle, path: List[Tuple[int, int]]) -> None:
        """
        添加路径约束，锁定路径中的每个坐标
        
        Args:
            vehicle: 车辆对象
            path: 要锁定的路径
        """
        # 先清除车辆之前的路径约束
        self.remove_path_constraint(vehicle)
        
        # 锁定新路径中的所有坐标
        for position in path:
            self.position_locks[position] = vehicle.id

    def add_vehicle_constraint(self, vehicle: Vehicle) -> None:
        """
        为车辆当前位置添加约束
        
        Args:
            vehicle: 车辆对象
        """
        self.position_locks[vehicle.current_position] = vehicle.id

    def add_direction_constraint(self, vehicle: Vehicle, grid) -> None:
        """
        为负载车辆添加方向锁定约束
        
        仅对负载车辆生效，在主通道上建立方向锁，防止对向车辆进入。
        
        Args:
            vehicle: 车辆对象
            grid: 网格地图对象
        """
        # 空载车辆不需要方向锁定
        if vehicle.is_empty():
            return  
        
        # 清除车辆之前的方向锁定约束
        self.remove_direction_constraint(vehicle, grid)
        
        # 获取车辆的完整路径
        full_path = vehicle.get_full_planned_path()
        
        # 分析路径中的主通道段
        main_channel_positions = []
        for i, position in enumerate(full_path):
            if grid.get_cell_type(position) == GRID_TYPE_MAIN_CHANNEL:
                main_channel_positions.append(position)
        
        # 根据主通道位置判断方向
        for i, position in enumerate(main_channel_positions): 
            # 判断方向：比较当前主通道位置与下一个主通道位置
            if i < len(main_channel_positions) - 1:
                direction = MAIN_CHANNEL_STATUS_NULL
                next_position = main_channel_positions[i + 1]

                # 不在同一行，跳过
                if next_position[1] != position[1]:
                    continue
                
                # 计算方向
                dx = next_position[0] - position[0]
                if dx > 0:
                    direction = MAIN_CHANNEL_STATUS_RIGHT
                elif dx < 0:
                    direction = MAIN_CHANNEL_STATUS_LEFT

                # 更新主通道状态
                grid.get_cell(position[0], position[1]).main_channel_status = direction
                grid.get_cell(next_position[0], next_position[1]).main_channel_status = direction
                
                # 添加到方向锁定表
                if position not in self.direction_locks:
                    self.direction_locks[position] = set()
                self.direction_locks[position].add(vehicle.id)
                if next_position not in self.direction_locks:
                    self.direction_locks[next_position] = set()
                self.direction_locks[next_position].add(vehicle.id)

    def remove_path_constraint(self, vehicle: Vehicle) -> None:
        """
        删除车辆的所有路径约束
        
        Args:
            vehicle: 车辆对象
        """
        # 获取车辆锁定的所有坐标
        locked_positions = [pos for pos, vid in self.position_locks.items() if vid == vehicle.id]
        
        # 从位置锁定表中删除这些坐标
        for position in locked_positions:
            del self.position_locks[position]

    def remove_direction_constraint(self, vehicle: Vehicle, grid) -> None:
        """
        删除车辆的方向锁定约束
        
        Args:
            vehicle: 车辆对象
            grid: 网格地图对象
        """
        # 获取车辆锁定的所有方向位置
        locked_directions = []
        for position, vehicle_ids in self.direction_locks.items():
            if vehicle.id in vehicle_ids:
                locked_directions.append(position)
        
        # 从方向锁定表中删除该车辆
        for position in locked_directions:
            self.direction_locks[position].discard(vehicle.id)
            
            # 如果没有其他车辆锁定该位置，则设置为NULL
            if not self.direction_locks[position]:
                del self.direction_locks[position]
                grid.get_cell(position[0], position[1]).main_channel_status = MAIN_CHANNEL_STATUS_NULL


    def check_path_conflicts(self, path: List[Tuple[int, int]], vehicle: Vehicle) -> List[str]:
        """
        检测路径冲突
        
        Args:
            path: 要检查的路径
            vehicle: 车辆对象
            
        Returns:
            冲突车辆ID列表，如果无冲突则返回空列表
        """
        # 检查路径中是否有冲突
        conflicting_vehicles = []
        
        for position in path:
            if position in self.position_locks and self.position_locks[position] != vehicle.id:
                conflicting_vehicle_id = self.position_locks[position]
                if conflicting_vehicle_id not in conflicting_vehicles:
                    conflicting_vehicles.append(conflicting_vehicle_id)
        
        return conflicting_vehicles
