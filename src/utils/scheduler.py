from typing import List
from src.models.grid import Grid
from src.models.task import TASK_STATUS_PENDING, TaskManager 
from src.models.vehicle import VEHICLE_STATUS_IDLE, VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED, Vehicle
from src.utils.visualizer import GridVisualizer
from src.utils.simulator import Simulator
from src.algorithms.a_star import AStarPlanner
import os

class Scheduler:
    """调度器类，管理任务分配和路径规划"""

    def __init__(self, num_vehicles: int):
        self.grid = Grid(10, 10)
        self.task_manager = TaskManager()
        self.path_planner = AStarPlanner(self.grid)
        self.vehicles: List[Vehicle] = []
        self.num_vehicles = num_vehicles
        self.grid_visualizer = GridVisualizer(self.grid, figsize=(40,40))
        self.simulator = Simulator()

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
                path_to_start = self.path_planner.find_path(vehicle, vehicle.current_position, task.start_position)
                if path_to_start is None: continue
                if vehicle.assign_task(task):
                    vehicle.set_path(path_to_start)
                    vehicle.start_task()
                    idle_vehicles.remove(vehicle)
                    print(f"任务 {task.id} 已分配给车辆 {vehicle.id}, 路径: {vehicle.get_path_str()}")
                    break
            else: print(f"任务 {task.id} 暂无可用车辆或所有车辆均无法到达")
        return

    def check_status(self):
        for v in self.vehicles:
            if v.status == VEHICLE_STATUS_IDLE:
                continue
            
            # 检查车辆是否有当前任务
            if v.current_task is None:
                continue
                
            task = v.current_task
            
            # 当车辆到达起始位置时
            if v.current_position == task.start_position:
                if v.vehicle_type == VEHICLE_TYPE_EMPTY:  # 确保车辆是空载状态
                    # 车辆载起货物
                    v.vehicle_type = VEHICLE_TYPE_LOADED
                    # 更新起始位置格子的货物信息（货物被取走）
                    self.grid.set_cargo(task.start_position[0], task.start_position[1], False)
                    # 规划去终点的路径
                    path_to_end = self.path_planner.find_path(v, task.start_position, task.end_position)
                    if path_to_end:
                        v.set_path(path_to_end)
                    else:
                        print(f"车辆 {v.id} 无法找到到终点 {task.end_position} 的路径")
            
            # 当车辆到达终点位置时
            elif v.current_position == task.end_position:
                if v.vehicle_type == VEHICLE_TYPE_LOADED:  # 确保车辆是载货状态
                    # 更新终点位置格子的货物信息（货物被放下）
                    self.grid.set_cargo(task.end_position[0], task.end_position[1], True)
                    # 车辆变为空载
                    v.vehicle_type = VEHICLE_TYPE_EMPTY
                    # 结束任务
                    v.complete_task()
                    print(f"车辆 {v.id} 已完成任务 {task.id}，货物已送达终点 {task.end_position}")

    def run(self):
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
