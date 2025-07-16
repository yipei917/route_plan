from typing import List, Tuple
from src.models.grid import GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_NORMAL_CHANNEL, Grid
from src.models.task import TASK_STATUS_PENDING, TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, TaskManager 
from src.models.vehicle import VEHICLE_STATUS_IDLE, VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED, Vehicle
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

        # todo 确保车辆在主通道上
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
            # 检查车辆是否空闲
            if vehicle.status == VEHICLE_STATUS_IDLE:
                continue
            
            # todo 检查车辆是否在主通道上
            # 检查车辆是否在主通道上
            # if self.grid.get_cell(vehicle.current_position[0], vehicle.current_position[1]) != GRID_TYPE_MAIN_CHANNEL:
            #     continue

            # 检查车辆是否有当前任务
            if vehicle.current_task is None:
                continue
                
            task = vehicle.current_task
            
            # 当车辆到达起始位置时
            if vehicle.current_position == task.start_position:
                if vehicle.vehicle_type == VEHICLE_TYPE_EMPTY:  # 确保车辆是空载状态
                    # 车辆载起货物
                    vehicle.vehicle_type = VEHICLE_TYPE_LOADED
                    # 更新起始位置格子的货物信息
                    if task.task_type == TASK_TYPE_OUTBOUND:
                        self.grid.set_cargo(task.start_position[0], task.start_position[1], False)
                    # 规划去终点的路径
                    path_to_end = self.path_planner.find_path(vehicle, task.start_position, task.end_position)
                    if path_to_end:
                        vehicle.set_full_planned_path(path_to_end)
                        self.assign_path(vehicle)
                    else:
                        print(f"车辆 {vehicle.id} 无法找到到终点 {task.end_position} 的路径")
            
            # 当车辆到达终点位置时
            elif vehicle.current_position == task.end_position:
                if vehicle.vehicle_type == VEHICLE_TYPE_LOADED:  # 确保车辆是载货状态
                    # 更新终点位置格子的货物信息（货物被放下）
                    if task.task_type == TASK_TYPE_INBOUND:
                        self.grid.set_cargo(task.end_position[0], task.end_position[1], True)
                    # 车辆变为空载
                    vehicle.vehicle_type = VEHICLE_TYPE_EMPTY
                    # 结束任务
                    vehicle.complete_task()

    def analyze_path_segments(self, path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """分析路径，将其分为主干道段和一般道路段"""
        if not path:
            return []
        
        num_main_channel = 0
        
        # 统计开头有多少个main
        for position in path:
            cell = self.grid.get_cell(position[0], position[1])
            if cell is None:
                break
            if cell.grid_type == GRID_TYPE_MAIN_CHANNEL:
                num_main_channel += 1
            else:
                break
            
        # 如果开头有多个main，则返回前step_size个main
        if num_main_channel > 1:
            return path[:min(num_main_channel, self.step_size)]
        else:
            main_start_idx = 0  # 已知开头是main
            next_main_idx = None
            for idx, position in enumerate(path[1:], start=1):
                cell = self.grid.get_cell(position[0], position[1])
                if cell is None:
                    break
                if cell.grid_type == GRID_TYPE_MAIN_CHANNEL:
                    next_main_idx = idx
                    break
            if next_main_idx is not None:
                # 存在后续main，返回从开头main到下一个main（包含），以及中间的normal
                return path[main_start_idx:next_main_idx+1]
            else:
                # 没有后续main，找到最后一个normal
                forward_path = path
                return_path = list(reversed(forward_path[:-1]))  # 不重复最后一个点
                return forward_path + return_path


    def assign_path(self, vehicle: Vehicle):
        """路径分配策略：主干道按step锁定，一般道路全部锁定"""
        print(f"\n=== 为车辆 {vehicle.id} 分配路径约束 ===")
        
        full_path = vehicle.full_planned_path
        if not full_path:
            print(f"车辆 {vehicle.id} 没有规划路径")
            return
        
        # 1. 分析路径段
        path_segments = self.analyze_path_segments(full_path)
        print(f"路径分析结果:")
        for i, (segment_type, positions) in enumerate(path_segments):
            print(f"  段{i+1}: {segment_type}, 长度={len(positions)}")
        
        # 2. 确保车辆当前位置在主干道上
        start_position = full_path[0]
        start_cell = self.grid.get_cell(start_position[0], start_position[1])
        if start_cell and start_cell.grid_type != GRID_TYPE_MAIN_CHANNEL:
            print(f"⚠️ 警告：车辆 {vehicle.id} 起始位置 {start_position} 不在主干道上")
        
        # 3. 根据路径段类型分配约束
        positions_to_lock = []
        
        for segment_type, positions in path_segments:
            if segment_type == 'main_channel':
                # 主干道：只锁定前step_size个坐标
                lock_count = min(self.step_size, len(positions))
                positions_to_lock.extend(positions[:lock_count])
                print(f"  主干道段：锁定前 {lock_count}/{len(positions)} 个坐标")
            else:
                # 一般道路：锁定全部坐标
                positions_to_lock.extend(positions)
                print(f"  一般道路段：锁定全部 {len(positions)} 个坐标")
        
        # 4. 检查冲突
        conflicts = self.constraint_manager.check_path_conflicts(positions_to_lock)
        if conflicts:
            print(f"⚠️ 路径冲突，与车辆 {set(conflicts)} 冲突")
            print("需要重新规划路径或等待")
            # 暂时设置执行路径但不锁定约束
            vehicle.set_current_execution_path(full_path)
            return False
        
        # 5. 添加路径约束
        self.constraint_manager.add_path_constraint(vehicle, positions_to_lock)
        
        # 6. 设置执行路径
        vehicle.set_current_execution_path(full_path)
        
        print(f"✅ 成功为车辆 {vehicle.id} 分配路径，锁定了 {len(positions_to_lock)} 个坐标")
        return True

    def release_vehicle_constraints(self, vehicle: Vehicle):
        """释放车辆的路径约束"""
        print(f"\n=== 释放车辆 {vehicle.id} 的路径约束 ===")
        self.constraint_manager.remove_path_constraint(vehicle)

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
