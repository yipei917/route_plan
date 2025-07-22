from src.utils.scheduler import Scheduler
from src.models.task import TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, Task
from src.models.vehicle import VEHICLE_TYPE_EMPTY, Vehicle

if __name__ == "__main__":
    scheduler = Scheduler(num_vehicles=2, step_size=3, output_path="output/test_1")
    scheduler.grid.load_map_from_xlsx("resource/test_map.xlsx")
    scheduler.task_manager.add_task(Task(
        id="T1",
        start_position=(8,7),
        end_position=(10,7),
        task_type=TASK_TYPE_OUTBOUND
    ))
    scheduler.task_manager.add_task(Task(
        id="T2",
        start_position=(10,7),
        end_position=(12,7),
        task_type=TASK_TYPE_INBOUND
    ))

    # 添加车辆
    vehicle_position = [(8,7), (10,7), (12,7), (14,7), (16,7), (18,7)]
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