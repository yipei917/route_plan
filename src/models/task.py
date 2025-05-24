from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime

# 使用字符串常量替代枚举
TASK_TYPE_INBOUND = "inbound"
TASK_TYPE_OUTBOUND = "outbound"

TASK_STATUS_PENDING = "pending"
TASK_STATUS_ASSIGNED = "assigned"
TASK_STATUS_IN_PROGRESS = "in_progress"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"


@dataclass
class TransportTask:
    """Transport task class"""
    id: str  # Task ID
    task_type: str  # "inbound" or "outbound"
    start_position: Tuple[int, int]  # Start position (x, y)
    end_position: Tuple[int, int]  # End position (x, y)
    priority: int = 0  # Task priority (higher number = higher priority)
    created_at: datetime = None  # Task creation time
    assigned_vehicle: Optional[str] = None  # ID of the vehicle assigned to this task
    status: str = TASK_STATUS_PENDING  # Current task status
    error_message: Optional[str] = None  # 添加错误信息字段

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def assign_to_vehicle(self, vehicle_id: str) -> None:
        """Assign task to a vehicle"""
        self.assigned_vehicle = vehicle_id
        self.status = TASK_STATUS_ASSIGNED

    def start_execution(self) -> None:
        """Mark task as in progress"""
        self.status = TASK_STATUS_IN_PROGRESS

    def complete(self) -> None:
        """Mark task as completed"""
        self.status = TASK_STATUS_COMPLETED

    def fail(self, error_message: str = None) -> None:
        """任务失败"""
        self.status = TASK_STATUS_FAILED
        self.error_message = error_message
        if self.assigned_vehicle:
            self.assigned_vehicle = None

    def reset_error(self) -> None:
        """重置错误状态"""
        self.error_message = None


class TaskManager:
    """Task queue manager"""

    def __init__(self):
        self.tasks: List[TransportTask] = []
        self._next_task_id = 1

    def add_task(self, task_type: str, start_pos: Tuple[int, int],
                 end_pos: Tuple[int, int], priority: int = 0) -> TransportTask:
        """Add a new task to the queue"""
        task_id = f"T{self._next_task_id:03d}"
        self._next_task_id += 1

        task = TransportTask(
            id=task_id,
            task_type=task_type,
            start_position=start_pos,
            end_position=end_pos,
            priority=priority
        )
        self.tasks.append(task)
        return task

    def get_next_task(self) -> Optional[TransportTask]:
        """Get the next available task based on priority and creation time"""
        available_tasks = [t for t in self.tasks
                           if t.status == TASK_STATUS_PENDING]
        if not available_tasks:
            return None

        # Sort by priority (descending) and creation time (ascending)
        return sorted(available_tasks,
                      key=lambda t: (-t.priority, t.created_at))[0]

    def get_tasks_by_status(self, status: str) -> List[TransportTask]:
        """Get all tasks with specified status"""
        print(f"\n=== 获取状态为 {status} 的任务 ===")
        print(f"当前所有任务:")
        for task in self.tasks:
            print(f"任务 {task.id}: 类型={task.task_type}, 状态={task.status}")

        matching_tasks = [t for t in self.tasks if t.status == status]
        print(f"找到 {len(matching_tasks)} 个匹配的任务")
        for task in matching_tasks:
            print(f"匹配任务 {task.id}: 类型={task.task_type}, 状态={task.status}")

        return matching_tasks

    def get_tasks_by_vehicle(self, vehicle_id: str) -> List[TransportTask]:
        """Get all tasks assigned to a specific vehicle"""
        return [t for t in self.tasks if t.assigned_vehicle == vehicle_id]

    def get_task_by_id(self, task_id: str) -> Optional[TransportTask]:
        """Get task by ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the queue"""
        task = self.get_task_by_id(task_id)
        if task:
            self.tasks.remove(task)
            return True
        return False

    def clear_completed_tasks(self) -> None:
        """Remove all completed tasks from the queue"""
        self.tasks = [t for t in self.tasks if t.status != TASK_STATUS_COMPLETED]

    def get_queue_status(self) -> dict:
        """Get current queue status"""
        return {
            "total_tasks": len(self.tasks),
            "pending": len(self.get_tasks_by_status(TASK_STATUS_PENDING)),
            "assigned": len(self.get_tasks_by_status(TASK_STATUS_ASSIGNED)),
            "in_progress": len(self.get_tasks_by_status(TASK_STATUS_IN_PROGRESS)),
            "completed": len(self.get_tasks_by_status(TASK_STATUS_COMPLETED)),
            "failed": len(self.get_tasks_by_status(TASK_STATUS_FAILED))
        }
