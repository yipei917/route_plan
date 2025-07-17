from src.utils.scheduler import Scheduler

if __name__ == "__main__":
    scheduler = Scheduler(num_vehicles=1, step_size=3)
    scheduler.initialize()
    print("Scheduler 初始化完成")
    scheduler.run()