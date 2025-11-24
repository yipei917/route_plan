from src.models.grid import Grid, GRID_TYPE_NORMAL_CHANNEL, GRID_TYPE_OBSTACLE, GRID_TYPE_MAIN_CHANNEL
from src.algorithms.a_star import AStarPlanner
from src.models.vehicle import Vehicle, VEHICLE_TYPE_EMPTY
from src.models.constraints import ConstraintManager
from src.utils.visualizer import GridVisualizer
from typing import List

class Test:

    def __init__(self, num_vehicles: int = 1, width: int = 5, height: int = 5):
        self.grid = Grid(width, height)
        self.constraint_manager = ConstraintManager()
        self.path_planner = AStarPlanner(self.grid, self.constraint_manager)
        self.vehicles: List[Vehicle] = []
        self.num_vehicles = num_vehicles
        self.grid_visualizer = GridVisualizer(self.grid, figsize=(50, 50))

    def initialize(self):
        # 初始化障碍物
        obstacle_positions = [(2,1), (2,2), (2,3), (1,2), (3,2)]
        for x, y in obstacle_positions:
            self.grid.set_cell_type(x, y, GRID_TYPE_OBSTACLE)

        main_positions = [(1,4), (2,4), (4,1), (4,2)]
        for x, y in main_positions:
            self.grid.set_cell_type(x, y, GRID_TYPE_MAIN_CHANNEL)
            self.grid.set_cell_directions(x, y, ["up", "down", "left", "right"])

        # 初始化可通行区域
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                if (x, y) not in obstacle_positions and (x, y) not in main_positions:
                    self.grid.set_cell_type(x, y, GRID_TYPE_NORMAL_CHANNEL)
                    self.grid.set_cell_directions(x, y, ["up", "down", "left", "right"])

        # 初始化车辆
        for i in range(self.num_vehicles):
            vehicle = Vehicle(id=f"V{i + 1:03d}", vehicle_type=VEHICLE_TYPE_EMPTY, current_position=(0, 0))
            self.vehicles.append(vehicle)
            self.constraint_manager.add_vehicle(vehicle)
            self.grid_visualizer.add_vehicle(vehicle)
    
    def assign_task(self):
        vehicle = self.vehicles[0]
        path = self.path_planner.find_path(vehicle, vehicle.current_position, (4, 4))
        if path is None:
            print("No path found")
            return
        vehicle.set_path(path)
        self.constraint_manager.add_path(vehicle, path)

    def simulate_step(self):
        vehicle = self.vehicles[0]
        next_pos = vehicle.get_next_position()
        if next_pos:
            vehicle.current_path_index += 1
            vehicle.update_position(next_pos)
        
        if self.grid.get_cell_type(vehicle.current_position) == GRID_TYPE_MAIN_CHANNEL:
            self.constraint_manager.remove_path(vehicle)
            path_remaining = vehicle.get_remaining_path()
            if path_remaining:
                print(f"剩余路径: {path_remaining}")
                vehicle.set_path(path_remaining)
                self.constraint_manager.add_path(vehicle, path_remaining)
        
        if vehicle.current_position == (4, 4):
            self.constraint_manager.remove_path(vehicle)
            return False
        return True

    def visualize(self, num_step: int):
        self.grid_visualizer.draw_grid(self.constraint_manager)
        self.grid_visualizer.draw_vehicles()
        self.grid_visualizer.save(f"test/output/vehicle_test_{num_step}.png")

    def run(self):
        self.initialize()

        print(f"\n=== 初始状态（步骤 {0}） ===")
        self.assign_task()
        self.visualize(0)

        i = 1
        flag = True
        while flag:
            print(f"\n=== 模拟状态（步骤 {i}） ===")
            flag = self.simulate_step()
            self.visualize(i)
            i += 1

if __name__ == "__main__":
    test = Test()
    test.run()