import os
from typing import List, Tuple
from src.models.grid import GRID_TYPE_INTERFACE, GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_NORMAL_CHANNEL, GRID_TYPE_UP_DOWN_CHANNEL, Grid
from src.models.task import TASK_STATUS_PENDING, TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, TaskManager 
from src.models.vehicle import (VEHICLE_STATUS_AVOIDING, VEHICLE_STATUS_IDLE, VEHICLE_STATUS_PICKUP, 
    VEHICLE_STATUS_DELIVER, VEHICLE_STATUS_WAITING, VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED, Vehicle)
from src.utils.constraints import ConstraintManager
from src.utils.visualizer import GridVisualizer
from src.utils.simulator import Simulator
from src.algorithms.a_star import AStarPlanner

class Scheduler:
    """调度器类，管理任务分配和路径规划"""

    def __init__(self, num_vehicles: int, step_size: int, output_path = "output"):
        self.grid = Grid(10, 10)
        self.num_vehicles = num_vehicles
        self.step_size = step_size
        self.output_path = output_path
        self.vehicles: List[Vehicle] = []
        self.task_manager = TaskManager()
        self.path_planner = AStarPlanner(self.grid)
        self.grid_visualizer = GridVisualizer(self.grid, figsize=(40,40))
        self.simulator = Simulator()
        self.constraint_manager = ConstraintManager()

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
            self.constraint_manager.add_vehicle_constraint(v)

    def assign_task(self):
        """分配任务"""
        # 获取待分配任务和空闲车辆
        pending_tasks = self.task_manager.get_tasks_by_status(TASK_STATUS_PENDING)
        idle_vehicles = [v for v in self.vehicles if v.status == VEHICLE_STATUS_IDLE]

        # 如果无任务或无空闲车辆，则返回
        if not pending_tasks or not idle_vehicles:
            return

        # 遍历待分配任务，为每个任务分配车辆
        for task in pending_tasks:
            # 如果无空闲车辆，则返回
            if not idle_vehicles:
                return

            # todo 车辆选择策略
            for vehicle in idle_vehicles:
                # 规划到起点路径
                path_to_start = self.path_planner.find_path(vehicle, vehicle.current_position, task.start_position)
                if path_to_start is None: continue

                # 分配任务
                if vehicle.assign_task(task):
                    # 设置目标位置和完整路径
                    vehicle.set_target_position(task.start_position)
                    vehicle.set_full_planned_path(path_to_start)

                    # 分配路径、开始任务
                    self.assign_path(vehicle)
                    vehicle.start_task()
                    print(f"任务 {task.id} 已分配给车辆 {vehicle.id}")

                    # 从空闲车辆列表中移除已分配车辆
                    idle_vehicles.remove(vehicle)
                    break
            else: print(f"任务 {task.id} 暂无可用车辆或所有车辆均无法到达")
        return

    def check_status(self):
        """检查车辆状态并处理状态转换"""
        # 优先处理处于负载状态的车辆
        loaded_vehicles = [v for v in self.vehicles if v.vehicle_type == VEHICLE_TYPE_LOADED]
        empty_vehicles = [v for v in self.vehicles if v.vehicle_type == VEHICLE_TYPE_EMPTY]
        ordered_vehicles = loaded_vehicles + empty_vehicles

        for vehicle in ordered_vehicles:
            task = vehicle.current_task
            on_main = self.grid.get_cell_type(vehicle.current_position) == GRID_TYPE_MAIN_CHANNEL or self.grid.get_cell_type(vehicle.current_position) == GRID_TYPE_INTERFACE
            
            # 避让完成
            if vehicle.status == VEHICLE_STATUS_AVOIDING and vehicle.current_position == vehicle.avoid_position:
                vehicle.avoid_position = None
                vehicle.clear_path()
                self.constraint_manager.remove_path_constraint(vehicle)
                if task is None:
                    vehicle.status = VEHICLE_STATUS_IDLE
                else:
                    vehicle.status = VEHICLE_STATUS_PICKUP
                expeller = next((v for v in self.vehicles if v.id == vehicle.expeller), None)
                if expeller is not None: # todo 递归等待处理
                    if not expeller.remove_from_waiting_list(vehicle.id):
                        expeller.status = expeller.last_status
                        self.planning_path(expeller)

            # 车辆空闲
            if vehicle.status == VEHICLE_STATUS_IDLE and on_main:
                self.constraint_manager.remove_path_constraint(vehicle)
                vehicle.clear_path()
                self.constraint_manager.add_vehicle_constraint(vehicle)

            # 确保车辆有任务
            if task is None: continue

            # 车辆在起点或终点
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
            
            # 车辆在主通道上，规划路径
            self.planning_path(vehicle)

    def planning_path(self, vehicle: Vehicle):
        target_position = vehicle.get_target_position()
        if target_position is None: return
        path = self.path_planner.find_path(vehicle, vehicle.current_position, target_position)
        if path is None: return
        vehicle.set_full_planned_path(path)
        self.constraint_manager.add_direction_constraint(vehicle, self.grid)
        self.assign_path(vehicle)

    def analyze_path_segments(self, path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """分析路径，返回需要锁定的路径段"""
        if not path: return []
        
        # 统计开头有多少个主通道
        num_main_channel = 0
        for position in path:
            if self.grid.get_cell_type(position) == GRID_TYPE_MAIN_CHANNEL or self.grid.get_cell_type(position) == GRID_TYPE_INTERFACE:
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
                if self.grid.get_cell_type(position) == GRID_TYPE_MAIN_CHANNEL or self.grid.get_cell_type(position) == GRID_TYPE_INTERFACE:
                    next_main_idx = idx
                    break

            # 存在后续主通道，返回从开头主通道到下一个主通道，以及中间的子通道
            if next_main_idx is not None:
                return path[0:next_main_idx+1]

            # 没有后续主通道，进去子通道再返回
            else:
                forward_path = path
                return_path = list(reversed(forward_path[:-1]))  # 不重复最后一个点
                return forward_path + return_path

    def assign_path(self, vehicle: Vehicle):
        """路径分配策略：主干道按step_size锁定，一般道路全部锁定"""
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

    def conflict_strategy(self, vehicle: Vehicle, conflicts: List[str]): # todo 避让失败处理
        # 获取冲突车辆
        conflict_vehicles = [v for v in self.vehicles if v.id in conflicts]

        # 检查冲突车辆是否在主干道且全空
        all_empty = True
        working_in_normal_channel = False
        same_row = True

        for conflict_vehicle in conflict_vehicles:
            if conflict_vehicle.current_position[1] != vehicle.current_position[1]:
                same_row = False
                break
            if conflict_vehicle.is_empty():
                if conflict_vehicle.status != VEHICLE_STATUS_IDLE:
                    grid_type = self.grid.get_cell_type(conflict_vehicle.current_position)
                    if grid_type == GRID_TYPE_NORMAL_CHANNEL or grid_type == GRID_TYPE_UP_DOWN_CHANNEL:
                        working_in_normal_channel = True
                        break
            else:
                all_empty = False
                break

        if working_in_normal_channel or not all_empty or not same_row:
            print(f"车辆 {vehicle.id} 与车辆 {', '.join(v.id for v in conflict_vehicles)} 冲突，等待车辆 {', '.join(v.id for v in conflict_vehicles)} 完成任务")
            return
        
        # 冲突车辆给非空车让路
        if not vehicle.is_empty():
            for conflict_vehicle in conflict_vehicles:
                print(f"车辆 {conflict_vehicle.id} 给车辆 {vehicle.id} 让路")
                if not self.avoid_strategy(conflict_vehicle, vehicle):
                    print(f"车辆 {conflict_vehicle.id} 避让失败，等待车辆 {conflict_vehicle.id} 完成任务")
                    return
        # 冲突车辆给对向空车让路
        else:
            vehicle_direction = self.get_vehicle_direction(vehicle)
            for conflict_vehicle in conflict_vehicles:
                if self.get_vehicle_direction(conflict_vehicle) == vehicle_direction:
                    print(f"车辆 {conflict_vehicle.id} 与车辆 {vehicle.id} 方向相同，等待车辆 {conflict_vehicle.id} 完成任务")
                else:
                    print(f"车辆 {conflict_vehicle.id} 与车辆 {vehicle.id} 方向不同，给车辆 {vehicle.id} 让路")
                    if not self.avoid_strategy(conflict_vehicle, vehicle):
                        print(f"车辆 {conflict_vehicle.id} 避让失败，等待车辆 {conflict_vehicle.id} 完成任务")
                        return

    def get_vehicle_direction(self, vehicle: Vehicle):
        if not vehicle.full_planned_path: return None
        next_position = vehicle.get_full_planned_path()[1]
        if next_position[0] > vehicle.current_position[0]:
            return "right"
        elif next_position[0] < vehicle.current_position[0]:
            return "left"

    def avoid_strategy(self, avoid_vehicle: Vehicle, expeller: Vehicle) -> bool:
        """避让策略：车辆去到附近的主干道，并且对应的格子没人占用"""
        print(f"\n=== 车辆 {avoid_vehicle.id} 执行避让策略 ===")
        print(f"当前位置: {avoid_vehicle.current_position}")
        
        # 获取当前车辆所在的主干道行
        x = avoid_vehicle.current_position[0]
        y = avoid_vehicle.current_position[1]
        
        # 获取所有主干道行
        main_rows = self.grid.main_channel_rows
        
        # 寻找附近可用的主干道位置
        available_positions = []
        
        for main_row in main_rows:
            if y == main_row: continue
            position = (x, main_row)
            if self.constraint_manager.position_locks.get(position) is None and self.path_planner.find_path(avoid_vehicle, avoid_vehicle.current_position, position) is not None:
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
        path_to_avoid = self.path_planner.find_path(avoid_vehicle, avoid_vehicle.current_position, best_position)
        print(f"  避让路径: {' -> '.join(str(p) for p in path_to_avoid)}")
        
        # 检查避让路径是否有冲突
        conflicts = self.constraint_manager.check_path_conflicts(path_to_avoid, avoid_vehicle)
        if conflicts:
            print(f"  避让路径存在冲突: {', '.join(v.id for v in conflicts)}")
            return False

        # 添加路径约束
        self.constraint_manager.add_path_constraint(avoid_vehicle, path_to_avoid)
        avoid_vehicle.set_current_execution_path(path_to_avoid)

        # 设置避让状态
        avoid_vehicle.avoid_position = best_position
        avoid_vehicle.status = VEHICLE_STATUS_AVOIDING
        avoid_vehicle.set_expeller(expeller.id)
        expeller.add_to_waiting_list(avoid_vehicle.id)
        expeller.last_status = expeller.status
        expeller.status = VEHICLE_STATUS_WAITING
        
        print(f"  避让策略执行成功，车辆 {avoid_vehicle.id} 将移动到 {best_position}")
        return True

    def run(self, visualize: bool = True):
        if visualize: self.grid_visualizer.visualize(self.output_path, "test_0.png")
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
            if visualize: self.grid_visualizer.visualize(self.output_path, f"test_{i}.png")
            i += 1
