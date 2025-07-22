from src.utils.scheduler import Scheduler
from src.models.task import TASK_TYPE_INBOUND, TASK_TYPE_OUTBOUND, TransportTask
from src.models.vehicle import VEHICLE_TYPE_EMPTY, Vehicle

if __name__ == "__main__":
    scheduler = Scheduler(num_vehicles=2, step_size=3, output_path="output/test_1")
    scheduler.grid.load_map_from_xlsx("resource/test_map.xlsx")
    scheduler.task_manager.add_task(task_type=TASK_TYPE_OUTBOUND,start_pos=(10,6),end_pos=(18,15))
    scheduler.task_manager.add_task(task_type=TASK_TYPE_INBOUND,start_pos=(2,8),end_pos=(3,6))
    # 添加车辆
    vehicle_position = [(6,7), (8,7)]
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