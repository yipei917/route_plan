from typing import List, Dict, Optional
import random
import os
from .models.grid import Grid, GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_OBSTACLE, GRID_TYPE_NORMAL_CHANNEL
from .models.task import TaskManager, TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, TASK_STATUS_PENDING, TASK_STATUS_IN_PROGRESS
from .models.vehicle import Vehicle, VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED, VEHICLE_STATUS_IDLE, VEHICLE_STATUS_MOVING, VEHICLE_STATUS_LOADING, VEHICLE_STATUS_UNLOADING, VEHICLE_STATUS_WAITING
from .models.constraints import ConstraintManager, PhysicalConstraint
from .algorithms.a_star import AStarPlanner
from .utils.visualizer import GridVisualizer

SYSTEM_STATUS_COMPLETED = "completed"
SYSTEM_STATUS_BUSY = "busy"
SYSTEM_STATUS_WORKING = "working"


class Scheduler:
    """调度器类，管理任务分配和路径规划"""

    def __init__(self, num_vehicles: int, width: int = 11, height: int = 11):
        self.grid = Grid(width, height)
        self.task_manager = TaskManager()
        self.constraint_manager = ConstraintManager()
        self.path_planner = AStarPlanner(self.grid, self.constraint_manager)
        self.vehicles: List[Vehicle] = []
        self.num_vehicles = num_vehicles
        self.grid_visualizer = GridVisualizer(self.grid)
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

    def initialize(self) -> None:
        """初始化车辆和约束"""

        # 添加障碍物约束
        obstacle_positions = [(x, y) for (x, y), cell in self.grid.cells.items() if cell.grid_type == GRID_TYPE_OBSTACLE]
        physical_constraint = PhysicalConstraint(obstacle_positions)
        self.constraint_manager.add_constraint(physical_constraint)

        # 获取主干道位置
        main_channel_positions = [(x, y) for (x, y), cell in self.grid.cells.items() if cell.grid_type == GRID_TYPE_MAIN_CHANNEL]

        # 随机生成车辆
        self.vehicles.clear()
        random.shuffle(main_channel_positions)  # 随机打乱主干道位置
        for i in range(self.num_vehicles):
            if i >= len(main_channel_positions):
                raise ValueError("主干道空间不足以顺序放置所有车辆")
            x, y = main_channel_positions[i]
            vehicle = Vehicle(id=f"V{i + 1:03d}", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(x, y))
            self.vehicles.append(vehicle)
            self.constraint_manager.add_vehicle(vehicle)
            self.grid_visualizer.add_vehicle(vehicle)
        
    def save_tasks(self, tasks_filename: str) -> None:
        """仅保存任务到JSON文件"""
        self.task_manager.save_tasks(tasks_filename)

    def save_map(self, map_filename: str) -> None:
        """仅保存地图到JSON文件"""
        self.grid.save_to_json(map_filename)

    def load_tasks(self, tasks_filename: str) -> None:
        """仅从JSON文件加载任务"""
        try:
            self.task_manager.load_tasks(tasks_filename)
        except FileNotFoundError:
            print(f"任务文件 {tasks_filename} 未找到。开始时没有任务。")

    def load_map(self, map_filename: str) -> None:
        """仅从JSON文件加载地图"""
        try:
            self.grid.load_from_json(map_filename)
        except FileNotFoundError:
            print(f"地图文件 {map_filename} 未找到。无法加载地图。")

    def load_from_xlsx(self, filename: str) -> None:
        """从Excel文件加载地图"""
        self.grid.load_map_from_excel(filename)

    def load_tasks_from_xlsx(self, filename: str) -> None:
        """从Excel文件加载任务"""
        self.task_manager.load_tasks_from_xlsx(filename)

    def assign_and_plan(self) -> str:
        """分配任务并规划路径"""
        pending_tasks = self.task_manager.get_tasks_by_status(TASK_STATUS_PENDING)
        if not pending_tasks: print("无可分配任务"); return SYSTEM_STATUS_WORKING

        idle_vehicles = [vehicle for vehicle in self.vehicles if vehicle.status == VEHICLE_STATUS_IDLE]
        if not idle_vehicles: print("无空闲车辆"); return SYSTEM_STATUS_BUSY

        assigned_any = False
        for task in pending_tasks:
            sorted_vehicles = sorted(idle_vehicles, key=lambda v: abs(v.current_position[0] - task.start_position[0]) + abs(v.current_position[1] - task.start_position[1]))
            for vehicle in sorted_vehicles:
                path_to_start = self.path_planner.find_path(vehicle, vehicle.current_position, task.start_position)
                if path_to_start is None: continue
                if vehicle.assign_task(task):
                    vehicle.set_path(path_to_start)
                    vehicle.start_task()
                    vehicle.status = VEHICLE_STATUS_LOADING
                    idle_vehicles.remove(vehicle)
                    self.constraint_manager.add_path(vehicle, path_to_start)
                    assigned_any = True
                    print(f"任务 {task.id} 已分配给车辆 {vehicle.id}, 路径: {vehicle.get_path_str()}")
                    break
            # else: print(f"任务 {task.id} 暂无可用车辆或所有车辆均无法到达")
        return SYSTEM_STATUS_WORKING if assigned_any else SYSTEM_STATUS_BUSY

    def simulate_step(self) -> bool:
        """模拟一步，更新车辆位置"""
        active_vehicles = [v for v in self.vehicles if v.status in (VEHICLE_STATUS_WAITING, VEHICLE_STATUS_MOVING, VEHICLE_STATUS_LOADING, VEHICLE_STATUS_UNLOADING)]
        if not active_vehicles: return False

        for vehicle in active_vehicles:
            next_pos = vehicle.get_next_position()
            if next_pos:
                vehicle.current_path_index += 1
                vehicle.update_position(next_pos)
                continue

            task = vehicle.current_task
            if not task:
                vehicle.status = VEHICLE_STATUS_IDLE
                self.constraint_manager.remove_path(vehicle)
                continue

            if vehicle.current_position == task.start_position:
                if task.task_type == TASK_TYPE_OUTBOUND:
                    self.grid.set_cargo(*task.start_position, False)
                    vehicle.vehicle_type = VEHICLE_TYPE_LOADED
                elif task.task_type == TASK_TYPE_INBOUND:
                    vehicle.vehicle_type = VEHICLE_TYPE_LOADED
                self.constraint_manager.remove_path(vehicle)
                path_to_end = self.path_planner.find_path(vehicle, vehicle.current_position, task.end_position)
                if path_to_end:
                    vehicle.set_path(path_to_end)
                    vehicle.status = VEHICLE_STATUS_UNLOADING
                    self.constraint_manager.add_path(vehicle, path_to_end)
                else:
                    print(f"车辆 {vehicle.id} 无法从起点{vehicle.current_position}到终点{task.end_position}，任务无法完成，task: {task.id}")
                    vehicle.set_waiting()
                    vehicle.status = VEHICLE_STATUS_WAITING

            elif vehicle.current_position == task.end_position:
                if task.task_type == TASK_TYPE_OUTBOUND: vehicle.vehicle_type = VEHICLE_TYPE_EMPTY
                elif task.task_type == TASK_TYPE_INBOUND:
                    self.grid.set_cargo(*task.end_position, True)
                    vehicle.vehicle_type = VEHICLE_TYPE_EMPTY
                vehicle.complete_task()
                self.constraint_manager.remove_path(vehicle)
                vehicle.status = VEHICLE_STATUS_IDLE
                print(f"车辆 {vehicle.id} 已完成任务")
        return True

    def visualize(self, filename: str) -> None:
        """可视化当前状态，保存到output目录"""
        self.grid_visualizer.draw_grid(self.constraint_manager)
        self.grid_visualizer.draw_vehicles()
        full_path = os.path.join(self.output_dir, filename)
        self.grid_visualizer.save(full_path)

    def run(self, max_steps: int, load: bool = True) -> None:
        """运行调度模拟，从指定任务开始"""
        tasks_filename = os.path.join(self.output_dir, "tasks.json")
        map_filename = os.path.join(self.output_dir, "map.json")

        if load:
            self.load_tasks(tasks_filename)
            self.load_map(map_filename)
        else:
            self.load_from_xlsx("resource/map4.xlsx")
            self.load_tasks_from_xlsx("resource/task1.xlsx")

        self.initialize()


        step = 0
        print(f"\n=== 初始状态（步骤 {step}） ===")
        step += 1

        while step <= max_steps:
            print(f"\n=== 模拟步骤 {step} ===")
            self.assign_and_plan()

            if not self.simulate_step():
                print("没有活动车辆，模拟结束")
                break

            step += 1


if __name__ == "__main__":
    scheduler = Scheduler(num_vehicles=1)
    scheduler.run(max_steps=100000000, load=False)
    # scheduler.visualize("final_state.png")

