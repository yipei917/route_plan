import os
from typing import List, Tuple
from src.models.grid import GRID_TYPE_INTERFACE, GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_NORMAL_CHANNEL, Grid
from src.models.task import TASK_STATUS_PENDING, TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, TaskManager 
from src.models.vehicle import (VEHICLE_STATUS_AVOIDING, VEHICLE_STATUS_IDLE, VEHICLE_STATUS_PICKUP, VEHICLE_STATUS_DELIVER, 
    VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED, Vehicle)
from src.utils.constraints import ConstraintManager
from src.utils.visualizer import GridVisualizer
from src.utils.simulator import Simulator
from src.algorithms.a_star import AStarPlanner

class Scheduler:
    """调度器类，管理任务分配和路径规划"""

    def __init__(self, num_vehicles: int, step_size: int, output_path = "output"):
        self.grid = Grid(10, 10)
        self.task_manager = TaskManager()
        self.path_planner = AStarPlanner(self.grid)
        self.vehicles: List[Vehicle] = []
        self.num_vehicles = num_vehicles
        self.grid_visualizer = GridVisualizer(self.grid, figsize=(40,40))
        self.simulator = Simulator()
        self.constraint_manager = ConstraintManager()
        self.step_size = step_size
        self.output_path = output_path

    def initialize(self) -> None:
        """初始化地图、车辆、模拟器和约束"""
        # 加载地图
        self.grid.load_map_from_xlsx("resource/test_map.xlsx")
        self.task_manager.load_tasks_from_xlsx("resource/test_task.xlsx")

        # 创建输出目录
        os.makedirs(self.output_path, exist_ok=True)

        # 添加车辆
        vehicle_position = [(8,7), (10,7), (12,7), (14,7), (16,7), (18,7)]
        for i in range(self.num_vehicles):
            v = Vehicle(
                id=f"V{i+1}",
                vehicle_type=VEHICLE_TYPE_EMPTY,
                current_position=vehicle_position[i]
            )
            self.vehicles.append(v)
            self.grid_visualizer.add_vehicle(v)
            self.simulator.add_vehicle(v)

    def assign_task(self):
        pending_tasks = self.task_manager.get_tasks_by_status(TASK_STATUS_PENDING)
        idle_vehicles = [v for v in self.vehicles if v.status == VEHICLE_STATUS_IDLE]

        if not pending_tasks or not idle_vehicles:
            return

        for task in pending_tasks:
            for vehicle in idle_vehicles:
                # todo 车辆选择策略
                path_to_start = self.path_planner.find_path(vehicle, vehicle.current_position, task.start_position)
                if path_to_start is None: continue
                if vehicle.assign_task(task):
                    vehicle.set_full_planned_path(path_to_start)
                    self.assign_path(vehicle)
                    vehicle.set_target_position(task.start_position)
                    vehicle.start_task()
                    idle_vehicles.remove(vehicle)
                    print(f"任务 {task.id} 已分配给车辆 {vehicle.id}")
                    break
            else: print(f"任务 {task.id} 暂无可用车辆或所有车辆均无法到达")
        return

    def check_status(self):
        """检查车辆状态并处理状态转换"""
        for vehicle in self.vehicles:
            task = vehicle.current_task
            cell = self.grid.get_cell(vehicle.current_position[0], vehicle.current_position[1])
            on_main = cell is not None and (cell.grid_type == GRID_TYPE_MAIN_CHANNEL or cell.grid_type == GRID_TYPE_INTERFACE)
            
            if vehicle.status == VEHICLE_STATUS_AVOIDING and vehicle.current_position == vehicle.avoid_position:
                vehicle.avoid_position = None
                if task is None:
                    vehicle.status = VEHICLE_STATUS_IDLE
                else:
                    vehicle.status = VEHICLE_STATUS_PICKUP

            if vehicle.status == VEHICLE_STATUS_IDLE and on_main:
                self.constraint_manager.remove_path_constraint(vehicle)
                vehicle.clear_path()

            if task is None: continue

            # 检查车辆是否在起点或终点
            if vehicle.current_position == task.start_position and vehicle.is_empty():
                vehicle.vehicle_type = VEHICLE_TYPE_LOADED
                if task.task_type == TASK_TYPE_OUTBOUND:
                    self.grid.set_cargo(task.start_position[0], task.start_position[1], False)
                vehicle.status = VEHICLE_STATUS_DELIVER
                vehicle.set_target_position(task.end_position)
            elif vehicle.current_position == task.end_position and not vehicle.is_empty():
                vehicle.vehicle_type = VEHICLE_TYPE_EMPTY
                if task.task_type == TASK_TYPE_INBOUND:
                    self.grid.set_cargo(task.end_position[0], task.end_position[1], True)
                # 释放方向锁定
                self.constraint_manager.remove_direction_constraint(vehicle, self.grid)
                vehicle.status = VEHICLE_STATUS_IDLE
                vehicle.complete_task()

            # 检查车辆是否在主通道上
            if not on_main: continue
            
            target_position = vehicle.get_target_position()
            if target_position is None: continue
            path = self.path_planner.find_path(vehicle, vehicle.current_position, target_position)
            if path is None: continue
            vehicle.set_full_planned_path(path)
            self.constraint_manager.add_direction_constraint(vehicle, self.grid)
            self.assign_path(vehicle)

    def analyze_path_segments(self, path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """分析路径，将其分为主干道段和一般道路段"""
        if not path:
            return []
        
        num_main_channel = 0
        
        # 统计开头有多少个主通道
        for position in path:
            cell = self.grid.get_cell(position[0], position[1])
            if cell is None:
                break
            if cell.grid_type == GRID_TYPE_MAIN_CHANNEL or cell.grid_type == GRID_TYPE_INTERFACE:
                num_main_channel += 1
            else:
                break
            
        # 如果开头有多个主通道，则返回前step_size个主通道
        if num_main_channel > 1:
            return path[:min(num_main_channel, self.step_size)]
        # 进入子通道
        else:
            next_main_idx = None
            for idx, position in enumerate(path[1:], start=1):
                cell = self.grid.get_cell(position[0], position[1])
                if cell is None:
                    break
                if cell.grid_type == GRID_TYPE_MAIN_CHANNEL or cell.grid_type == GRID_TYPE_INTERFACE:
                    next_main_idx = idx
                    break
            if next_main_idx is not None:
                # 存在后续主通道，返回从开头主通道到下一个主通道，以及中间的子通道
                return path[0:next_main_idx+1]
            else:
                # 没有后续主通道，进去子通道再返回
                forward_path = path
                return_path = list(reversed(forward_path[:-1]))  # 不重复最后一个点
                return forward_path + return_path

    def assign_path(self, vehicle: Vehicle):
        """路径分配策略：主干道按step锁定，一般道路全部锁定"""
 
        full_path = vehicle.full_planned_path
        if not full_path:
            print(f"车辆 {vehicle.id} 没有规划路径")
            return

        # 分析路径段
        path_segments = self.analyze_path_segments(full_path)

        # 检查冲突
        conflicts = self.constraint_manager.check_path_conflicts(path_segments, vehicle)
        if conflicts:
            self.conflict_strategy(vehicle, conflicts)
            return
        
        # 添加路径约束
        self.constraint_manager.add_path_constraint(vehicle, path_segments)
        
        # 设置执行路径
        vehicle.set_current_execution_path(path_segments)

    def conflict_strategy(self, vehicle: Vehicle, conflicts: List[str]):
        conflict_vehicles = []
        all_empty = True
        working_in_normal_channel = False
        for conflict in conflicts:
            for v in self.vehicles:
                if v.id == conflict:
                    conflict_vehicles.append(v)
                    if v.is_empty():
                        if v.status == VEHICLE_STATUS_IDLE:
                            if not self.avoid_strategy(v):
                                print(f"车辆 {v.id} 避让失败，等待车辆 {v.id} 完成任务")
                                return
                        else:
                            cell = self.grid.get_cell(v.current_position[0], v.current_position[1])
                            if cell is None:
                                continue
                            if cell.grid_type == GRID_TYPE_NORMAL_CHANNEL:
                                working_in_normal_channel = True
                                break
                    else:
                        all_empty = False
                        break

        if working_in_normal_channel or not all_empty:
            print(f"车辆 {vehicle.id} 与车辆 {conflict_vehicles} 冲突，等待车辆 {conflict_vehicles} 完成任务")
            return
        
        if not vehicle.is_empty():
            for v in conflict_vehicles:
                print(f"车辆 {v.id} 为空，给车辆 {vehicle.id} 让路")
                if not self.avoid_strategy(v):
                    print(f"车辆 {v.id} 避让失败，等待车辆 {v.id} 完成任务")
                    return
        else:
            vehicle_direction = self.get_vehicle_direction(vehicle)
            for v in conflict_vehicles:
                if self.get_vehicle_direction(v) == vehicle_direction:
                    print(f"车辆 {v.id} 与车辆 {vehicle.id} 方向相同，等待车辆 {v.id} 完成任务")
                else:
                    print(f"车辆 {v.id} 与车辆 {vehicle.id} 方向不同，给车辆 {vehicle.id} 让路")
                    if not self.avoid_strategy(v):
                        print(f"车辆 {v.id} 避让失败，等待车辆 {v.id} 完成任务")
                        return

    def get_vehicle_direction(self, vehicle: Vehicle):
        next_position = vehicle.get_full_planned_path()[1]
        if next_position[0] > vehicle.current_position[0]:
            return "right"
        elif next_position[0] < vehicle.current_position[0]:
            return "left"

    def avoid_strategy(self, vehicle: Vehicle) -> bool:
        """避让策略：车辆去到附近的主干道，并且对应的格子没人占用"""
        print(f"\n=== 车辆 {vehicle.id} 执行避让策略 ===")
        print(f"当前位置: {vehicle.current_position}")
        
        # 获取当前车辆所在的主干道行
        x = vehicle.current_position[0]
        y = vehicle.current_position[1]
        
        # 获取所有主干道行
        main_rows = self.grid.main_channel_rows
        print(f"主干道行: {main_rows}")
        
        # 寻找附近可用的主干道位置
        available_positions = []
        
        for main_row in main_rows:
            if y == main_row:
                continue
            position = (x, main_row)
            if self.constraint_manager.position_locks.get(position) is None:
                # 计算与当前位置的距离
                distance = abs(main_row - y)  # 行距离
                available_positions.append((position, distance))
                print(f"  发现可用位置 {position}, 距离: {distance}")
        
        if not available_positions:
            print(f"  当前主干道列 {x} 没有可用位置")
            return False
        
        # 选择最近的可用位置
        available_positions.sort(key=lambda x: x[1])  # 按距离排序
        best_position = available_positions[0][0]
        distance = available_positions[0][1]
        
        print(f"  选择最佳避让位置: {best_position}, 距离: {distance}")
        
        # 规划到避让位置的路径
        path_to_avoid = self.path_planner.find_path(vehicle, vehicle.current_position, best_position)
        if path_to_avoid is None:
            print(f"  无法找到到避让位置 {best_position} 的路径")
            return False
        
        print(f"  避让路径: {' -> '.join(str(p) for p in path_to_avoid)}")
        
        # 检查避让路径是否有冲突
        conflicts = self.constraint_manager.check_path_conflicts(path_to_avoid, vehicle)
        if conflicts:
            print(f"  避让路径存在冲突: {conflicts}")
            return False

        # 添加路径约束
        self.constraint_manager.add_path_constraint(vehicle, path_to_avoid)
        vehicle.set_current_execution_path(path_to_avoid)
        vehicle.avoid_position = best_position
        vehicle.status = VEHICLE_STATUS_AVOIDING
        
        print(f"  避让策略执行成功，车辆 {vehicle.id} 将移动到 {best_position}")
        return True

    def run(self):
        self.grid_visualizer.visualize(self.output_path, "test_0.png")
        i = 1
        while True:
            print("--------------------------------")
            print(f"=== 第{i}次迭代 ===")
            print("--------------------------------")
            self.assign_task()
            if not self.simulator.simulate_step():
                print("所有任务均已完成，模拟结束")
                break
            self.check_status()
            self.grid_visualizer.visualize(self.output_path, f"test_{i}.png")
            i += 1
