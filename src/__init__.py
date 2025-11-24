"""
四向穿梭车路径规划工具库

提供带方向约束的A*路径规划、路径冲突检测、方向锁定等功能。
适用于智能仓储系统中四向穿梭车的路径规划场景。
"""

__version__ = "1.0.0"
__author__ = "Route Planner Team"

# 核心类导出
from .algorithms.a_star import AStarPlanner
from .models.grid import Grid, GridCell
from .models.vehicle import Vehicle, VEHICLE_TYPE_EMPTY, VEHICLE_TYPE_LOADED
from .utils.constraints import ConstraintManager

# 常量导出
from .models.grid import (
    GRID_TYPE_NORMAL_CHANNEL,
    GRID_TYPE_MAIN_CHANNEL,
    GRID_TYPE_UP_DOWN_CHANNEL,
    GRID_TYPE_OBSTACLE,
    GRID_TYPE_INTERFACE,
    MAIN_CHANNEL_STATUS_NULL,
    MAIN_CHANNEL_STATUS_LEFT,
    MAIN_CHANNEL_STATUS_RIGHT,
)

__all__ = [
    # 核心类
    "AStarPlanner",
    "Grid",
    "GridCell",
    "Vehicle",
    "ConstraintManager",
    # 车辆类型常量
    "VEHICLE_TYPE_EMPTY",
    "VEHICLE_TYPE_LOADED",
    # 网格类型常量
    "GRID_TYPE_NORMAL_CHANNEL",
    "GRID_TYPE_MAIN_CHANNEL",
    "GRID_TYPE_UP_DOWN_CHANNEL",
    "GRID_TYPE_OBSTACLE",
    "GRID_TYPE_INTERFACE",
    # 主通道状态常量
    "MAIN_CHANNEL_STATUS_NULL",
    "MAIN_CHANNEL_STATUS_LEFT",
    "MAIN_CHANNEL_STATUS_RIGHT",
]

