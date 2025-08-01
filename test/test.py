from src.utils.scheduler import Scheduler
from src.models.task import TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, TransportTask
from src.models.vehicle import VEHICLE_TYPE_EMPTY, Vehicle
import os
import sys

# 测试一，基础避让功能
def test_1():
    scheduler = Scheduler(num_vehicles=2, step_size=3, output_path="output/test_1")
    os.makedirs("output/test_1", exist_ok=True)
    scheduler.grid.load_map_from_xlsx("resource/test_map.xlsx")
    scheduler.task_manager.add_task(task_type=TASK_TYPE_OUTBOUND,start_pos=(10,6),end_pos=(11,7))
    scheduler.task_manager.add_task(task_type=TASK_TYPE_INBOUND,start_pos=(2,8),end_pos=(3,6))
    # 添加车辆
    vehicle_position = [(6,7), (12,7)]
    for i in range(scheduler.num_vehicles):
        v = Vehicle(
                id=f"V{i+1}",
                vehicle_type=VEHICLE_TYPE_EMPTY,
                current_position=vehicle_position[i]
            )
        scheduler.vehicles.append(v)
        scheduler.grid_visualizer.add_vehicle(v)
        scheduler.simulator.add_vehicle(v)

    scheduler.run()

# 测试二，驱除主干道空闲车
def test_2():
    scheduler = Scheduler(num_vehicles=2, step_size=3, output_path="output/test_2")
    os.makedirs("output/test_2", exist_ok=True)
    scheduler.grid.load_map_from_xlsx("resource/test_map.xlsx")
    scheduler.task_manager.add_task(task_type=TASK_TYPE_OUTBOUND,start_pos=(10,6),end_pos=(11,7))
    # 添加车辆
    vehicle_position = [(3,7), (8,7)]
    for i in range(scheduler.num_vehicles):
        v = Vehicle(
                id=f"V{i+1}",
                vehicle_type=VEHICLE_TYPE_EMPTY,
                current_position=vehicle_position[i]
            )
        scheduler.vehicles.append(v)
        scheduler.grid_visualizer.add_vehicle(v)
        scheduler.simulator.add_vehicle(v)

    scheduler.run()

if __name__ == "__main__":
    # 获取命令行参数，默认为 test_1
    test_name = sys.argv[1] if len(sys.argv) > 1 else "1"
    
    if test_name == "1":
        test_1()
    elif test_name == "2":
        test_2()
    else:
        print(f"未知的测试名称: {test_name}")
        sys.exit(1)