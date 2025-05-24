from typing import List, Dict, Optional
from datetime import datetime
import random
import json
import os
from models.grid import Grid, GridCell, GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_OBSTACLE
from models.task import TaskManager, TransportTask, TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, TASK_STATUS_PENDING
from models.vehicle import Vehicle, VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED, TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, \
    VEHICLE_STATUS_IDLE, VEHICLE_STATUS_MOVING
from models.constraints import ConstraintManager, PhysicalConstraint
from algorithms.a_star import AStarPlanner
from utils.visualizer import GridVisualizer

SYSTEM_STATUS_COMPLETED = "completed"
SYSTEM_STATUS_BUSY = "busy"
SYSTEM_STATUS_WORKING = "working"


def assign_vehicle_by_distance(vehicles: List[Vehicle], task: TransportTask) -> Optional[Vehicle]:
    """
    根据距离为任务选择最合适的车辆。

    Args:
        vehicles: 车辆列表
        task: 待分配的任务，包含起点位置 (start_position)

    Returns:
        距离最近的空闲车辆，如果没有空闲车辆则返回 None
    """
    # 获取任务的起点
    task_start_x, task_start_y = task.start_position

    # 筛选空闲车辆并计算距离
    min_distance = float('inf')
    selected_vehicle = None

    for vehicle in vehicles:
        # 计算曼哈顿距离
        vehicle_x, vehicle_y = vehicle.current_position
        distance = abs(vehicle_x - task_start_x) + abs(vehicle_y - task_start_y)

        # 更新最近车辆
        if distance < min_distance:
            min_distance = distance
            selected_vehicle = vehicle

    return selected_vehicle


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

    def generate_map(self, seed: Optional[int] = None) -> None:
        if seed is not None:
            random.seed(seed)

        # 重置网格
        self.grid.width = 11
        self.grid.height = 11
        self.grid.cells.clear()
        self.grid.entrances.clear()
        self.grid.exits.clear()
        self.grid.main_channel_rows.clear()
        self.grid.main_channel_columns.clear()

        # 初始化所有格子为正常类型
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                self.grid.cells[(x, y)] = GridCell(x, y)

        # 设置主干道：横向行2，纵向列2
        self.grid.main_channel_rows = [3, 7]
        self.grid.main_channel_columns = [3, 7]

        # 标记主干道
        for row in self.grid.main_channel_rows:
            for x in range(self.grid.width):
                cell = self.grid.get_cell(x, row)
                if cell:
                    cell.grid_type = GRID_TYPE_MAIN_CHANNEL
        for col in self.grid.main_channel_columns:
            for y in range(self.grid.height):
                cell = self.grid.get_cell(col, y)
                if cell:
                    cell.grid_type = GRID_TYPE_MAIN_CHANNEL

        # 设置入口和出口
        self.grid.add_entrance(0, 3)
        self.grid.add_entrance(0, 7)
        self.grid.add_exit(10, 3)
        self.grid.add_exit(10, 7)

        restricted_positions = set()  # 入口和出口
        for row in self.grid.main_channel_rows:
            for x in range(self.grid.width):
                restricted_positions.add((x, row))
        for col in self.grid.main_channel_columns:
            for y in range(self.grid.height):
                restricted_positions.add((col, y))
        obstacle_positions = {(1, 1), (1, 9), (9, 1), (9, 9)}
        for x, y in obstacle_positions:
            if (x, y) not in restricted_positions:
                cell = self.grid.get_cell(x, y)
                if cell:
                    cell.grid_type = GRID_TYPE_OBSTACLE

        # 设置货物：非主干道、非入口/出口、非障碍物的格子中 20% 有货物
        cargo_positions = []
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                if (y in self.grid.main_channel_rows or x in self.grid.main_channel_columns or
                        (x, y) in obstacle_positions):
                    continue
                cargo_positions.append((x, y))
        random.seed(42)
        random.shuffle(cargo_positions)
        num_cargo = int(len(cargo_positions) * 0.2)
        for x, y in cargo_positions[:num_cargo]:
            self.grid.set_cargo(x, y, True)

    def initialize(self, seed: Optional[int] = None) -> None:
        """初始化地图、车辆和约束"""
        self.constraint_manager.set_grid(self.grid)

        # 添加物理约束（禁用点）
        obstacle_positions = [(x, y) for (x, y), cell in self.grid.cells.items() if
                              cell.grid_type == GRID_TYPE_OBSTACLE]
        physical_constraint = PhysicalConstraint(obstacle_positions)
        self.constraint_manager.add_constraint(physical_constraint)

        # 初始化车辆
        for i in range(self.num_vehicles):
            while True:
                x = random.randint(0, self.grid.width - 1)
                y = random.randint(0, self.grid.height - 1)
                if (x,
                    y) not in obstacle_positions and y not in self.grid.main_channel_rows and x not in self.grid.main_channel_columns:
                    break
            vehicle_type = VEHICLE_TYPE_EMPTY
            vehicle = Vehicle(id=f"V{i + 1:03d}", vehicle_type=vehicle_type, task_type=TASK_TYPE_OUTBOUND,
                              current_position=(x, y))
            self.vehicles.append(vehicle)
            self.constraint_manager.add_vehicle(vehicle)
            self.grid_visualizer.add_vehicle(vehicle)

    def generate_tasks(self, num_tasks: int) -> None:
        """生成指定数量的任务"""
        entrances = self.grid.get_all_entrances()
        exits = self.grid.get_all_exits()

        for _ in range(num_tasks):
            if random.choice([True, False]):
                entrance = random.choice(entrances)
                while True:
                    dest_x = random.randint(0, self.grid.width - 1)
                    dest_y = random.randint(0, self.grid.height - 1)
                    cell = self.grid.get_cell(dest_x, dest_y)
                    if cell and cell.grid_type != "obstacle" and dest_y not in self.grid.main_channel_rows and dest_x not in self.grid.main_channel_columns:
                        break
                task = self.task_manager.add_task(task_type=TASK_TYPE_INBOUND, start_pos=entrance,
                                                  end_pos=(dest_x, dest_y))
                self.constraint_manager.add_task(task)
            else:
                exit_pos = random.choice(exits)
                while True:
                    src_x = random.randint(0, self.grid.width - 1)
                    src_y = random.randint(0, self.grid.height - 1)
                    cell = self.grid.get_cell(src_x, src_y)
                    if cell and cell.grid_type != "obstacle" and src_y not in self.grid.main_channel_rows and src_x not in self.grid.main_channel_columns:
                        break
                task = self.task_manager.add_task(task_type=TASK_TYPE_OUTBOUND, start_pos=(src_x, src_y),
                                                  end_pos=exit_pos)
                self.constraint_manager.add_task(task)

    def save_map_and_tasks(self, map_filename: str, tasks_filename: str, save_tasks: bool = True) -> None:
        """保存地图和任务到JSON文件"""
        self.grid.save_to_json(map_filename)
        if save_tasks:
            tasks_data = [{"id": task.id, "task_type": task.task_type, "start_position": task.start_position,
                           "end_position": task.end_position, "priority": task.priority,
                           "created_at": task.created_at.isoformat(), "status": task.status}
                          for task in self.task_manager.tasks]
            with open(tasks_filename, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)

    def load_map_and_tasks(self, map_filename: str, tasks_filename: str) -> None:
        """从JSON文件加载地图和任务"""
        self.grid.load_from_json(map_filename)
        self.constraint_manager.set_grid(self.grid)
        try:
            with open(tasks_filename, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            for task_data in tasks_data:
                task = TransportTask(id=task_data["id"], task_type=task_data["task_type"],
                                     start_position=tuple(task_data["start_position"]),
                                     end_position=tuple(task_data["end_position"]),
                                     priority=task_data["priority"],
                                     created_at=datetime.fromisoformat(task_data["created_at"]),
                                     status=task_data["status"])
                self.task_manager.tasks.append(task)
                self.constraint_manager.add_task(task)
        except FileNotFoundError:
            print(f"任务文件 {tasks_filename} 未找到。开始时没有任务。")

    def assign_and_plan(self) -> str:
        """分配任务并规划路径"""
        # 无任务
        pending_tasks = self.task_manager.get_tasks_by_status(TASK_STATUS_PENDING)
        if not pending_tasks:
            print("无可分配任务")
            return SYSTEM_STATUS_WORKING

        # 无空闲车
        idle_vehicles = [vehicle for vehicle in self.vehicles if vehicle.status == VEHICLE_STATUS_IDLE]
        if not idle_vehicles:
            return SYSTEM_STATUS_BUSY

        for task in pending_tasks:
            # 无空闲车
            if not idle_vehicles:
                return SYSTEM_STATUS_BUSY

            is_valid, error_msg = self.constraint_manager.check_entrance_exit_order(task, task.start_position)
            if not is_valid:
                print(f"任务 {task.id} 无法分配: {error_msg}")
                continue

            vehicle = assign_vehicle_by_distance(idle_vehicles, task)
            if vehicle.assign_task(task):
                path_to_start = self.path_planner.find_path(vehicle, vehicle.current_position, task.start_position)
                if path_to_start == None:
                    print(f"无法分配任务")
                vehicle.set_path(path_to_start)
                vehicle.start_task()
                idle_vehicles.remove(vehicle)
                print(f"任务 {task.id} 已分配给车辆 {vehicle.id}, 路径: {vehicle.get_path_str()}")
                continue

        return SYSTEM_STATUS_WORKING

    def simulate_step(self) -> bool:
        """模拟一步，更新车辆位置"""
        active_vehicles = [v for v in self.vehicles if v.status == VEHICLE_STATUS_MOVING]
        if not active_vehicles:
            return False

        for vehicle in active_vehicles:
            next_pos = vehicle.get_next_position()
            if not next_pos:
                if vehicle.current_position == vehicle.current_task.start_position:
                    path_to_end = self.path_planner.find_path(vehicle, vehicle.current_position, vehicle.current_task.end_position)
                    vehicle.set_path(path_to_end)
                    vehicle.start_task()
                else:
                    vehicle.complete_task()
                    self.constraint_manager.remove_task(vehicle.current_task)
                continue
            vehicle.current_path_index += 1
            vehicle.update_position(next_pos)
            if vehicle.is_at_target():
                vehicle.complete_task()
                self.constraint_manager.remove_task(vehicle.current_task)
                print(f"车辆 {vehicle.id} 已完成任务")
        return True

    def visualize(self, filename: str) -> None:
        """可视化当前状态，保存到output目录"""
        self.grid_visualizer.draw_grid()
        self.grid_visualizer.draw_vehicles()
        full_path = os.path.join(self.output_dir, filename)
        self.grid_visualizer.save(full_path)

    def run(self, num_tasks: int, max_steps: int, save_map: bool = True, save_tasks: bool = True) -> None:
        """运行调度模拟，每一步都生成图片"""
        map_filename = os.path.join(self.output_dir, "map.json")
        tasks_filename = os.path.join(self.output_dir, "tasks.json")

        if save_map:
            self.generate_map(seed=42)
            self.generate_tasks(num_tasks)
            self.save_map_and_tasks(map_filename, tasks_filename, save_tasks)
        else:
            self.load_map_and_tasks(map_filename, tasks_filename)
            self.vehicles.clear()
        self.initialize()

        step = 0
        print(f"\n=== 初始状态（步骤 {step}） ===")
        self.visualize(f"step_{step}.png")
        step += 1

        while step <= max_steps:
            print(f"\n=== 模拟步骤 {step} ===")
            self.assign_and_plan()
            if not self.simulate_step():
                print("没有活动车辆，模拟结束")
                break
            self.visualize(f"step_{step}.png")
            step += 1


if __name__ == "__main__":
    scheduler = Scheduler(num_vehicles=2)
    # scheduler.run(num_tasks=3, max_steps=10, save_map=True, save_tasks=True)
    scheduler.run(num_tasks=0, max_steps=30, save_map=False, save_tasks=False)
