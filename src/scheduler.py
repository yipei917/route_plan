from typing import List, Dict, Optional
from datetime import datetime
import random
import json
import os
from .models.grid import Grid, GridCell, GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_OBSTACLE
from .models.task import TaskManager, TransportTask, TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, TASK_STATUS_PENDING
from .models.vehicle import Vehicle, VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED, TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, \
    VEHICLE_STATUS_IDLE, VEHICLE_STATUS_MOVING, VEHICLE_STATUS_LOADING, VEHICLE_STATUS_UNLOADING
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
                    cell.allowed_directions = ["up", "down", "left", "right"]
        for col in self.grid.main_channel_columns:
            for y in range(self.grid.height):
                cell = self.grid.get_cell(col, y)
                if cell:
                    cell.grid_type = GRID_TYPE_MAIN_CHANNEL
                    cell.allowed_directions = ["up", "down", "left", "right"]

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
        self.constraint_manager.grid = self.grid

        # 添加物理约束（禁用点）
        obstacle_positions = [(x, y) for (x, y), cell in self.grid.cells.items() if
                              cell.grid_type == GRID_TYPE_OBSTACLE]
        physical_constraint = PhysicalConstraint(obstacle_positions)
        self.constraint_manager.add_constraint(physical_constraint)

        main_channel_positions = []
        for row in self.grid.main_channel_rows:
            for x in range(self.grid.width):
                pos = (x, row)
                main_channel_positions.append(pos)
 
        self.vehicles.clear()
        for i in range(self.num_vehicles):
            if i >= len(main_channel_positions):
                raise ValueError("主干道空间不足以顺序放置所有车辆")
            x, y = main_channel_positions[i]
            vehicle_type = VEHICLE_TYPE_EMPTY
            vehicle = Vehicle(id=f"V{i + 1:03d}", vehicle_type=vehicle_type, task_type=TASK_TYPE_OUTBOUND,
                              current_position=(x, y))
            self.vehicles.append(vehicle)
            self.constraint_manager.add_vehicle(vehicle)
            self.grid_visualizer.add_vehicle(vehicle)

    def generate_tasks(self, num_tasks: int) -> None:
        """根据当前货物情况生成指定数量的任务"""
        entrances = self.grid.get_all_entrances()
        exits = self.grid.get_all_exits()

        for _ in range(num_tasks):
            if random.choice([True, False]):
                # 入库任务：目标格子必须为空
                entrance = random.choice(entrances)
                while True:
                    dest_x = random.randint(0, self.grid.width - 1)
                    dest_y = random.randint(0, self.grid.height - 1)
                    cell = self.grid.get_cell(dest_x, dest_y)
                    if (cell and cell.grid_type != "obstacle" and
                        dest_y not in self.grid.main_channel_rows and
                        dest_x not in self.grid.main_channel_columns and
                        not cell.has_cargo):
                        break
                task = self.task_manager.add_task(task_type=TASK_TYPE_INBOUND, start_pos=entrance,
                                                  end_pos=(dest_x, dest_y))
                self.constraint_manager.add_task(task)
            else:
                # 出库任务：源格子必须有货物
                exit_pos = random.choice(exits)
                while True:
                    src_x = random.randint(0, self.grid.width - 1)
                    src_y = random.randint(0, self.grid.height - 1)
                    cell = self.grid.get_cell(src_x, src_y)
                    if (cell and cell.grid_type != "obstacle" and
                        src_y not in self.grid.main_channel_rows and
                        src_x not in self.grid.main_channel_columns and
                        cell.has_cargo):
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
        pending_tasks = self.task_manager.get_tasks_by_status(TASK_STATUS_PENDING)
        if not pending_tasks:
            print("无可分配任务")
            return SYSTEM_STATUS_WORKING

        idle_vehicles = [vehicle for vehicle in self.vehicles if vehicle.status == VEHICLE_STATUS_IDLE]
        if not idle_vehicles:
            print("无空闲车辆")
            return SYSTEM_STATUS_BUSY

        assigned_any = False

        for task in pending_tasks:
            # 检查入口/出口顺序约束
            is_valid, error_msg = self.constraint_manager.check_entrance_exit_order(task, task.start_position)
            if not is_valid:
                print(f"任务 {task.id} 无法分配: {error_msg}")
                continue

            # 按距离排序所有空闲车辆
            sorted_vehicles = sorted(
                idle_vehicles,
                key=lambda v: abs(v.current_position[0] - task.start_position[0]) + abs(v.current_position[1] - task.start_position[1])
            )

            for vehicle in sorted_vehicles:
                # 规划路径（先到任务起点）
                path_to_start = self.path_planner.find_path(vehicle, vehicle.current_position, task.start_position)
                if path_to_start is None:
                    continue  # 该车无法到达，尝试下一个

                # 分配任务和路径
                if vehicle.assign_task(task):
                    vehicle.set_path(path_to_start)
                    vehicle.start_task()
                    vehicle.status = VEHICLE_STATUS_LOADING
                    idle_vehicles.remove(vehicle)
                    self.constraint_manager.add_task(task)  # 启动任务后加入约束管理
                    assigned_any = True
                    print(f"任务 {task.id} 已分配给车辆 {vehicle.id}, 路径: {vehicle.get_path_str()}")
                    break  # 该任务已分配，跳出车辆循环

            else:
                print(f"任务 {task.id} 暂无可用车辆或所有车辆均无法到达")

        if assigned_any:
            return SYSTEM_STATUS_WORKING
        else:
            return SYSTEM_STATUS_BUSY

    def simulate_step(self) -> bool:
        """模拟一步，更新车辆位置"""
        active_vehicles = [v for v in self.vehicles if v.status in (VEHICLE_STATUS_MOVING, VEHICLE_STATUS_LOADING, VEHICLE_STATUS_UNLOADING)]
        if not active_vehicles:
            return False

        for vehicle in active_vehicles:
            next_pos = vehicle.get_next_position()
            if next_pos:
                # 正常移动
                vehicle.current_path_index += 1
                vehicle.update_position(next_pos)
                continue

            # 路径已走完，判断当前阶段
            task = vehicle.current_task
            if not task:
                continue

            if vehicle.current_position == task.start_position and vehicle.status == VEHICLE_STATUS_LOADING:
                # 到达起点，准备去终点
                if task.task_type == TASK_TYPE_OUTBOUND:
                    self.grid.set_cargo(*task.start_position, False)
                    vehicle.vehicle_type = VEHICLE_TYPE_LOADED
                elif task.task_type == TASK_TYPE_INBOUND:
                    vehicle.vehicle_type = VEHICLE_TYPE_LOADED
                # 规划去终点路径
                path_to_end = self.path_planner.find_path(vehicle, vehicle.current_position, task.end_position)
                if path_to_end:
                    vehicle.set_path(path_to_end)
                    vehicle.status = VEHICLE_STATUS_UNLOADING
                else:
                    print(f"车辆 {vehicle.id} 无法从起点到终点")
                    vehicle.complete_task()
                    self.constraint_manager.remove_task(task)
                continue

            if vehicle.current_position == task.end_position and vehicle.status == VEHICLE_STATUS_UNLOADING:
                # 到达终点，完成任务
                if task.task_type == TASK_TYPE_OUTBOUND:
                    vehicle.vehicle_type = VEHICLE_TYPE_EMPTY
                elif task.task_type == TASK_TYPE_INBOUND:
                    self.grid.set_cargo(*task.end_position, True)
                    vehicle.vehicle_type = VEHICLE_TYPE_EMPTY
                vehicle.complete_task()
                self.constraint_manager.remove_task(task)
                vehicle.status = VEHICLE_STATUS_IDLE
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
    # scheduler.run(num_tasks=3, max_steps=100, save_map=True, save_tasks=True)
    scheduler.run(num_tasks=0, max_steps=100, save_map=False, save_tasks=False)
