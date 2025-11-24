#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.scheduler import Scheduler
from src.models.vehicle import VEHICLE_TYPE_LOADED, VEHICLE_TYPE_EMPTY
from src.models.grid import GRID_TYPE_MAIN_CHANNEL, MAIN_CHANNEL_STATUS_LEFT, MAIN_CHANNEL_STATUS_RIGHT, MAIN_CHANNEL_STATUS_NULL

def test_direction_lock():
    """测试方向锁定功能"""
    print("=== 测试方向锁定功能 ===")
    
    # 创建调度器
    scheduler = Scheduler(num_vehicles=2, step_size=3)
    scheduler.initialize()
    
    # 创建两个测试车辆
    vehicle1 = scheduler.vehicles[0]
    vehicle2 = scheduler.vehicles[1]
    
    # 设置车辆1为负载状态
    vehicle1.vehicle_type = VEHICLE_TYPE_LOADED
    vehicle2.vehicle_type = VEHICLE_TYPE_EMPTY
    
    print(f"车辆1状态: {'负载' if vehicle1.is_empty() == False else '空载'}")
    print(f"车辆2状态: {'负载' if vehicle2.is_empty() == False else '空载'}")
    
    # 测试路径 - 主通道路径
    test_path = [(8, 7), (9, 7), (10, 7), (11, 7), (12, 7)]
    
    print(f"\n测试路径: {test_path}")
    
    # 分析路径中的主通道位置
    main_channel_positions = []
    for position in test_path:
        cell = scheduler.grid.get_cell(position[0], position[1])
        if cell and cell.grid_type == GRID_TYPE_MAIN_CHANNEL:
            main_channel_positions.append(position)
            print(f"  位置 {position}: 主通道")
        else:
            print(f"  位置 {position}: 一般道路")
    
    print(f"主通道位置: {main_channel_positions}")
    
    # 设置车辆1的完整路径
    vehicle1.set_full_planned_path(test_path)
    
    # 测试方向锁定
    print(f"\n=== 测试方向锁定 ===")
    
    # 为负载车辆添加方向锁定
    scheduler.constraint_manager.add_direction_constraint(vehicle1, scheduler.grid)
    
    # 检查方向锁定状态
    print(f"方向锁定表: {scheduler.constraint_manager.direction_locks}")
    
    # 检查主通道状态变化
    print("主通道状态变化:")
    for position in main_channel_positions:
        cell = scheduler.grid.get_cell(position[0], position[1])
        if cell:
            status_map = {
                MAIN_CHANNEL_STATUS_NULL: "无限制",
                MAIN_CHANNEL_STATUS_LEFT: "向左",
                MAIN_CHANNEL_STATUS_RIGHT: "向右"
            }
            status = status_map.get(cell.main_channel_status, "未知")
            print(f"  位置 {position}: {status}")
    
    # 测试释放方向锁定
    print(f"\n=== 测试释放方向锁定 ===")
    scheduler.constraint_manager.remove_direction_constraint(vehicle1, scheduler.grid)
    print(f"释放后方向锁定表: {scheduler.constraint_manager.direction_locks}")
    
    # 检查释放后的主通道状态
    print("释放后的主通道状态:")
    for position in main_channel_positions:
        cell = scheduler.grid.get_cell(position[0], position[1])
        if cell:
            status_map = {
                MAIN_CHANNEL_STATUS_NULL: "无限制",
                MAIN_CHANNEL_STATUS_LEFT: "向左",
                MAIN_CHANNEL_STATUS_RIGHT: "向右"
            }
            status = status_map.get(cell.main_channel_status, "未知")
            print(f"  位置 {position}: {status}")

if __name__ == "__main__":
    test_direction_lock() 