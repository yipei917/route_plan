from typing import List, Tuple, Dict
from .vehicle import Vehicle
from .grid import GRID_TYPE_MAIN_CHANNEL, MAIN_CHANNEL_STATUS_LEFT, MAIN_CHANNEL_STATUS_RIGHT, MAIN_CHANNEL_STATUS_NULL

class ConstraintManager:
    """约束管理器 - 管理车辆路径冲突检测、坐标锁定和方向锁定"""

    def __init__(self):
        self.position_locks: Dict[Tuple[int, int], str] = {}
        self.direction_locks: Dict[Tuple[int, int], str] = {}

    def add_path_constraint(self, vehicle: Vehicle, path: List[Tuple[int, int]]) -> None:
        """添加限制路径，锁定路径中的每个坐标"""

        print(f"\n=== 为车辆 {vehicle.id} 添加路径约束 ===")
        print(f"路径: {' -> '.join(str(p) for p in path)}")
        
        # 先清除车辆之前的路径约束
        self.remove_path_constraint(vehicle)
        
        # 锁定新路径中的所有坐标
        for position in path:
            self.position_locks[position] = vehicle.id

    def add_vehicle_constraint(self, vehicle: Vehicle) -> None:
        """为车辆添加路径约束"""
        self.position_locks[vehicle.current_position] = vehicle.id

    def add_direction_constraint(self, vehicle: Vehicle, grid) -> None:
        """为负载车辆添加方向锁定约束"""
        
        if vehicle.is_empty():
            return  # 空载车辆不需要方向锁定
            
        print(f"\n=== 为负载车辆 {vehicle.id} 添加方向锁定 ===")
        
        # 清除车辆之前的方向锁定
        self.remove_direction_constraint(vehicle, grid)
        
        # 获取车辆的完整路径
        full_path = vehicle.get_full_planned_path()
        
        # 分析路径中的主通道段
        main_channel_positions = []
        for i, position in enumerate(full_path):
            cell = grid.get_cell(position[0], position[1])
            if cell and cell.grid_type == GRID_TYPE_MAIN_CHANNEL:
                main_channel_positions.append(position)
        
        # 根据主通道位置判断方向
        for i, position in enumerate(main_channel_positions):
            direction = MAIN_CHANNEL_STATUS_NULL
            
            # 判断方向：比较当前主通道位置与下一个主通道位置
            if i < len(main_channel_positions) - 1:
                next_position = main_channel_positions[i + 1]
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
                self.direction_locks[position] = vehicle.id       
                self.direction_locks[next_position] = vehicle.id

    def remove_path_constraint(self, vehicle: Vehicle) -> None:
        """删除车辆的所有约束信息"""
        
        print(f"\n=== 释放车辆 {vehicle.id} 的路径约束 ===")
        
        # 获取车辆锁定的所有坐标
        locked_positions = [pos for pos, vid in self.position_locks.items() if vid == vehicle.id]
        
        print(f"车辆 {vehicle.id} 锁定的位置: {locked_positions}")
        
        # 从位置锁定表中删除这些坐标
        for position in locked_positions:
            del self.position_locks[position]

    def remove_direction_constraint(self, vehicle: Vehicle, grid) -> None:
        """删除车辆的方向锁定约束"""
        
        # 获取车辆锁定的所有方向
        locked_directions = [pos for pos, vid in self.direction_locks.items() if vid == vehicle.id]
        
        # 从方向锁定表中删除这些位置
        for position in locked_directions:
            del self.direction_locks[position]
            grid.get_cell(position[0], position[1]).main_channel_status = MAIN_CHANNEL_STATUS_NULL

    def check_path_conflicts(self, path: List[Tuple[int, int]], vehicle: Vehicle) -> List[str]:
        """检测路径冲突"""

        print(f"\n=== 检测车辆 {vehicle.id} 的路径冲突 ===")
        print(f"检查路径: {' -> '.join(str(p) for p in path)}")
        
        # 检查路径中是否有冲突
        conflicting_vehicles = []
        conflict_positions = []
        
        for position in path:
            if position in self.position_locks and self.position_locks[position] != vehicle.id:
                conflicting_vehicle_id = self.position_locks[position]
                conflicting_vehicles.append(conflicting_vehicle_id)
                conflict_positions.append((position, conflicting_vehicle_id))
                print(f"  冲突位置 {position}: 被车辆 {conflicting_vehicle_id} 锁定")
        
        if conflicting_vehicles:
            unique_conflicts = list(set(conflicting_vehicles))
            print(f"发现冲突: 与车辆 {unique_conflicts} 在 {len(conflict_positions)} 个位置冲突")
            print(f"冲突详情:")
            for position, vehicle_id in conflict_positions:
                print(f"  - 位置 {position}: 被车辆 {vehicle_id} 占用")
        else:
            print(f"未发现路径冲突")
        
        return conflicting_vehicles
