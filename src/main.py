from src.utils.scheduler import Scheduler

if __name__ == "__main__":
    scheduler = Scheduler(num_vehicles=2)
    scheduler.initialize()
    print("Scheduler 初始化完成")
    scheduler.assign_task()
    scheduler.visualize("test.png")