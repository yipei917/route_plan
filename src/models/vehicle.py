from typing import Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime
from .task import TASK_STATUS_ASSIGNED, TransportTask

# 使用字符串常量替代枚举
VEHICLE_TYPE_EMPTY = "empty"
VEHICLE_TYPE_LOADED = "loaded"

VEHICLE_STATUS_IDLE = "idle"
VEHICLE_STATUS_PICKUP = "pickup"
VEHICLE_STATUS_AVOIDING = "avoiding"
VEHICLE_STATUS_WAITING = "waiting"
VEHICLE_STATUS_DELIVER = "deliver"

@dataclass
class Vehicle:
    """Vehicle class"""
    id: str
    vehicle_type: str
    current_position: Tuple[int, int]
    status: str = VEHICLE_STATUS_IDLE
    full_planned_path: List[Tuple[int, int]] = field(default_factory=list)  # 完整规划路径
    current_execution_path: List[Tuple[int, int]] = field(default_factory=list)  # 当前执行路径
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
        
        if not self.full_planned_path:
            print(f"错误：没有设置完整规划路径")
            return
        
        print(f"开始执行任务")
        try:
            # 更新任务状态
            self.current_task.start_execution()
            # 更新车辆状态
            self.status = VEHICLE_STATUS_PICKUP
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

    def set_full_planned_path(self, path: List[Tuple[int, int]]) -> None:
        """设置完整规划路径"""
        print(f"\n=== 设置完整规划路径 ===")
        print(f"车辆 {self.id} 当前状态: {self.status}")
        print(f"当前完整路径长度: {len(self.full_planned_path)}")
        print(f"新完整路径长度: {len(path) if path else 0}")
        
        if not path:
            print(f"路径为空，清除完整规划路径")
            self.full_planned_path = []
            return

        self.full_planned_path = path
        print(f"完整规划路径已设置")
        print(f"完整路径: {' -> '.join(str(p) for p in path)}")

    def set_current_execution_path(self, path: List[Tuple[int, int]]) -> None:
        """设置当前执行路径"""
        print(f"\n=== 设置当前执行路径 ===")
        print(f"车辆 {self.id} 当前状态: {self.status}")
        print(f"当前执行路径长度: {len(self.current_execution_path)}")
        print(f"新执行路径长度: {len(path) if path else 0}")
        
        if not path:
            print(f"路径为空，清除当前执行路径")
            self.current_execution_path = []
            self.current_path_index = 0
            return

        self.current_execution_path = path
        self.current_path_index = 0
        print(f"当前执行路径已设置")
        print(f"目标位置: {path[-1]}")
        print(f"执行路径: {' -> '.join(str(p) for p in path)}")

    def get_next_position(self) -> Optional[Tuple[int, int]]:
        """获取下一个位置"""
        if self.current_path_index + 1 >= len(self.current_execution_path):
            return None
        else:
            return self.current_execution_path[self.current_path_index + 1] if self.current_execution_path else None

    def is_empty(self) -> bool:
        """检查车辆是否为空"""
        return self.vehicle_type == VEHICLE_TYPE_EMPTY

    def get_full_planned_path(self) -> List[Tuple[int, int]]:
        return self.full_planned_path