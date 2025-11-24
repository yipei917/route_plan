#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.scheduler import Scheduler
from src.models.grid import GRID_TYPE_MAIN_CHANNEL, GRID_TYPE_NORMAL_CHANNEL, MAIN_CHANNEL_STATUS_LEFT, MAIN_CHANNEL_STATUS_RIGHT, MAIN_CHANNEL_STATUS_NULL
from src.models.vehicle import VEHICLE_TYPE_LOADED

def test_direction_constraint(scheduler, test_path, path_name):
    """测试方向约束功能"""
    print(f"\n--- 测试路径 {path_name} 的方向约束 ---")
    print(f"路径: {test_path}")
    
    # 创建测试车辆
    vehicle = scheduler.vehicles[0]
    vehicle.vehicle_type = VEHICLE_TYPE_LOADED  # 设置为负载状态
    
    # 设置车辆的完整路径
    vehicle.set_full_planned_path(test_path)
    
    print("路径中的主通道位置分析:")
    main_channel_positions = []
    for i, position in enumerate(test_path):
        cell = scheduler.grid.get_cell(position[0], position[1])
        if cell and cell.grid_type == GRID_TYPE_MAIN_CHANNEL:
            main_channel_positions.append((i, position))
            print(f"  位置 {i}: {position} -> 主通道")
        else:
            print(f"  位置 {i}: {position} -> 一般道路")
    
    print(f"主通道位置: {[pos for _, pos in main_channel_positions]}")
    
    # 测试方向约束
    print(f"\n=== 测试方向约束 ===")
    
    # 添加方向约束
    try:
        scheduler.constraint_manager.add_direction_constraint(vehicle, scheduler.grid)
        
        # 检查方向锁定状态
        print(f"方向锁定表: {scheduler.constraint_manager.direction_locks}")
        
        # 检查主通道状态变化
        print("主通道状态变化:")
        for i, position in main_channel_positions:
            cell = scheduler.grid.get_cell(position[0], position[1])
            if cell:
                status_map = {
                    MAIN_CHANNEL_STATUS_NULL: "无限制",
                    MAIN_CHANNEL_STATUS_LEFT: "向左",
                    MAIN_CHANNEL_STATUS_RIGHT: "向右"
                }
                status = status_map.get(cell.main_channel_status, "未知")
                print(f"  位置 {position}: {status}")
        
        # 测试释放方向约束
        print(f"\n=== 测试释放方向约束 ===")
        scheduler.constraint_manager.remove_direction_constraint(vehicle, scheduler.grid)
        
        print("释放后的主通道状态:")
        for i, position in main_channel_positions:
            cell = scheduler.grid.get_cell(position[0], position[1])
            if cell:
                status_map = {
                    MAIN_CHANNEL_STATUS_NULL: "无限制",
                    MAIN_CHANNEL_STATUS_LEFT: "向左",
                    MAIN_CHANNEL_STATUS_RIGHT: "向右"
                }
                status = status_map.get(cell.main_channel_status, "未知")
                print(f"  位置 {position}: {status}")
        
    except Exception as e:
        print(f"方向约束测试出错: {e}")

def test_analyze_path_segments():
    """测试路径段分析功能"""
    print("=== 测试 analyze_path_segments 功能 ===")
    
    # 创建调度器
    scheduler = Scheduler(num_vehicles=1, step_size=3)
    scheduler.initialize()
    
    # 创建多个测试路径
    test_paths = {
        "路径1-向右": [(8, 7), (7, 7), (6, 7), (5, 7), (4, 7), (3, 7), (2, 7), (2, 6)],
        "路径2-向左": [(3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7)],
        "路径3-混合": [(8, 7), (9, 7), (10, 7), (10, 6), (10, 5), (10, 4), (10, 3)],
        "路径4-一般道路": [(10, 7), (10, 6), (10, 5), (10, 4), (10, 3)],
        "路径5-复杂": [(8, 7), (7, 7), (7, 8), (7, 9), (7, 10), (7, 11), (7, 12), (7, 13), (7, 14), (6, 14), (6, 15)]
    }
    
    # 对每个路径进行测试
    for path_name, test_path in test_paths.items():
        test_direction_constraint(scheduler, test_path, path_name)

if __name__ == "__main__":
    test_analyze_path_segments() 