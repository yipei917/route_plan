from src.models.grid import (
    Grid,
    GRID_TYPE_NORMAL_CHANNEL,
    GRID_TYPE_OBSTACLE,
    GRID_TYPE_MAIN_CHANNEL,
)
from src.algorithms.a_star import AStarPlanner
from src.models.vehicle import (
    Vehicle,
    VEHICLE_TYPE_EMPTY,
    VEHICLE_TYPE_LOADED,
    VEHICLE_STATUS_IDLE,
    VEHICLE_STATUS_WAITING,
    VEHICLE_STATUS_WORKING,
)
from src.models.constraints import ConstraintManager
from src.utils.visualizer import GridVisualizer
from src.models.task import (
    TaskManager,
    TASK_TYPE_OUTBOUND,
    TASK_TYPE_INBOUND,
    TASK_STATUS_PENDING,
)
from typing import List


class Test:

    def __init__(self, num_vehicles: int = 2, width: int = 7, height: int = 7):
        self.grid = Grid(width, height)
        self.constraint_manager = ConstraintManager()
        self.task_manager = TaskManager()
        self.path_planner = AStarPlanner(self.grid, self.constraint_manager)
        self.vehicles: List[Vehicle] = []
        self.num_vehicles = num_vehicles
        self.grid_visualizer = GridVisualizer(self.grid, figsize=(35, 35))

    def initialize(self):
        # 将所有main channel相关的position都放到main_positions里
        main_positions = [
            (0, 1), (6, 1), (0, 5), (6, 5),  # 原始主通道
            (1, 5), (2, 5), (3, 5), (4, 5), (5, 5),  # left_positions
            (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),  # right_positions
        ]
        for x, y in main_positions:
            self.grid.set_cell_type(x, y, GRID_TYPE_MAIN_CHANNEL)
            self.grid.set_cell_directions(x, y, ["up", "down", "left", "right"])


        up_down_positions = [(1,2), (1,3), (1,4), (1,6), (5,2), (5,3), (5,4), (5,6)]
        for x, y in up_down_positions:
            self.grid.set_cell_type(x, y, GRID_TYPE_MAIN_CHANNEL)
            self.grid.set_cell_directions(x, y, ["up", "down"])

        # 初始化可通行区域
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                if (x, y) not in main_positions and (x, y) not in up_down_positions:
                    self.grid.set_cell_type(x, y, GRID_TYPE_NORMAL_CHANNEL)
                    self.grid.set_cell_directions(x, y, ["up", "down"])

        v_positions = [(1,2), (5, 2)]
        # 初始化车辆
        for i in range(self.num_vehicles):
            vehicle = Vehicle(
                id=f"V{i + 1:03d}",
                vehicle_type=VEHICLE_TYPE_EMPTY,
                current_position=v_positions[i],
            )
            self.vehicles.append(vehicle)
            self.constraint_manager.add_vehicle(vehicle)
            self.grid_visualizer.add_vehicle(vehicle)

        self.task_manager.add_task(
            task_type=TASK_TYPE_INBOUND, start_pos=(4, 0), end_pos=(6, 0)
        )
        self.task_manager.add_task(
            task_type=TASK_TYPE_OUTBOUND, start_pos=(1, 0), end_pos=(1, 4)
        )

    def assign_and_plan(self):
        """分配任务并规划路径"""
        pending_tasks = self.task_manager.get_tasks_by_status(TASK_STATUS_PENDING)
        if not pending_tasks:
            print("无可分配任务")
            return

        idle_vehicles = [
            vehicle
            for vehicle in self.vehicles
            if vehicle.status == VEHICLE_STATUS_IDLE
        ]
        if not idle_vehicles:
            print("无空闲车辆")
            return

        for task in pending_tasks:
            for vehicle in idle_vehicles:
                path_to_start = self.path_planner.find_path(
                    vehicle, vehicle.current_position, task.start_position
                )
                if path_to_start is None:
                    continue
                if vehicle.assign_task(task):
                    vehicle.set_path(path_to_start)
                    vehicle.start_task()
                    idle_vehicles.remove(vehicle)
                    # self.constraint_manager.add_path(vehicle, path_to_start)
                    print(
                        f"任务 {task.id} 已分配给车辆 {vehicle.id}, 路径: {vehicle.get_path_str()}"
                    )
                    break
            # else: print(f"任务 {task.id} 暂无可用车辆或所有车辆均无法到达")
        return

    def simulate_step(self):
        """模拟一步，更新车辆位置"""
        active_vehicles = [
            v
            for v in self.vehicles
            if v.status in (VEHICLE_STATUS_WAITING, VEHICLE_STATUS_WORKING)
        ]
        if not active_vehicles:
            return False

        for vehicle in active_vehicles:
            next_pos = vehicle.get_next_position()
            if next_pos:
                vehicle.current_path_index += 1
                vehicle.update_position(next_pos)

            task = vehicle.current_task
            if not task:
                vehicle.status = VEHICLE_STATUS_IDLE
                self.constraint_manager.remove_path(vehicle)
                continue

            if (
                self.grid.get_cell_type(vehicle.current_position)
                == GRID_TYPE_MAIN_CHANNEL
            ):
                self.constraint_manager.remove_path(vehicle)
                path_remaining = vehicle.get_remaining_path()
                if path_remaining:
                    print(f"剩余路径: {path_remaining}")
                    vehicle.set_path(path_remaining)
                    self.constraint_manager.add_path(vehicle, path_remaining)

            if vehicle.current_position == task.start_position:
                if task.task_type == TASK_TYPE_OUTBOUND:
                    self.grid.set_cargo(*task.start_position, False)
                    vehicle.vehicle_type = VEHICLE_TYPE_LOADED
                elif task.task_type == TASK_TYPE_INBOUND:
                    vehicle.vehicle_type = VEHICLE_TYPE_LOADED
                self.constraint_manager.remove_path(vehicle)
                path_to_end = self.path_planner.find_path(
                    vehicle, vehicle.current_position, task.end_position
                )
                if path_to_end:
                    vehicle.set_path(path_to_end)
                    vehicle.status = VEHICLE_STATUS_WORKING
                    self.constraint_manager.add_path(vehicle, path_to_end)
                else:
                    print(
                        f"车辆 {vehicle.id} 无法从起点{vehicle.current_position}到终点{task.end_position}，任务无法完成，task: {task.id}"
                    )
                    vehicle.set_waiting()

            elif vehicle.current_position == task.end_position:
                if task.task_type == TASK_TYPE_OUTBOUND:
                    vehicle.vehicle_type = VEHICLE_TYPE_EMPTY
                elif task.task_type == TASK_TYPE_INBOUND:
                    self.grid.set_cargo(*task.end_position, True)
                    vehicle.vehicle_type = VEHICLE_TYPE_EMPTY
                vehicle.complete_task()
                self.constraint_manager.remove_path(vehicle)
                vehicle.status = VEHICLE_STATUS_IDLE
                print(f"车辆 {vehicle.id} 已完成任务")
        return True

    def visualize(self, num_step: int):
        self.grid_visualizer.draw_grid(self.constraint_manager)
        self.grid_visualizer.draw_vehicles()
        self.grid_visualizer.save(f"test/output/vehicle_test_{num_step}.png")

    def run(self):
        self.initialize()
        self.visualize(0)
        print(f"\n=== 初始状态（步骤 0） ===")
        step = 1

        flag = True
        while flag:
            print(f"\n=== 模拟步骤 {step} ===")
            self.assign_and_plan()

            flag = self.simulate_step()
            self.visualize(step)
            step += 1


if __name__ == "__main__":
    test = Test()
    test.run()
