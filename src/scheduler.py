from typing import List, Dict, Optional
from datetime import datetime
import random
import json
import os
from .models.grid import Grid, GridCell, GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_OBSTACLE
from .models.task import (
    TaskManager,
    TransportTask,
    TASK_TYPE_INBOUND,
    TASK_TYPE_OUTBOUND,
    TASK_STATUS_PENDING,
)
from .models.vehicle import (
    Vehicle,
    VEHICLE_TYPE_EMPTY,
    VEHICLE_TYPE_LOADED,
    VEHICLE_STATUS_IDLE,
    VEHICLE_STATUS_MOVING,
    VEHICLE_STATUS_LOADING,
    VEHICLE_STATUS_UNLOADING,
    VEHICLE_STATUS_WAITING,
)
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
        
    def genarate_cargo(self) -> None:
        """随机生成货物"""
        obstacle_positions = [(x, y) for (x, y), cell in self.grid.cells.items() if cell.grid_type == GRID_TYPE_OBSTACLE]
        main_channel_positions = [(x, y) for (x, y), cell in self.grid.cells.items() if cell.grid_type == GRID_TYPE_MAIN_CHANNEL]

        # 随机生成货物
        all_positions = [(x, y) for x in range(self.grid.width) for y in range(self.grid.height)]
        valid_positions = [
            pos for pos in all_positions
            if pos not in obstacle_positions and pos not in main_channel_positions
        ]
        num_cargo = max(1, int(0.1 * len(valid_positions)))  # 10% 的货物
        cargo_positions = random.sample(valid_positions, num_cargo)
        for x, y in cargo_positions:
            self.grid.set_cargo(x, y, True)

    def generate_tasks(self, num_tasks: int, seed: Optional[int] = None) -> None:
        """根据当前货物情况生成指定数量的任务，支持随机种子"""
        if seed is not None:
            random.seed(seed)

        entrances, exits = self.grid.get_all_entrances(), self.grid.get_all_exits()
        for _ in range(num_tasks):
            if random.choice([True, False]):
                entrance = random.choice(entrances)
                while True:
                    dest_x, dest_y = random.randint(0, self.grid.width - 1), random.randint(0, self.grid.height - 1)
                    cell = self.grid.get_cell(dest_x, dest_y)
                    if cell and cell.grid_type != GRID_TYPE_OBSTACLE and dest_y not in self.grid.main_channel_rows and dest_x not in self.grid.main_channel_columns and not cell.has_cargo:
                        break
                self.task_manager.add_task(task_type=TASK_TYPE_INBOUND, start_pos=entrance, end_pos=(dest_x, dest_y))
            else:
                exit_pos = random.choice(exits)
                while True:
                    src_x, src_y = random.randint(0, self.grid.width - 1), random.randint(0, self.grid.height - 1)
                    cell = self.grid.get_cell(src_x, src_y)
                    if cell and cell.grid_type != GRID_TYPE_OBSTACLE and src_y not in self.grid.main_channel_rows and src_x not in self.grid.main_channel_columns and cell.has_cargo:
                        break
                self.task_manager.add_task(task_type=TASK_TYPE_OUTBOUND, start_pos=(src_x, src_y), end_pos=exit_pos)

    def save_tasks(self, tasks_filename: str, save_tasks: bool = True, save_map: bool = True) -> None:
        """保存任务和地图到JSON文件"""
        if save_tasks:
            tasks_data = [{"id": task.id, "task_type": task.task_type, "start_position": task.start_position, "end_position": task.end_position, "priority": task.priority, "created_at": task.created_at.isoformat(), "status": task.status} for task in self.task_manager.tasks]
            with open(tasks_filename, "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)

        if save_map:
            map_filename = tasks_filename.replace("tasks.json", "map.json")
            self.grid.save_to_json(map_filename)

    def load_tasks(self, tasks_filename: str, load_map: bool = True) -> None:
        """从JSON文件加载任务和地图"""
        try:
            with open(tasks_filename, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)
            for task_data in tasks_data:
                self.task_manager.tasks.append(TransportTask(id=task_data["id"], task_type=task_data["task_type"], start_position=tuple(task_data["start_position"]), end_position=tuple(task_data["end_position"]), priority=task_data["priority"], created_at=datetime.fromisoformat(task_data["created_at"]), status=task_data["status"]))
        except FileNotFoundError:
            print(f"任务文件 {tasks_filename} 未找到。开始时没有任务。")

        if load_map:
            map_filename = tasks_filename.replace("tasks.json", "map.json")
            try:
                self.grid.load_from_json(map_filename)
            except FileNotFoundError:
                print(f"地图文件 {map_filename} 未找到。无法加载地图。")

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
            else: print(f"任务 {task.id} 暂无可用车辆或所有车辆均无法到达")
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
            if not task: continue

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
                    print(f"车辆 {vehicle.id} 无法从起点{vehicle.current_position}到终点{task.end_position}，任务无法完成")
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

    def run(self, num_tasks: int, max_steps: int, load: bool = True) -> None:
        """运行调度模拟，每一步都生成图片"""
        tasks_filename = os.path.join(self.output_dir, "tasks.json")

        if load:
            self.load_tasks(tasks_filename, load_map=True)
        else:
            self.load_from_xlsx("resource/map4.xlsx")
            self.genarate_cargo()
            self.generate_tasks(num_tasks)
            self.save_tasks(tasks_filename, save_tasks=True, save_map=True)

        self.initialize()

        step = 0
        print(f"\n=== 初始状态（步骤 {step}） ===")
        # self.visualize(f"step_{step}.png")
        step += 1

        while step <= max_steps:
            print(f"\n=== 模拟步骤 {step} ===")
            self.assign_and_plan()
            if not self.simulate_step():
                print("没有活动车辆，模拟结束")
                break
            # self.visualize(f"step_{step}.png")
            step += 1

    def load_from_xlsx(self, filename: str) -> None:
        """从Excel文件加载地图和任务"""
        self.grid.load_map_from_excel(filename)


if __name__ == "__main__":
    scheduler = Scheduler(num_vehicles=2)
    scheduler.run(num_tasks=2, max_steps=200, load=True)

