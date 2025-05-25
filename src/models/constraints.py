from abc import ABC, abstractmethod
from typing import List, Tuple, Dict
from .grid import Grid, GRID_TYPE_OBSTACLE, GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_NORMAL_CHANNEL
from .vehicle import Vehicle, VEHICLE_STATUS_WAITING


class Constraint(ABC):
    """约束条件基类"""

    @abstractmethod
    def check(self, grid: Grid, vehicle: Vehicle, position: Tuple[int, int]) -> bool:
        """检查约束条件是否满足"""
        pass


class PhysicalConstraint(Constraint):
    """物理约束"""

    def __init__(self, restricted_positions: List[Tuple[int, int]]):
        self.restricted_positions = set(restricted_positions)

    def check(self, grid: Grid, vehicle: Vehicle, position: Tuple[int, int]) -> bool:
        """检查位置是否在物理限制区域内"""
        return position not in self.restricted_positions


class DirectionConstraint(Constraint):
    """方向约束"""

    def __init__(self, position: Tuple[int, int], allowed_directions: List[str]):
        self.position = position
        self.allowed_directions = allowed_directions

    def check(self, grid: Grid, vehicle: Vehicle, position: Tuple[int, int]) -> bool:
        """检查方向约束是否满足"""
        if position != self.position:
            return True

        cell = grid.get_cell(*position)
        if not cell:
            return False

        return all(direction in self.allowed_directions for direction in cell.allowed_directions)


class CargoConstraint(Constraint):
    """货物约束"""

    def check(self, grid: Grid, vehicle: Vehicle, position: Tuple[int, int]) -> bool:
        """检查货物约束是否满足"""
        cell = grid.get_cell(*position)
        if not cell:
            return False

        # 满车不能通过有货物的格子
        if not vehicle.is_empty() and cell.has_cargo:
            return False

        return True


class ChannelConstraint(Constraint):
    """通道约束"""

    def check(self, grid: Grid, vehicle: Vehicle, position: Tuple[int, int]) -> bool:
        """检查通道约束是否满足"""
        cell = grid.get_cell(*position)
        if not cell:
            return False

        # 检查格子类型
        if cell.grid_type == GRID_TYPE_OBSTACLE:
            return False

        if cell.grid_type == GRID_TYPE_MAIN_CHANNEL:
            # 主通道允许所有车辆通过
            return True

        if cell.grid_type == GRID_TYPE_NORMAL_CHANNEL:
            # 普通通道，空车可以穿行，满车不能通过有货物的格子
            if vehicle.is_empty():
                return True
            return not cell.has_cargo

        return False


class VehicleConflictConstraint(Constraint):
    """车辆冲突约束"""

    def __init__(self):
        self.vehicles: Dict[str, Vehicle] = {}  # 车辆ID到车辆对象的映射
        self.occupied_positions: Dict[Tuple[int, int], str] = {}  # 位置到车辆ID的映射
        self.active_paths: Dict[str, List[Tuple[int, int]]] = {}  # 车辆ID到活动路径的映射

    def add_vehicle(self, vehicle: Vehicle) -> None:
        """添加车辆到约束系统"""
        self.vehicles[vehicle.id] = vehicle
        if vehicle.path:
            self.active_paths[vehicle.id] = vehicle.path
        self._update_occupied_positions()

    def remove_vehicle(self, vehicle_id: str) -> None:
        """从约束系统中移除车辆"""
        if vehicle_id in self.vehicles:
            del self.vehicles[vehicle_id]
            if vehicle_id in self.active_paths:
                del self.active_paths[vehicle_id]
            self._update_occupied_positions()

    def _update_occupied_positions(self) -> None:
        """更新被占用的位置：将所有车辆的整条路径都视为占用"""
        self.occupied_positions.clear()
        for vehicle in self.vehicles.values():
            if vehicle.status != VEHICLE_STATUS_WAITING and vehicle.path:
                for pos in vehicle.path:
                    self.occupied_positions[pos] = vehicle.id
            elif vehicle.status != VEHICLE_STATUS_WAITING:
                # 如果没有路径，只占当前位置
                self.occupied_positions[vehicle.current_position] = vehicle.id

    def check(self, grid: Grid, vehicle: Vehicle, position: Tuple[int, int]) -> bool:
        """检查位置是否会发生冲突"""
        return position not in self.occupied_positions


class ConstraintManager:
    """约束管理器"""

    def __init__(self):
        self.constraints: List[Constraint] = []
        self.vehicle_conflict_constraint = VehicleConflictConstraint()
        self.add_constraint(self.vehicle_conflict_constraint)
        self.vehicles = []
        self.grid = None
        self.entrance_tasks = {}  # 记录每个入口的任务队列
        self.exit_tasks = {}  # 记录每个出口的任务队列

    def add_constraint(self, constraint: Constraint) -> None:
        """添加约束"""
        self.constraints.append(constraint)

    def remove_constraint(self, constraint: Constraint) -> None:
        """移除约束"""
        if constraint in self.constraints:
            self.constraints.remove(constraint)

    def check_all_constraints(self, grid: Grid, vehicle: Vehicle, position: Tuple[int, int]) -> bool:
        """检查所有约束条件，包括车辆冲突约束"""
        # 先检查所有通用约束
        basic_ok = all(constraint.check(grid, vehicle, position) for constraint in self.constraints)
        # 再单独检查车辆冲突约束（可选，防止被遗漏或被移除）
        vehicle_ok = self.vehicle_conflict_constraint.check(grid, vehicle, position)
        return basic_ok and vehicle_ok

    def add_vehicle(self, vehicle: Vehicle) -> None:
        """添加车辆到约束系统"""
        self.vehicle_conflict_constraint.add_vehicle(vehicle)
        if vehicle not in self.vehicles:
            self.vehicles.append(vehicle)

    def remove_vehicle(self, vehicle_id: str) -> None:
        """从约束系统中移除车辆"""
        self.vehicle_conflict_constraint.remove_vehicle(vehicle_id)
        self.vehicles = [v for v in self.vehicles if v.id != vehicle_id]

    def get_conflicting_vehicles(self, vehicle: Vehicle) -> List[Vehicle]:
        """获取与指定车辆发生冲突的所有车辆"""
        return self.vehicle_conflict_constraint.get_conflicting_vehicles(vehicle)

    def add_task(self, task):
        """添加任务到相应的队列"""
        if task.task_type == "inbound":
            # 入库任务添加到入口队列
            if task.start_position in self.entrance_tasks:
                self.entrance_tasks[task.start_position].append(task)
        else:
            # 出库任务添加到出口队列
            if task.end_position in self.exit_tasks:
                self.exit_tasks[task.end_position].append(task)

    def check_entrance_exit_order(self, task, position):
        """检查入口/出口的任务顺序约束"""
        if task.task_type == "inbound":
            # 检查入库任务是否按顺序执行
            entrance_tasks = self.entrance_tasks.get(task.start_position, [])
            if entrance_tasks and task != entrance_tasks[0]:
                return False, f"入口 {task.start_position} 的任务必须按顺序执行，当前任务不是队列中的第一个任务"
        else:
            # 检查出库任务是否按顺序执行
            exit_tasks = self.exit_tasks.get(task.end_position, [])
            if exit_tasks and task != exit_tasks[0]:
                return False, f"出口 {task.end_position} 的任务必须按顺序执行，当前任务不是队列中的第一个任务"
        return True, None

    def remove_task(self, task):
        """从队列中移除已完成的任务"""
        if task.task_type == "inbound":
            if task.start_position in self.entrance_tasks:
                self.entrance_tasks[task.start_position] = [t for t in self.entrance_tasks[task.start_position] if
                                                            t.id != task.id]
        else:
            if task.end_position in self.exit_tasks:
                self.exit_tasks[task.end_position] = [t for t in self.exit_tasks[task.end_position] if t.id != task.id]
