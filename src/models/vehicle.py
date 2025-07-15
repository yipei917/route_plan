from typing import Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime
from .task import TASK_STATUS_ASSIGNED, TransportTask

# 使用字符串常量替代枚举
VEHICLE_TYPE_EMPTY = "empty"
VEHICLE_TYPE_LOADED = "loaded"

VEHICLE_STATUS_IDLE = "idle"
VEHICLE_STATUS_MOVING = "moving"
VEHICLE_STATUS_AVOIDING = "avoiding"
VEHICLE_STATUS_WAITING = "waiting"

@dataclass
class Vehicle:
    """Vehicle class"""
    id: str
    vehicle_type: str
    current_position: Tuple[int, int]
    status: str = VEHICLE_STATUS_IDLE
    path: List[Tuple[int, int]] = field(default_factory=list)
    current_task: Optional[TransportTask] = None
    task_history: List[TransportTask] = field(default_factory=list)
    last_update_time = datetime.now()
    current_path_index = 0

    def assign_task(self, task: TransportTask) -> bool:
        """Assign a task to the vehicle"""
        print(f"\n=== 分配任务 ===")
        print(f"车辆 {self.id} 当前状态: {self.status}")
        print(f"任务 {task.id} 当前状态: {task.status}")
        
        # 检查车辆状态
        if self.status != VEHICLE_STATUS_IDLE:
            print(f"错误：车辆状态不是空闲状态，当前状态: {self.status}")
            return False
        
        if self.current_task:
            print(f"错误：车辆已有任务 {self.current_task.id}")
            return False
        
        print(f"开始分配任务")
        try:
            # 更新任务状态
            task.assign_to_vehicle(self.id)
            # 更新车辆状态
            self.current_task = task
            print(f"任务分配完成")
            print(f"车辆状态: {self.status}")
            print(f"任务状态: {task.status}")
            return True
        except Exception as e:
            print(f"分配任务时发生错误: {str(e)}")
            # 发生错误时恢复状态
            self.current_task = None
            return False

    def start_task(self) -> None:
        """Start executing the current task"""
        print(f"\n=== 启动任务 ===")
        print(f"车辆 {self.id} 当前状态: {self.status}")
        print(f"任务 {self.current_task.id if self.current_task else 'None'} 当前状态: {self.current_task.status if self.current_task else 'None'}")
        
        # 检查车辆和任务状态
        if not self.current_task:
            print(f"错误：车辆没有当前任务")
            return
        
        if self.status != VEHICLE_STATUS_IDLE:
            print(f"错误：车辆状态不是空闲状态，当前状态: {self.status}")
            return
        
        if self.current_task.status != TASK_STATUS_ASSIGNED:
            print(f"错误：任务状态不是已分配状态，当前状态: {self.current_task.status}")
            return
        
        if not self.path:
            print(f"错误：没有设置路径")
            return
        
        print(f"开始执行任务")
        try:
            # 更新任务状态
            self.current_task.start_execution()
            # 更新车辆状态
            self.status = VEHICLE_STATUS_MOVING
            print(f"任务启动完成")
            print(f"车辆状态: {self.status}")
            print(f"任务状态: {self.current_task.status}")
        except Exception as e:
            print(f"启动任务时发生错误: {str(e)}")
            # 发生错误时恢复状态
            self.status = VEHICLE_STATUS_IDLE
            if self.current_task:
                self.current_task.status = TASK_STATUS_ASSIGNED

    def complete_task(self) -> None:
        """Complete the current task"""
        print(f"\n=== 完成任务 ===")
        print(f"车辆 {self.id} 当前状态: {self.status}")
        print(f"任务 {self.current_task.id if self.current_task else 'None'} 当前状态: {self.current_task.status if self.current_task else 'None'}")
        
        if self.current_task:
            print(f"开始完成任务")
            # 先完成当前任务
            self.current_task.complete()
            print(f"任务状态更新为: {self.current_task.status}")
            
            # 将任务添加到历史记录
            self.task_history.append(self.current_task)
            print(f"任务添加到历史记录")
            
            # 清除当前任务相关状态
            self.current_task = None
            self.status = VEHICLE_STATUS_IDLE
            self.path = []
            print(f"清除任务相关状态")
            
            # 更新最后更新时间
            self.last_update_time = datetime.now()
            print(f"任务完成处理完成")
            print(f"车辆状态: {self.status}")

    def update_position(self, new_position: Tuple[int, int]) -> None:
        """更新车辆位置 - 仅用于内部状态更新，不用于移动"""
        print(f"\n=== 更新位置 ===")
        print(f"车辆 {self.id} 当前位置: {self.current_position}")
        print(f"新位置: {new_position}")
        print(f"当前状态: {self.status}")
        
        # 直接更新位置
        self.current_position = new_position
        self.last_update_time = datetime.now()
        print(f"位置已更新")

    def set_path(self, path: List[Tuple[int, int]]) -> None:
        """设置路径"""
        print(f"\n=== 设置路径 ===")
        print(f"车辆 {self.id} 当前状态: {self.status}")
        print(f"当前路径长度: {len(self.path) if self.path else 0}")
        print(f"新路径长度: {len(path) if path else 0}")
        
        if not path:
            print(f"路径为空，清除路径")
            self.path = []
            self.current_path_index = 0
            return

        self.path = path
        self.current_path_index = 0
        print(f"路径已设置")
        print(f"目标位置: {path[-1]}")
        print(f"完整路径: {' -> '.join(str(p) for p in path)}")

    def set_waiting(self) -> None:
        """设置等待状态"""
        self.path = []
        self.current_path_index = 0
        self.status = VEHICLE_STATUS_WAITING

    def get_next_position(self) -> Optional[Tuple[int, int]]:
        """获取下一个位置"""
        if self.current_path_index + 1 >= len(self.path):
            return None
        else:
            return self.path[self.current_path_index + 1] if self.path else None

    def is_empty(self) -> bool:
        """检查车辆是否为空"""
        return self.vehicle_type == VEHICLE_TYPE_EMPTY

    def get_path_str(self) -> str:
        """返回当前路径的字符串表示"""
        if not self.path:
            return ""
        return " -> ".join(f"({x},{y})" for x, y in self.path)

    def get_remaining_path(self) -> List[Tuple[int, int]]:
        """获取车辆的剩余路径"""
        if not self.path or self.current_path_index >= len(self.path):
            return []
        return self.path[self.current_path_index:]