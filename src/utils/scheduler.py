from typing import List, Tuple
from src.models.grid import GRID_TYPE_INTERFACE, GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_NORMAL_CHANNEL, GRID_TYPE_UP_DOWN_CHANNEL, Grid
from src.models.task import TASK_STATUS_PENDING, TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, TaskManager 
from src.models.vehicle import (VEHICLE_STATUS_IDLE, VEHICLE_STATUS_PICKUP, VEHICLE_STATUS_DELIVER, 
    VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED, Vehicle)
from src.models.constraints import ConstraintManager
from src.utils.visualizer import GridVisualizer
from src.utils.simulator import Simulator
from src.algorithms.a_star import AStarPlanner
import os

class Scheduler:
    """调度器类，管理任务分配和路径规划"""

    def __init__(self, num_vehicles: int, step_size: int):
        self.grid = Grid(10, 10)
        self.task_manager = TaskManager()
        self.path_planner = AStarPlanner(self.grid)
        self.vehicles: List[Vehicle] = []
        self.num_vehicles = num_vehicles
        self.grid_visualizer = GridVisualizer(self.grid, figsize=(40,40))
        self.simulator = Simulator()
        self.constraint_manager = ConstraintManager()
        self.step_size = step_size

    def initialize(self) -> None:
        """初始化地图、车辆、模拟器和约束"""
        # 加载地图
        self.grid.load_map_from_xlsx("resource/test_map.xlsx")
        self.task_manager.load_tasks_from_xlsx("resource/test_task.xlsx")

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
        
    def visualize(self, filename: str) -> None:
        """可视化当前状态, 保存到output目录"""
        self.grid_visualizer.draw_grid()
        self.grid_visualizer.draw_vehicles()
        full_path = os.path.join("output", filename)
        self.grid_visualizer.save(full_path)

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
                    vehicle.start_task()
                    idle_vehicles.remove(vehicle)
                    print(f"任务 {task.id} 已分配给车辆 {vehicle.id}")
                    break
            else: print(f"任务 {task.id} 暂无可用车辆或所有车辆均无法到达")
        return

    def check_status(self):
        for vehicle in self.vehicles:
            task = vehicle.current_task
            if task is None: continue

            # 检查车辆是否在起点或终点
            if vehicle.current_position == task.start_position and vehicle.is_empty():
                vehicle.vehicle_type = VEHICLE_TYPE_LOADED
                if task.task_type == TASK_TYPE_OUTBOUND:
                    self.grid.set_cargo(task.start_position[0], task.start_position[1], False)
                vehicle.status = VEHICLE_STATUS_DELIVER
            elif vehicle.current_position == task.end_position and not vehicle.is_empty():
                vehicle.vehicle_type = VEHICLE_TYPE_EMPTY
                if task.task_type == TASK_TYPE_INBOUND:
                    self.grid.set_cargo(task.end_position[0], task.end_position[1], True)
                # 释放方向锁定
                self.constraint_manager.remove_direction_constraint(vehicle, self.grid)
                vehicle.status = VEHICLE_STATUS_IDLE
                vehicle.complete_task()

            # 检查车辆是否在主通道上
            cell = self.grid.get_cell(vehicle.current_position[0], vehicle.current_position[1])
            if cell is None or cell.grid_type == GRID_TYPE_NORMAL_CHANNEL:
                continue
            
            if vehicle.status == VEHICLE_STATUS_PICKUP:
                path = self.path_planner.find_path(vehicle, vehicle.current_position, task.start_position)
                if path is None: continue
                vehicle.set_full_planned_path(path)
                self.assign_path(vehicle)
            elif vehicle.status == VEHICLE_STATUS_DELIVER:
                path = self.path_planner.find_path(vehicle, vehicle.current_position, task.end_position)
                if path is None: continue
                vehicle.set_full_planned_path(path)
                self.constraint_manager.add_direction_constraint(vehicle, self.grid)
                self.assign_path(vehicle)
            elif vehicle.status == VEHICLE_STATUS_IDLE:
                # todo 闲置车辆处理
                self.constraint_manager.remove_path_constraint(vehicle)
            

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
            if cell.grid_type == GRID_TYPE_MAIN_CHANNEL or cell.grid_type == GRID_TYPE_INTERFACE or cell.grid_type == GRID_TYPE_UP_DOWN_CHANNEL:
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
                if cell.grid_type == GRID_TYPE_MAIN_CHANNEL or cell.grid_type == GRID_TYPE_INTERFACE or cell.grid_type == GRID_TYPE_UP_DOWN_CHANNEL:
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
            # todo 避让算法，等待算法
            print(f"路径冲突，与车辆 {set(conflicts)} 冲突")
            print("需要重新规划路径或等待")
            return
        
        # 添加路径约束
        self.constraint_manager.add_path_constraint(vehicle, path_segments)
        
        # 设置执行路径
        vehicle.set_current_execution_path(path_segments)

    def run(self):
        self.visualize("test_0.png")
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
            self.visualize(f"test_{i}.png")
            i += 1
